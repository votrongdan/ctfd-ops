import warnings

from flask import current_app
from requests import session, RequestException

from CTFd.models import db
from CTFd.utils import get_config, set_config, logging

from .base import BaseRouter
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

    def reload(self, exclude=None):
        rules = []
        for container in DBContainer.get_all_alive_container():
            if container.uuid == exclude:
                continue
                
            if container.challenge.redirect_rules:
                for rule in [r.strip() for r in container.challenge.redirect_rules.split(",") if r.strip()]:
                    if "/" in rule:
                        port, rtype = rule.split("/", 1)
                        name = f'{rtype}_{container.user_id}_{container.uuid}_{port}'
                        config = {
                            'type': self.types.get(rtype, rtype),
                            'local_ip': f'{container.user_id}-{container.uuid}',
                            'local_port': port,
                            'use_compression': 'true',
                        }
                        if config['type'] == 'http':
                            config['subdomain'] = container.http_subdomain
                        elif config['type'] == 'tcp':
                            # Get the allocated port. Since container.ports is a JSON dict (or string keys), map using str(port)
                            config['remote_port'] = container.ports.get(str(port), container.ports.get(port))
                        rules.append(self.FrpRule(name, config))
            else:
                name = f'{container.challenge.redirect_type}_{container.user_id}_{container.uuid}'
                config = {
                    'type': self.types[container.challenge.redirect_type],
                    'local_ip': f'{container.user_id}-{container.uuid}',
                    'local_port': container.challenge.redirect_port,
                    'use_compression': 'true',
                }
                if config['type'] == 'http':
                    config['subdomain'] = container.http_subdomain
                elif config['type'] == 'tcp':
                    config['remote_port'] = container.port
                rules.append(self.FrpRule(name, config))

        try:
            if not self.common:
                common = get_config("whale:frp_config_template", '')
                if '[common]' in common:
                    self.common = common
                else:
                    remote = self.ses.get(f'{self.url}/api/config')
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
        if container.challenge.redirect_rules:
            access_strs = []
            for rule in [r.strip() for r in container.challenge.redirect_rules.split(",") if r.strip()]:
                if "/" in rule:
                    port, rtype = rule.split("/", 1)
                    if rtype == 'direct':
                        alloc_port = container.ports.get(str(port), container.ports.get(port, 'Unknown'))
                        access_strs.append(f'nc {get_config("whale:frp_direct_ip_address", "127.0.0.1")} {alloc_port}')
                    elif rtype == 'http':
                        host = get_config("whale:frp_http_domain_suffix", "")
                        hport = get_config("whale:frp_http_port", "80")
                        host += f':{hport}' if hport != '80' else ''
                        access_strs.append(f'<a target="_blank" href="http://{container.http_subdomain}.{host}/">Link to the Challenge ({port})</a>')
            return '<br>'.join(access_strs)

        if container.challenge.redirect_type == 'direct':
            return f'nc {get_config("whale:frp_direct_ip_address", "127.0.0.1")} {container.port}'
        elif container.challenge.redirect_type == 'http':
            host = get_config("whale:frp_http_domain_suffix", "")
            port = get_config("whale:frp_http_port", "80")
            host += f':{port}' if port != '80' else ''
            return f'<a target="_blank" href="http://{container.http_subdomain}.{host}/">Link to the Challenge</a>'
        return ''

    def register(self, container: WhaleContainer):
        if container.challenge.redirect_rules:
            if not container.ports:
                container.ports = {}
            # SQLAlchemy JSON mutation tracking requires setting the dict again or using flag_modified
            new_ports = dict(container.ports)
            
            for rule in [r.strip() for r in container.challenge.redirect_rules.split(",") if r.strip()]:
                if "/" in rule:
                    port, rtype = rule.split("/", 1)
                    if rtype == 'direct':
                        if str(port) not in new_ports and port not in new_ports:
                            avail_port = CacheProvider(app=current_app).get_available_port()
                            if not avail_port:
                                return False, 'No available ports. Please wait for a few minutes.'
                            new_ports[str(port)] = avail_port
            container.ports = new_ports
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(container, "ports")
            db.session.commit()
        else:
            if container.challenge.redirect_type == 'direct':
                if not container.port:
                    port = CacheProvider(app=current_app).get_available_port()
                    if not port:
                        return False, 'No available ports. Please wait for a few minutes.'
                    container.port = port
                    db.session.commit()
            elif container.challenge.redirect_type == 'http':
                pass
        self.reload()
        return True, 'success'

    def unregister(self, container: WhaleContainer):
        redis_util = CacheProvider(app=current_app)
        
        if container.challenge.redirect_rules:
            if container.ports:
                for port_val in container.ports.values():
                    try:
                        redis_util.add_available_port(port_val)
                    except Exception as e:
                        logging.log(
                            'whale', 'Error deleting port from cache',
                            name=container.user.name,
                            challenge_id=container.challenge_id,
                        )
        else:
            if container.challenge.redirect_type == 'direct':
                try:
                    redis_util.add_available_port(container.port)
                except Exception as e:
                    logging.log(
                        'whale', 'Error deleting port from cache',
                        name=container.user.name,
                        challenge_id=container.challenge_id,
                    )
                    return False, 'Error deleting port from cache'
        self.reload(exclude=container.uuid)
        return True, 'success'

    def check_availability(self):
        try:
            resp = self.ses.get(f'{self.url}/api/status', timeout=2.0)
        except RequestException as e:
            return False, 'Unable to access frpc admin api'
        if resp.status_code == 401:
            return False, 'frpc admin api unauthorized'
        return True, 'Available'
