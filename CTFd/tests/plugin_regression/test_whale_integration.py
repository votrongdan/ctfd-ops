"""Real Docker Swarm, Redis allocations and FRP HTTP/TCP integration."""
import importlib
import socket
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
import requests
from CTFd.models import db
from .fixtures import make_user, login, csrf

wm = importlib.import_module('CTFd.plugins.ctfd-whale.models')
wc = importlib.import_module('CTFd.plugins.ctfd-whale.utils.cache')
ctrl = importlib.import_module('CTFd.plugins.ctfd-whale.utils.control')
routermod = importlib.import_module('CTFd.plugins.ctfd-whale.utils.routers')
docker = importlib.import_module('CTFd.plugins.ctfd-whale.utils.docker')
redirects = importlib.import_module('CTFd.plugins.ctfd-whale.utils.redirects')


def create_challenge(app, rules='', kind='http', port=8080):
    with app.app_context():
        ch=wm.DynamicDockerChallenge(name='Regression-'+uuid.uuid4().hex[:10], value=500,
                                    category='Regression', docker_image='ctfd-fix-regression-multi:latest',
                                    redirect_type=kind, redirect_port=port, redirect_rules=rules, state='visible')
        db.session.add(ch); db.session.commit()
        return ch.id


def eventually(fn):
    deadline=time.monotonic()+60
    last=None
    while time.monotonic()<deadline:
        try:
            value=fn()
            if value: return value
        except (requests.RequestException, OSError) as e: last=e
        time.sleep(.3)
    raise AssertionError('Service did not become accessible: '+str(last))


def snapshot(app, uid):
    with app.app_context():
        c=wm.WhaleContainer.query.filter_by(user_id=uid).one()
        return {'id': c.id, 'flag':c.flag, 'port':c.port, 'ports':dict(c.ports or {}), 'uuid':c.uuid,
                'rules':redirects.rules_for(c.challenge),
                'hosts':{p:redirects.http_subdomain(c,p) for p,k in redirects.rules_for(c.challenge) if k=='http'},
                'access':routermod.Router.access(c)}


def http_result(host):
    r=requests.get('http://frps:19081/', headers={'Host':host+'.127.0.0.1.nip.io'},timeout=3)
    return r.text if r.status_code==200 else None


def tcp_result(port):
    with socket.create_connection(('frps',int(port)),timeout=3) as sock:
        return sock.recv(512).decode()


@pytest.mark.parametrize('rules,kind,port', [('', 'http',8080), ('','direct',2222),
    ('8080/http,2222/direct','http',8080), ('8080/http,8081/http','http',8080),
    ('2222/direct,8080/direct','direct',2222)])
def test_real_routes_create_destroy(app, rules, kind, port):
    user=make_user(app)
    ch_id=create_challenge(app,rules,kind,port)
    try:
        with app.app_context():
            docker.DockerUtils.init()
            ok,msg=ctrl.ControlUtil.try_add_container(user.id,ch_id)
            assert ok,msg
        state=snapshot(app,user.id)
        for p,k in state['rules']:
            if k=='http':
                assert eventually(lambda: http_result(state['hosts'][p])) == p+':'+state['flag']
            elif p=='2222':
                remote=state['ports'].get(p,state['port'])
                assert eventually(lambda:tcp_result(remote)) == state['flag']
            else:
                remote=state['ports'][p]
                assert eventually(lambda: requests.get('http://frps:'+str(remote),timeout=3).text)==p+':'+state['flag']
        with app.app_context():
            pool=wc.CacheProvider(app); pool.init_port_sets()
            used=set(state['ports'].values()) | ({state['port']} if state['port'] else set())
            free={int(p) for p in pool.provider.smembers(pool.global_port_key)}
            assert not used & free
            routermod.Router.reload()
        # Same URLs/ports continue to work after a rebuild and FRP reload.
        for p,k in state['rules']:
            if k=='http': assert eventually(lambda:http_result(state['hosts'][p])) == p+':'+state['flag']
        with app.app_context():
            assert ctrl.ControlUtil.try_renew_container(user.id)[0]
            assert ctrl.ControlUtil.try_remove_container(user.id)[0]
            free={int(p) for p in pool.provider.smembers(pool.global_port_key)}
            assert used <= free
            assert wm.WhaleContainer.query.filter_by(user_id=user.id).count()==0
            assert not docker.DockerUtils.client.services.list(filters={'label':'whale_id='+str(user.id)+'-'+state['uuid']})
    finally:
        with app.app_context():
            ctrl.ControlUtil.try_remove_container(user.id)


def test_per_user_environment_flag_and_player_api(app):
    a,b=make_user(app),make_user(app)
    ch=create_challenge(app,'8080/http,2222/direct')
    clients=[]
    try:
        for u in (a,b):
            c=app.test_client(); assert login(c,u.name).status_code==302; clients.append(c)
            r=c.post('/api/v1/plugins/ctfd-whale/container?challenge_id='+str(ch),json={},headers=csrf(c))
            assert r.status_code==200,r.data
        sa,sb=snapshot(app,a.id),snapshot(app,b.id)
        assert sa['flag']!=sb['flag'] and sa['ports']!=sb['ports'] and sa['uuid']!=sb['uuid']
        assert eventually(lambda:http_result(sa['hosts']['8080']))=='8080:'+sa['flag']
        assert eventually(lambda:http_result(sb['hosts']['8080']))=='8080:'+sb['flag']
        for flag,status in [(sb['flag'],'incorrect'),(sa['flag'],'correct')]:
            r=clients[0].post('/api/v1/challenges/attempt',json={'challenge_id':ch,'submission':flag},headers=csrf(clients[0]))
            assert r.status_code==200,r.data
            assert r.json['data']['status']==status,r.json
    finally:
        with app.app_context():
            for u in (a,b): ctrl.ControlUtil.try_remove_container(u.id)


def test_exhaustion_and_frp_failure_release(app):
    user=make_user(app); ch=create_challenge(app,'2222/direct,8080/direct')
    with app.app_context():
        pool=wc.CacheProvider(app); pool.init_port_sets()
        before={int(p) for p in pool.provider.smembers(pool.global_port_key)}
        # Real Redis, constrained pool, real Docker creation and cleanup.
        pool.replace_pools({19120}, set())
        ok,msg=ctrl.ControlUtil.try_add_container(user.id,ch)
        assert not ok
        assert {int(p) for p in pool.provider.smembers(pool.global_port_key)}=={19120}
        assert wm.WhaleContainer.query.filter_by(user_id=user.id).count()==0
        pool.init_port_sets()
        real=routermod.Router._router
        original=real.ses.put
        failed=[False]
        def fail_once(*args,**kwargs):
            if not failed[0]:
                failed[0]=True
                raise requests.ConnectionError('injected FRP write failure')
            return original(*args,**kwargs)
        with patch.object(real.ses,'put',side_effect=fail_once):
            assert not ctrl.ControlUtil.try_add_container(user.id,ch)[0]
        assert {int(p) for p in pool.provider.smembers(pool.global_port_key)}==before
        assert wm.WhaleContainer.query.filter_by(user_id=user.id).count()==0


def test_failed_cleanup_retains_recovery_record(app):
    user=make_user(app); ch=create_challenge(app,'2222/direct')
    with app.app_context():
        pool=wc.CacheProvider(app); pool.init_port_sets()
        real=routermod.Router._router
        with patch.object(real.ses,'put',side_effect=requests.ConnectionError('FRP unavailable')):
            assert not ctrl.ControlUtil.try_add_container(user.id,ch)[0]
            record=wm.WhaleContainer.query.filter_by(user_id=user.id).one()
            assert record.status==-1 and record.ports
            held=set(record.ports.values())
            pool.init_port_sets()
            assert not held & {int(p) for p in pool.provider.smembers(pool.global_port_key)}
        assert ctrl.ControlUtil.try_remove_container(user.id)[0]
        assert held <= {int(p) for p in pool.provider.smembers(pool.global_port_key)}


def test_cleanup_rechecks_pending_snapshot(app):
    user=make_user(app); ch=create_challenge(app)
    with app.app_context():
        record=wm.WhaleContainer(user.id,ch); record.status=1
        db.session.add(record); db.session.commit()
        with patch.object(routermod.Router._router,'unregister') as unregister:
            ok,msg=ctrl.ControlUtil.try_remove_container(user.id,expired_only=True)
            assert not ok
            unregister.assert_not_called()
        db.session.delete(record); db.session.commit()


def test_concurrent_create_and_pool_rebuild(app):
    users=[make_user(app),make_user(app)]
    challenge=create_challenge(app,'8080/http,2222/direct')
    def create(user):
        with app.app_context(): return ctrl.ControlUtil.try_add_container(user.id,challenge)
    def rebuild():
        with app.app_context(): wc.CacheProvider(app).init_port_sets()
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            results=[executor.submit(create,user) for user in users]
            reset=executor.submit(rebuild)
            assert all(f.result()[0] for f in results)
            reset.result()
        states=[snapshot(app,user.id) for user in users]
        assert states[0]['ports']!=states[1]['ports']
        for state in states:
            assert eventually(lambda:http_result(state['hosts']['8080']))=='8080:'+state['flag']
            assert eventually(lambda:tcp_result(state['ports']['2222']))==state['flag']
    finally:
        with app.app_context():
            for user in users: ctrl.ControlUtil.try_remove_container(user.id)
