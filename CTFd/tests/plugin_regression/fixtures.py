"""Run only against a disposable DB; never use the live competition DB."""
import importlib
import os
import sys
import uuid
from types import SimpleNamespace
from unittest.mock import patch
import pytest

# Legacy tests used Python identifier spellings for on-disk hyphenated plugins.
# Keep aliases confined to the test harness, pointing to the exact same modules.
for plugin, children in {
    'ctfd-single-session': ['models', 'session_tracker', 'routes'],
    'ctfd-account-provisioning': ['services.ctfd_import_adapter'],
}.items():
    for child in [''] + children:
        name = 'CTFd.plugins.' + plugin + ('.' + child if child else '')
        sys.modules[name.replace(plugin, plugin.replace('-', '_'))] = importlib.import_module(name)


@pytest.fixture(scope='session')
def app():
    from CTFd import create_app
    from CTFd.models import db
    from CTFd.utils import set_config
    url = os.environ.get('DATABASE_URL', '')
    assert 'ctfd_regression' in url or url.startswith('sqlite:'), 'Disposable DB required'
    application = getattr(sys, '_ctfd_regression_app', None)
    if application is None:
        with patch('flask_apscheduler.APScheduler.start'), patch('flask_apscheduler.APScheduler.add_job'):
            application = create_app()
    application.config.update(TESTING=True, SERVER_NAME='localhost', UPDATE_CHECK=False)
    with application.app_context():
        for key, value in {'setup': True, 'ctf_name': 'Regression', 'user_mode': 'users',
                           'challenge_visibility': 'public', 'account_visibility': 'public',
                           'ssm:mode': 'monitoring', 'whale:docker_auto_connect_network': 'ctfd_fix_regression_challenges',
                           'whale:frp_http_port': '19081', 'whale:frp_direct_port_minimum': '19100',
                           'whale:frp_direct_port_maximum': '19120'}.items():
            set_config(key, value)
    yield application


@pytest.fixture
def user(app):
    return make_user(app)


@pytest.fixture
def admin_user(app):
    return make_user(app, 'admin')


def make_user(app, kind='user'):
    from CTFd.models import Users, db
    with app.app_context():
        name = kind + '_' + uuid.uuid4().hex[:12]
        user = Users(name=name, email=name + '@example.com', password='password', type=kind, verified=True)
        db.session.add(user); db.session.commit()
        return SimpleNamespace(id=user.id, name=user.name, email=user.email)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(app, admin_user):
    c = app.test_client()
    login(c, admin_user.name)
    return c


def login(client, name, password='password'):
    if not hasattr(client, '_regression_ip'):
        client._regression_ip = '10.231.' + str(uuid.uuid4().int % 250) + '.' + str(uuid.uuid4().int % 250 + 1)
        client.environ_base['REMOTE_ADDR'] = client._regression_ip
    client.get('/login')
    with client.session_transaction() as s:
        nonce = s['nonce']
    return client.post('/login', data={'name': name, 'password': password, 'nonce': nonce})


def csrf(client):
    with client.session_transaction() as s:
        return {'CSRF-Token': s['nonce']}


@pytest.fixture(autouse=True)
def restore_mode(request):
    yield
    if 'app' in request.fixturenames:
        from CTFd.utils import set_config
        with request.getfixturevalue('app').app_context():
            set_config('ssm:mode', 'monitoring')
