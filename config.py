import os

workers = int(os.environ.get('GUNICORN_PROCESSES', '1'))
threads = int(os.environ.get('GUNICORN_THREADS', '2'))

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}
