import datetime
import importlib
import io
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from flask import session
from sqlalchemy import create_engine, inspect, text
from alembic.migration import MigrationContext
from alembic.operations import Operations
from CTFd.models import db, Users
from CTFd.cache import cache
from CTFd.utils import set_config
from .fixtures import csrf, login

ssm = importlib.import_module('CTFd.plugins.ctfd-single-session.session_tracker')
prov = importlib.import_module('CTFd.plugins.ctfd-account-provisioning.services.provisioning_service')
storage = importlib.import_module('CTFd.plugins.ctfd-account-provisioning.services.storage')
parser = importlib.import_module('CTFd.plugins.ctfd-account-provisioning.services.csv_parser')
wm = importlib.import_module('CTFd.plugins.ctfd-whale.models')
frp = importlib.import_module('CTFd.plugins.ctfd-whale.utils.routers.frp')
wc = importlib.import_module('CTFd.plugins.ctfd-whale.utils.cache')
control = importlib.import_module('CTFd.plugins.ctfd-whale.utils.control')


def test_additive_migration_old_sqlite(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path/'old.db'))
    migration = importlib.import_module('CTFd.plugins.ctfd-whale.migrations.0001_multi_port')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE dynamic_docker_challenge (id INTEGER PRIMARY KEY, redirect_port INTEGER)'))
        conn.execute(text('CREATE TABLE whale_container (id INTEGER PRIMARY KEY, port INTEGER, flag TEXT)'))
        conn.execute(text("INSERT INTO whale_container VALUES (1, 19100, 'old-flag')"))
        op = Operations(MigrationContext.configure(conn))
        migration.upgrade(op); migration.upgrade(op)
        assert 'ports' in {c['name'] for c in inspect(conn).get_columns('whale_container')}
        assert conn.execute(text('SELECT port, flag, ports FROM whale_container')).fetchone() == (19100, 'old-flag', None)


def test_additive_migration_partial_sqlite(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path/'partial.db'))
    migration = importlib.import_module('CTFd.plugins.ctfd-whale.migrations.0001_multi_port')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE dynamic_docker_challenge (id INTEGER PRIMARY KEY, redirect_rules TEXT)'))
        conn.execute(text('CREATE TABLE whale_container (id INTEGER PRIMARY KEY, ports JSON)'))
        conn.execute(text('INSERT INTO whale_container VALUES (1, :ports)'), ports='{"22":19100}')
        migration.upgrade(Operations(MigrationContext.configure(conn)))
        assert conn.execute(text('SELECT ports FROM whale_container')).scalar() == '{"22":19100}'


def test_csv_required_and_duplicates():
    r = parser.parse_csv(io.BytesIO(b'Player ID,Name\nP1,Alice\np1,Bob\nP2,\n,Charlie\n,\n'))
    assert [p.name for p in r.players] == ['Alice']
    assert len(r.errors) == 3


def test_pending_blocks_other_request(app, user):
    with app.test_request_context():
        record, blocked = ssm.SessionTracker.register_session_atomic(user.id, 'pending-'+uuid.uuid4().hex)
        assert not blocked
        other, blocked = ssm.SessionTracker.register_session_atomic(user.id, 'other-'+uuid.uuid4().hex)
        assert other is None and blocked
        record = ssm.SSMSession.query.get(record.id)
        record.pending_until = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        db.session.commit()
        assert not ssm.SessionTracker.has_active_session(user.id)


def test_parallel_registration_real_database(app, user):
    def register(i):
        with app.test_request_context():
            return ssm.SessionTracker.register_session_atomic(user.id, uuid.uuid4().hex)[1]
    with ThreadPoolExecutor(max_workers=4) as pool:
        blocked = list(pool.map(register, range(4)))
    assert blocked.count(False) == 1


def test_login_logout_block_monitoring(app, user):
    a, b = app.test_client(), app.test_client()
    assert login(a, user.name).status_code == 302
    with app.app_context():
        assert len(ssm.SessionTracker.get_active_sessions(user.id)) == 1
        set_config('ssm:mode', 'block')
    assert b'already logged in' in login(b, user.name).data
    assert a.get('/logout').status_code == 302
    assert login(b, user.name).status_code == 302
    assert b.get('/settings').status_code == 200
    with app.app_context():
        set_config('ssm:mode', 'monitoring')
    assert login(a, user.name).status_code == 302
    with app.app_context():
        assert len(ssm.SessionTracker.get_active_sessions(user.id)) == 2
    a.get('/logout'); b.get('/logout')


def test_old_login_age_does_not_override_cache(app, user):
    c = app.test_client(); login(c, user.name)
    with app.app_context():
        r = ssm.SSMSession.query.filter_by(user_id=user.id, is_active=True).one()
        r.created_at = datetime.datetime.utcnow() - datetime.timedelta(days=100)
        db.session.commit()
        assert ssm.SessionTracker.is_session_valid(r)
        assert not r.is_expired
        assert ssm.SessionTracker.cleanup_expired() >= 0
        assert ssm.SessionTracker.has_active_session(user.id)
        cache.delete(r.cache_key)
        assert not ssm.SessionTracker.has_active_session(user.id)


def test_real_session_save_refresh_and_force_logout(app, user):
    c = app.test_client(); login(c, user.name)
    with app.app_context():
        r = ssm.SSMSession.query.filter_by(user_id=user.id, is_active=True).one()
        assert r.pending_until is None
        assert r.lifecycle == ssm.get_app_lifecycle_id()
        rid = r.id
    with c.session_transaction() as s:
        s['modified-test'] = True
    with app.app_context():
        assert ssm.SessionTracker.has_active_session(user.id)
        assert ssm.SessionTracker.force_logout_session(rid)
    assert c.get('/settings').status_code == 302


def test_late_pending_save_cannot_login(app, user):
    from flask import Response
    from CTFd.utils.sessions import CachedSession
    with app.test_request_context():
        sid = uuid.uuid4().hex
        r = ssm.SessionTracker.register_session(user.id, sid)
        r.pending_until = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        db.session.commit()
        s = CachedSession({'id': user.id}, sid=sid, permanent=True)
        s.modified = True
        app.session_interface.save_session(app, s, Response())
        assert not s
        assert not ssm.SessionTracker.has_active_session(user.id)


def test_session_save_failure_clears_pending(app, user):
    from flask import Response
    from CTFd.utils.sessions import CachedSession
    with app.test_request_context():
        sid = uuid.uuid4().hex
        r = ssm.SessionTracker.register_session(user.id, sid)
        s = CachedSession({'id': user.id}, sid=sid, permanent=True)
        s.modified = True
        with patch.object(app.session_interface.delegate, 'save_session', side_effect=RuntimeError('cache unavailable')):
            with pytest.raises(RuntimeError):
                app.session_interface.save_session(app, s, Response())
        record = ssm.SSMSession.query.filter_by(
            session_hash=ssm.hash_session_id(sid)
        ).one()
        assert not record.is_active
        assert record.pending_until is None


def upload(c, rows):
    return c.post('/plugins/ctfd-account-provisioning/admin/upload', data={
        'file': (io.BytesIO(('Player ID,Name\n'+rows).encode()), 'players.csv'),
        'email_domain': 'ctf.local', 'nonce': csrf(c)['CSRF-Token']}, headers=csrf(c))


def test_provision_preview_confirm_retry_download(app, admin_client):
    name = 'Test'+uuid.uuid4().hex[:8]
    response = upload(admin_client, 'P001,'+name+'\n')
    assert response.status_code == 200, response.data
    preview = response.json
    assert preview['valid_count'] == 1
    p = preview['participants'][0]
    with app.app_context():
        assert Users.query.filter_by(name=p['username']).first() is None
    args = {'json': {'token':preview['token']}, 'headers':csrf(admin_client)}
    response = admin_client.post('/plugins/ctfd-account-provisioning/admin/provision', **args)
    assert response.status_code == 200, response.data
    assert response.json['total_success'] == 1
    retry = admin_client.post('/plugins/ctfd-account-provisioning/admin/provision', **args)
    assert retry.json['successful'] == response.json['successful']
    url = '/plugins/ctfd-account-provisioning/admin/download/'+response.json['doc_token']
    first, second = admin_client.get(url), admin_client.get(url)
    assert first.status_code == second.status_code == 200
    assert first.data == second.data and first.data.startswith(b'PK')
    player = app.test_client()
    assert login(player, p['username'], p['password']).status_code == 302
    assert player.get('/settings').status_code == 200
    with app.app_context():
        job = storage.ProvisioningJob.query.filter_by(token_hash=storage.digest(preview['token'])).one()
        assert p['password'].encode() not in job.payload
        assert Users.query.filter_by(name=p['username']).count() == 1


def test_provision_constraints_and_owner(app, admin_client, admin_user):
    preview = upload(admin_client, 'P1,'+'x'*130+'\nP2,Valid\nP2,Duplicate\nP3,\n').json
    assert preview['valid_count'] == 1
    assert preview['invalid_count'] == 3
    other = app.test_client(); login(other, admin_user.name)
    # This fixture admin differs from admin_client's owner only if explicitly created.
    from .fixtures import make_user
    other_admin = make_user(app, 'admin'); other = app.test_client(); login(other, other_admin.name)
    result = other.post('/plugins/ctfd-account-provisioning/admin/provision', json={'token':preview['token']}, headers=csrf(other))
    assert result.status_code == 400


def test_provision_document_failure_retry_and_expiry(app, admin_client):
    token = upload(admin_client, 'P1,Recovery'+uuid.uuid4().hex[:8]+'\n').json['token']
    result = admin_client.post('/plugins/ctfd-account-provisioning/admin/provision', json={'token':token}, headers=csrf(admin_client))
    url = '/plugins/ctfd-account-provisioning/admin/download/'+result.json['doc_token']
    with patch.object(prov, 'generate_credential_document', side_effect=RuntimeError('render unavailable')):
        with pytest.raises(RuntimeError):
            admin_client.get(url)
    assert admin_client.get(url).status_code == 200
    with app.app_context():
        job = storage.ProvisioningJob.query.filter_by(token_hash=storage.digest(token)).one()
        job.expires_at = datetime.datetime.utcnow()-datetime.timedelta(seconds=1)
        db.session.commit()
    assert admin_client.get(url).status_code == 404


def test_pool_rebuild_respects_legacy_and_multi(app, user):
    with app.app_context():
        ch = wm.DynamicDockerChallenge(name='PoolTest', value=500, category='Test', docker_image='unused', redirect_type='direct', redirect_port=80)
        db.session.add(ch); db.session.commit()
        c = wm.WhaleContainer(user.id, ch.id); c.port=19100; c.ports={'22':19101}
        db.session.add(c); db.session.commit()
        pool=wc.CacheProvider(app)
        pool.init_port_sets()
        free = {int(p) for p in pool.provider.smembers(pool.global_port_key)}
        assert 19100 not in free and 19101 not in free and 19102 in free
        db.session.delete(c); db.session.delete(ch); db.session.commit()
        pool.init_port_sets()


def test_http_routes_and_legacy_access(app, user):
    with app.app_context():
        ch=wm.DynamicDockerChallenge(name='HTTP', value=500, category='Test', redirect_type='http', redirect_port=80)
        c=wm.WhaleContainer(user.id, 0); c.challenge=ch
        router=object.__new__(frp.FrpRouter)
        ch.redirect_rules='80/http,8080/http,22/direct'; c.ports={'22':19100}
        access=router.access(c)
        assert c.http_subdomain+'.' in access
        assert c.http_subdomain+'-p8080.' in access
        assert '19100' in access
        assert c.http_subdomain+'-p8080.' in c.user_access
        assert 'local_port = 8080' in c.frp_config
        ch.redirect_rules='80/http,22/direct'
        assert '-p80.' not in router.access(c)
        ch.redirect_rules=''; assert 'Link to the Challenge</a>' in router.access(c)
        db.session.rollback()


def test_provision_result_failure_rolls_back_accounts(app, admin_client):
    preview=upload(admin_client,'P1,Rollback'+uuid.uuid4().hex[:8]+'\n').json
    username=preview['participants'][0]['username']
    with patch.object(storage,'encode',side_effect=RuntimeError('encryption unavailable')):
        with pytest.raises(RuntimeError):
            admin_client.post('/plugins/ctfd-account-provisioning/admin/provision',json={'token':preview['token']},headers=csrf(admin_client))
    with app.app_context():
        assert Users.query.filter_by(name=username).count()==0
    retry=admin_client.post('/plugins/ctfd-account-provisioning/admin/provision',json={'token':preview['token']},headers=csrf(admin_client))
    assert retry.json['total_success']==1


def test_provision_partial_success_after_preview_collision(app, admin_client):
    preview=upload(admin_client,'P1,First'+uuid.uuid4().hex[:8]+'\nP2,Second'+uuid.uuid4().hex[:8]+'\n').json
    collided=preview['participants'][0]
    with app.app_context():
        db.session.add(Users(name=collided['username'],email=collided['email'],password='different'))
        db.session.commit()
    result=admin_client.post('/plugins/ctfd-account-provisioning/admin/provision',json={'token':preview['token']},headers=csrf(admin_client))
    assert result.json['total_success']==1 and result.json['total_failed']==1
    output=admin_client.get('/plugins/ctfd-account-provisioning/admin/download/'+result.json['doc_token'])
    from docx import Document
    text=' '.join(cell.text for t in Document(io.BytesIO(output.data)).tables for row in t.rows for cell in row.cells)
    assert collided['password'] not in text
    assert preview['participants'][1]['password'] in text


def test_preview_cancel_and_recovery_page(app, admin_client):
    token=upload(admin_client,'P1,Cancel'+uuid.uuid4().hex[:8]+'\n').json['token']
    response=admin_client.delete('/plugins/ctfd-account-provisioning/admin/preview/'+token,json={},headers=csrf(admin_client))
    assert response.status_code==200
    assert admin_client.post('/plugins/ctfd-account-provisioning/admin/provision',json={'token':token},headers=csrf(admin_client)).status_code==400
    token=upload(admin_client,'P1,Recover'+uuid.uuid4().hex[:8]+'\n').json['token']
    assert admin_client.post('/plugins/ctfd-account-provisioning/admin/provision',json={'token':token},headers=csrf(admin_client)).json['total_success']==1
    assert ('/admin/download/'+token).encode() in admin_client.get('/plugins/ctfd-account-provisioning/admin').data
    # A stale Cancel request cannot delete already-created credentials.
    admin_client.delete('/plugins/ctfd-account-provisioning/admin/preview/'+token,json={},headers=csrf(admin_client))
    assert admin_client.get('/plugins/ctfd-account-provisioning/admin/download/'+token).status_code==200
