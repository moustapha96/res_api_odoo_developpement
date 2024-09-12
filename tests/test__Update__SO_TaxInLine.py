#!/usr/bin/python3

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


print('\n 2. sale.order - Update one:')
r = requests.put(
    'http://localhost:8069/api/sale.order/3',  # fill SO 'id' here
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': access_token
    },
    data = json.dumps({
        # simple field (non relational)
        'note': 'TAXES UPDATE TEST !!!',
        
        # one2many field
        'order_line': [
            {
                'id': 7,  # fill LINE 'id' here
                
                # Database data description:
                # "Tax 15.00%"  is 'account.tax' ID: 1
                # "Tax 5%"      is 'account.tax' ID: 3
                
                # For more than one level of nesting you should use the
                # special Odoo syntax, something like this:
                
                # many2many field
                'tax_id': [
                    (6,0, [1, 3])  # ["Tax 15.00%", "Tax 5%"]
                ],
                
                # Here are more DETAILS on creating/updating x2many fields:
                #   https://www.odoo.com/documentation/16.0/developer/reference/addons/orm.html#odoo.fields.Command
                #   https://www.odoo.com/forum/help-1/question/how-to-insert-value-to-a-one2many-field-in-table-with-create-method-28714
                #   https://stackoverflow.com/questions/26011102/openerp-odoo-model-relationship-xml-syntax
                #   https://doc.odoo.com/v6.0/developer/2_5_Objects_Fields_Methods/methods.html
            },
        ],
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print(r.text)
