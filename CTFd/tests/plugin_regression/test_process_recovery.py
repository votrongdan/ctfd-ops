"""Real gunicorn worker restart and concurrent HTTP requests against test stack."""
import concurrent.futures
import importlib
import io
import json
import os
import signal
import subprocess
import time
import uuid

import pytest
import requests
from CTFd.models import Users, db
from CTFd.utils import set_config
from .fixtures import make_user

ssm=importlib.import_module('CTFd.plugins.ctfd-single-session.session_tracker')


def nonce(client):
    response=client.get('http://127.0.0.1:8000/login',timeout=10)
    import re
    found=re.search(r'name="nonce"[^>]*value="([^"]+)"',response.text)
    assert found,response.text[:200]
    return found.group(1)


def login_http(client,name,password='password'):
    return client.post('http://127.0.0.1:8000/login',data={'name':name,'password':password,'nonce':nonce(client)},allow_redirects=False,timeout=15)


@pytest.fixture(scope='module')
def server():
    path='/tmp/ctfd-regression-gunicorn.log'
    with open(path,'w') as log:
        process=subprocess.Popen(['gunicorn','tests.plugin_regression.http_app:app','--bind','0.0.0.0:8000','--workers','2','--worker-class','gthread','--threads','2','--timeout','90'],stdout=log,stderr=log)
        try:
            deadline=time.monotonic()+45
            while time.monotonic()<deadline:
                if process.poll() is not None: raise AssertionError(open(path).read())
                try:
                    if requests.get('http://127.0.0.1:8000/login',timeout=2).status_code==200: break
                except requests.RequestException: pass
                time.sleep(.2)
            else: raise AssertionError(open(path).read())
            yield process
        finally:
            process.terminate()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()


def worker_pids(process):
    return open('/proc/'+str(process.pid)+'/task/'+str(process.pid)+'/children').read().split()


def restart_workers(process):
    old=worker_pids(process)
    process.send_signal(signal.SIGHUP)
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        children=worker_pids(process)
        if len(children)>=2 and all(pid not in children for pid in old):
            for _ in range(2):
                assert requests.get('http://127.0.0.1:8000/login',timeout=10).status_code==200
            return
        time.sleep(.2)
    raise AssertionError('Workers did not restart')


def test_multiworker_provision_retry_restart_download(app,server):
    admin=make_user(app,'admin'); client=requests.Session()
    assert login_http(client,admin.name).status_code==302
    unique='Process'+uuid.uuid4().hex[:8]
    csrf=nonce(client)
    response=client.post('http://127.0.0.1:8000/plugins/ctfd-account-provisioning/admin/upload',
        files={'file':('input.csv',('Player ID,Name\nP1,'+unique+'\n').encode(),'text/csv')},data={'nonce':csrf,'email_domain':'ctf.local'},timeout=15)
    assert response.status_code==200,response.text
    preview=response.json(); token=preview['token']
    restart_workers(server)
    cookies=client.cookies.get_dict()
    def confirm(i):
        c=requests.Session(); c.cookies.update(cookies)
        return c.post('http://127.0.0.1:8000/plugins/ctfd-account-provisioning/admin/provision',json={'token':token},headers={'CSRF-Token':csrf},timeout=30)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        results=list(ex.map(confirm,range(4)))
    assert all(r.status_code==200 and r.json()['total_success']==1 for r in results),[(r.status_code,r.text[:200]) for r in results]
    assert len({r.json()['successful'][0]['user_id'] for r in results})==1
    doc='http://127.0.0.1:8000/plugins/ctfd-account-provisioning/admin/download/'+token
    first=client.get(doc,timeout=15)
    assert first.status_code==200
    restart_workers(server)
    second=client.get(doc,timeout=15)
    assert second.status_code==200 and first.content==second.content
    assert token in client.get('http://127.0.0.1:8000/plugins/ctfd-account-provisioning/admin',timeout=15).text
    with app.app_context():
        assert Users.query.filter_by(name=preview['participants'][0]['username']).count()==1


def test_multiworker_block_login_and_restart_session(app,server):
    user=make_user(app)
    with app.app_context(): set_config('ssm:mode','block')
    clients=[requests.Session() for _ in range(4)]
    nonces=[nonce(c) for c in clients]
    def attempt(i):
        return clients[i].post('http://127.0.0.1:8000/login',data={'name':user.name,'password':'password','nonce':nonces[i]},allow_redirects=False,timeout=30)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        results=list(ex.map(attempt,range(4)))
    # A racing loser can receive the core redirect, but must never retain auth.
    authenticated=[i for i,c in enumerate(clients) if c.get('http://127.0.0.1:8000/settings',allow_redirects=False,timeout=15).status_code==200]
    assert len(authenticated)==1,[(r.status_code,r.text[:100]) for r in results]
    winner=clients[authenticated[0]]
    restart_workers(server)
    assert winner.get('http://127.0.0.1:8000/settings',allow_redirects=False,timeout=15).status_code==200
    with app.app_context():
        db.session.rollback()
        assert len(ssm.SessionTracker.get_active_sessions(user.id))==1
    winner.get('http://127.0.0.1:8000/logout',timeout=15)
    assert login_http(requests.Session(),user.name).status_code==302
