#!/bin/bash

uv pip install -r requirements.txt --system
python3 manage.py collectstatic --noinput
python3 manage.py migrate --noinput
python3 manage.py populate_tests