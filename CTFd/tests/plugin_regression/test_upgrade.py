"""Upgrade an actual MariaDB installation with old Whale/SSM columns removed."""
import os
import subprocess
import pytest


def test_old_mariadb_schema_startup_and_data_preserved():
    url=os.environ.get('UPGRADE_DATABASE_URL')
    if not url: pytest.skip('UPGRADE_DATABASE_URL must name a disposable database')
    assert 'ctfd_regression_upgrade' in url
    env=dict(os.environ,DATABASE_URL=url,REDIS_URL='redis://cache:6379/2')
    setup='''
from unittest.mock import patch
from CTFd import create_app
from CTFd.models import db, Users
import importlib
with patch('flask_apscheduler.APScheduler.start'), patch('flask_apscheduler.APScheduler.add_job'):
    app=create_app()
with app.app_context():
    wm=importlib.import_module('CTFd.plugins.ctfd-whale.models')
    sm=importlib.import_module('CTFd.plugins.ctfd-single-session.models')
    user=Users.query.filter_by(name='legacy-migration-player').first()
    if user is None:
        user=Users(name='legacy-migration-player',email='legacy@example.com',password='password')
        db.session.add(user); db.session.commit()
        ch=wm.DynamicDockerChallenge(name='legacy-migration-challenge',value=500,category='Test',redirect_type='direct',redirect_port=2222)
        db.session.add(ch); db.session.commit()
        c=wm.WhaleContainer(user.id,ch.id); c.port=19119; c.flag='flag{preserved_legacy_value}'
        db.session.add(c)
        import datetime
        db.session.add(sm.SSMSession(user_id=user.id,session_hash='legacy-migration-hash',cache_key='sessionlegacy',is_active=True))
        db.session.commit()
    db.session.remove()
    with db.engine.begin() as connection:
        connection.execute('ALTER TABLE dynamic_docker_challenge DROP COLUMN redirect_rules')
        connection.execute('ALTER TABLE whale_container DROP COLUMN ports')
        connection.execute('ALTER TABLE ssm_sessions DROP COLUMN lifecycle')
        connection.execute('ALTER TABLE ssm_sessions DROP COLUMN pending_until')
'''
    verify='''
from unittest.mock import patch
from CTFd import create_app
import importlib
with patch('flask_apscheduler.APScheduler.start'), patch('flask_apscheduler.APScheduler.add_job'):
    app=create_app()
with app.app_context():
    wm=importlib.import_module('CTFd.plugins.ctfd-whale.models')
    sm=importlib.import_module('CTFd.plugins.ctfd-single-session.models')
    c=wm.WhaleContainer.query.filter_by(flag='flag{preserved_legacy_value}').one()
    assert c.port==19119 and c.ports is None and c.challenge.redirect_rules is None
    assert '19119' in c.user_access
    s=sm.SSMSession.query.filter_by(session_hash='legacy-migration-hash').one()
    assert s.is_active and s.lifecycle is None and s.pending_until is None
print('OLD_SCHEMA_STARTUP_PRESERVED')
'''
    for code in (setup,verify,verify):
        result=subprocess.run(['python','-c',code],env=env,capture_output=True,text=True,timeout=60)
        assert result.returncode==0,result.stdout+result.stderr
