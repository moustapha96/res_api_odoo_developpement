#!/usr/bin/python2


url = 'http://localhost:8069'
# Tested only in Odoo v10 !!
username = 'admin'
password = 'admin'


#=============================================================
import requests, json


print "\n 1. Login in Odoo and get access tokens:"
r = requests.get(
    url + '/api/auth/get_tokens',
    headers = {'Content-Type': 'text/html; charset=utf-8'},
    data = json.dumps({
        'username': username,
        'password': password,
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
access_token = r.json()['access_token']


print "\n The following operations completely repeat the manual sequence of actions."
print " Perhaps some operations can be skipped or combined in one operation,"
print " but in that case, it's need to carefully analyze Odoo code to not miss anything!"


print "\n 2. Create Quotation (== sale.order - Create one):"
r = requests.post(
    url + '/api/sale.order',
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': access_token
    },
    data = json.dumps({
        # many2one fields (existing 'id', not dictionary of new record!):
        'partner_id':   8,
        # one2many fields (list of dictionaries of new records):
        'order_line': [
            {
                'product_id':       25,
                'product_uom_qty':  1,
                'price_unit':       100,
            },
            {
                'product_id':       35,
                'product_uom_qty':  2,
                'price_unit':       200,
            },
        ],
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
order_id = r.json()['id']


print "\n 3. Quotation >> SaleOrder (== Call method 'action_confirm' (without parameters)):"
r = requests.put(
    url + '/api/sale.order/%s/action_confirm' % order_id,
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': access_token
    },
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text


print "\n 4. Create Invoice (== Call method 'action_invoice_create' (without parameters)):"
r = requests.put(
    url + '/api/sale.order/%s/action_invoice_create' % order_id,
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': access_token
    },
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
invoice_id = eval(r.text)[0]


print "\n 5. Validate Invoice (== Call method 'action_invoice_open' (without parameters)):"
r = requests.put(
    url + '/api/account.invoice/%s/action_invoice_open' % invoice_id,
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': access_token
    },
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
