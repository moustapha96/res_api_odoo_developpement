#!/usr/bin/python

import requests, json


print('\n 1. Login in Odoo and get access tokens:')
r = requests.get(
    'http://localhost:8069/api/auth/get_tokens',
    headers = {'Content-Type': 'text/html; charset=utf-8'},
    data = json.dumps({
        'username': 'admin',
        'password': 'admin',
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print(r.text)
access_token = r.json()['access_token']


print('\n 2. res.partner - Read all (with filters, offset, limit, order, exclude_fields, include_fields):')
r = requests.get(
    'http://localhost:8069/api/res.partner',
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': access_token
    },
    data = json.dumps({
        'filters':  [('name', 'like', 'ompany'), ('id', '<=', 50)],
        #'filters':  [('name', 'like', 'ser'), ('id', '<=', 50),],
        #'filters':  [('id', '<=', 20)],
        #'offset':   10,
        'limit':    5,
        'order':    'name desc',  # default 'name asc'
        'exclude_fields': '*',
        'include_fields': ['id', 'name', ('state_id',('code')) ],
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print(r.text)
