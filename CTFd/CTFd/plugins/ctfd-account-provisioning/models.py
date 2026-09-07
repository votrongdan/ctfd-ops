"""Expiring encrypted provisioning jobs shared by every application worker."""
from CTFd.models import db


class ProvisioningJob(db.Model):
    __tablename__ = 'account_provisioning_jobs'
    token_hash = db.Column(db.String(64), primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    payload = db.Column(db.LargeBinary(length=16777215), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
