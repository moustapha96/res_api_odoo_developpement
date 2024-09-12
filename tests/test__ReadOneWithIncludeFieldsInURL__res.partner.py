#!/usr/bin/python

import requests


print('\n 1. Login in Odoo and get access tokens:')
r = requests.get(
    'http://localhost:8069/api/auth/get_tokens?username=admin&password=admin',
    #verify = False      # for self-signed TLS/SSL certificates
)
print(r.text)
access_token = r.json()['access_token']


print("\n 2. res.partner - Read one (with 'include_fields' and 'exclude_fields' in URL):")
r = requests.get(
    "http://localhost:8069/api/res.partner/3?exclude_fields=*&include_fields=['id','name',('state_id',('code'))]",
    headers = {'Access-Token': access_token},
    #verify = False      # for self-signed TLS/SSL certificates
)
print(r.text)
