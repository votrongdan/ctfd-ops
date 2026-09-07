"""Disposable multi-worker HTTP integration target."""
import os
assert 'ctfd_regression' in os.environ.get('DATABASE_URL','')
from CTFd import create_app
app = create_app()
