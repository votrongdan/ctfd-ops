import warnings

from flask import current_app
from requests import session, RequestException

from CTFd.models import db
from CTFd.utils import get_config, set_config, logging

from .base import BaseRouter
from ..redirects import rules_for, http_subdomain
from CTFd.plugins._lifecycle import lifecycle_lock
from ..cache import CacheProvider
from ..db import DBContainer
from ..exceptions import WhaleError, WhaleWarning
from ...models import WhaleContainer


class FrpRouter(BaseRouter):
    name = "frp"
    types = {
        'direct': 'tcp',
        'http': 'http',
    }

    class FrpRule:
        def __init__(self, name, config):
            self.name = name
            self.config = config

        def __str__(self) -> str:
            return f'[{self.name}]\n' + '\n'.join(f'{k} = {v}' for k, v in self.config.items())

    def __init__(self):
        super().__init__()
        self.ses = session()
        self.url = get_config("whale:frp_api_url").rstrip("/")
        self.common = ''
        try:
            CacheProvider(app=current_app).init_port_sets()
        except Exception:
            warnings.warn(
                "cache initialization failed",
                WhaleWarning
            )

    def reload(self, exclude=None, include=None):
        with lifecycle_lock("whale-routing"):
            return self._reload(exclude, include)

    def _reload(self, exclude=None, include=None):
        rules = []
        containers = list(DBContainer.get_all_alive_container())
        if include is not None and all(c.id != include.id for c in containers):
            containers.append(include)
        for container in containers:
            if container.uuid == exclude:
                continue
            for port, kind in rules_for(container.challenge):
                suffix = "_" + port if container.challenge.redirect_rules else ""
                name = f'{kind}_{container.user_id}_{container.uuid}{suffix}'
                config = {
                    'type': self.types[kind],
                    'local_ip': f'{container.user_id}-{container.uuid}',
                    'local_port': port,
                    'use_compression': 'true',
                }
                if kind == 'http':
                    config['subdomain'] = http_subdomain(container, port)
                else:
                    remote = (container.ports or {}).get(port) if container.challenge.redirect_rules else container.port
                    if not remote:
                        raise WhaleError("Missing reserved port for container " + str(container.id))
                    config['remote_port'] = remote
                rules.append(self.FrpRule(name, config))

        try:
            if not self.common:
                common = get_config("whale:frp_config_template", '')
                if '[common]' in common:
                    self.common = common
                else:
                    remote = self.ses.get(f'{self.url}/api/config', timeout=5)
                    assert remote.status_code == 200
                    set_config("whale:frp_config_template", remote.text)
                    self.common = remote.text
            config = self.common + '\n' + '\n'.join(str(r) for r in rules)
            assert self.ses.put(
                f'{self.url}/api/config', config, timeout=5
            ).status_code == 200
            assert self.ses.get(
                f'{self.url}/api/reload', timeout=5
            ).status_code == 200
        except (RequestException, AssertionError) as e:
            raise WhaleError(
                '\nfrpc request failed\n' +
                (f'{e}\n' if str(e) else '') +
                'please check the frp related configs'
            ) from None

    def access(self, container: WhaleContainer):
        result = []
        for port, kind in rules_for(container.challenge):
            if kind == 'direct':
                remote = (container.ports or {}).get(port, 'Unknown') if container.challenge.redirect_rules else container.port
                result.append(f'nc {get_config("whale:frp_direct_ip_address", "127.0.0.1")} {remote}')
            else:
                host = get_config("whale:frp_http_domain_suffix", "")
                hport = str(get_config("whale:frp_http_port", "80"))
                host += f':{hport}' if hport != '80' else ''
                label = f' ({port})' if container.challenge.redirect_rules else ''
                result.append(f'<a target="_blank" href="http://{http_subdomain(container, port)}.{host}/">Link to the Challenge{label}</a>')
        return '<br>'.join(result)

    def register(self, container: WhaleContainer):
        with lifecycle_lock("whale-routing"):
            pool = CacheProvider(app=current_app)
            for port, kind in rules_for(container.challenge):
                if kind != 'direct':
                    continue
                existing = (container.ports or {}).get(port) if container.challenge.redirect_rules else container.port
                if existing:
                    continue
                reserved = pool.get_available_port()
                if reserved is None:
                    raise WhaleError('No available ports. Please wait for a few minutes.')
                try:
                    if container.challenge.redirect_rules:
                        container.ports = dict(container.ports or {}, **{port: reserved})
                    else:
                        container.port = reserved
                    # Persist each reservation so crash recovery can find it.
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    pool.add_available_port(reserved)
                    raise
            self.reload(include=container)
            return True, 'success'

    def unregister(self, container: WhaleContainer):
        with lifecycle_lock("whale-routing"):
            # Never free a port while FRP may still be serving its old route.
            self.reload(exclude=container.uuid)
            ports = set((container.ports or {}).values())
            if container.port:
                ports.add(container.port)
            container.ports = {}
            container.port = 0
            db.session.commit()
            pool = CacheProvider(app=current_app)
            for port in ports:
                pool.add_available_port(port)
            return True, 'success'

    def check_availability(self):
        try:
            resp = self.ses.get(f'{self.url}/api/status', timeout=2.0)
        except RequestException as e:
            return False, 'Unable to access frpc admin api'
        if resp.status_code == 401:
            return False, 'frpc admin api unauthorized'
        return True, 'Available'
