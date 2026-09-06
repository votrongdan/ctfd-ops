#!/bin/bash
python internal.py &
gunicorn --bind 0.0.0.0:80 --workers 4 app:app
