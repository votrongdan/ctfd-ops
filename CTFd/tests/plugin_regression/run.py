"""Usage: python -m tests.plugin_regression.run [pytest arguments]."""
import os
import sys
from unittest.mock import patch

assert 'ctfd_regression' in os.environ.get('DATABASE_URL', '') or os.environ.get('DATABASE_URL', '').startswith('sqlite:'), 'Disposable database required'
from CTFd import create_app
with patch('flask_apscheduler.APScheduler.start'), patch('flask_apscheduler.APScheduler.add_job'):
    sys._ctfd_regression_app = create_app()
import pytest
raise SystemExit(pytest.main(['--import-mode=importlib', '-p', 'no:cacheprovider'] + sys.argv[1:]))
