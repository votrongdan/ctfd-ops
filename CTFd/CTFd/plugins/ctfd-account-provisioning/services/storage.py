"""Database persistence; a stable key is independent of CTFd's cookie secret."""
import datetime
import hashlib
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet
from flask import current_app, session
from CTFd.models import db
from CTFd.plugins._lifecycle import lifecycle_lock
from CTFd.utils import get_config
from ..models import ProvisioningJob


def cipher():
    key = current_app.config.get('ACCOUNT_PROVISIONING_KEY') or os.environ.get('ACCOUNT_PROVISIONING_KEY')
    if key:
        return Fernet(key.encode() if isinstance(key, str) else key)
    # Uploads already have a persistent shared volume in the shipped Compose.
    path = Path(current_app.config['UPLOAD_FOLDER']) / '.account-provisioning.key'
    with lifecycle_lock('provisioning-key'):
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(Fernet.generate_key())
                stream.flush()
                os.fsync(stream.fileno())
        return Fernet(path.read_bytes())


def ttl(kind):
    default = 3600 if kind == 'preview' else 86400
    return max(1, int(get_config('account_provisioning:' + kind + '_ttl', default)))


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def encode(data):
    return cipher().encrypt(json.dumps(data, ensure_ascii=False).encode())


def decode(job):
    return json.loads(cipher().decrypt(job.payload).decode())


def save(token, data, kind='preview'):
    cleanup_expired()
    data = dict(data, token=token)
    job = ProvisioningJob(token_hash=digest(token), owner_id=session['id'], payload=encode(data),
                          expires_at=datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl(kind)))
    db.session.add(job)
    db.session.commit()
    return job


def get(token):
    job = ProvisioningJob.query.filter_by(token_hash=digest(token), owner_id=session.get('id')).first()
    if job is None or job.expires_at <= datetime.datetime.utcnow():
        return None
    return job


def delete(token):
    job = get(token)
    if job:
        db.session.delete(job)
        db.session.commit()


def cleanup_expired():
    # Caller holds provisioning lock; cannot race a long-running confirmation.
    ProvisioningJob.query.filter(ProvisioningJob.expires_at <= datetime.datetime.utcnow()).delete()
    db.session.commit()
