"""Run after Docker Compose startup; uses only Python's standard library."""
import json
import os
import time
import urllib.request

BASE = os.environ.get('WEALTHHUB_URL', 'http://localhost:18080').rstrip('/')

def call(path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
        return json.loads(body) if 'application/json' in response.headers.get('Content-Type', '') else body

for attempt in range(60):
    try:
        call('/api/health')
        break
    except OSError:
        if attempt == 59:
            raise
        time.sleep(2)
assert b'WealthHub' in call('/')
token = call('/api/auth/login', {'username': 'demo', 'password': 'local-demo-only'})['access_token']
assert call('/api/portfolio', token=token)['total'] == 244000
job = call('/api/onboard', {'name': 'Taylor Demo', 'email': 'taylor@example.com', 'risk': 'Balanced'}, token)
for attempt in range(30):
    status = call('/api/jobs/' + job['job_id'], token=token)['status']
    assert status != 'failed', 'Worker failed'
    if status == 'completed':
        break
    time.sleep(2)
else:
    raise RuntimeError('Worker did not complete within 60 seconds')
assert call('/api/jobs/' + job['job_id'] + '/pdf', token=token).startswith(b'%PDF')
print('PASS: health, dashboard, login, portfolio, onboarding persistence, worker, PDF download')
