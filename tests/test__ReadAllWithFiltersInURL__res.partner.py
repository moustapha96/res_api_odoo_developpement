#!/usr/bin/python2

import requests


print '\n 1. Login in Odoo and get access tokens:'
r = requests.get(
    'http://localhost:8069/api/auth/get_tokens?username=admin&password=admin',
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
access_token = r.json()['access_token']


print '\n 2. res.partner - Read all (with filters in URL):'
r = requests.get(
    "http://localhost:8069/api/res.partner?filters=[('name','like','ompany'),('id','!=',50)]",
    headers = {'Access-Token': access_token},
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
