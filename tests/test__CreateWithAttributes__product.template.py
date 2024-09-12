#!/usr/bin/python2

import requests, json


print '\n 1. Login in Odoo and get access tokens:'
r = requests.get(
    'http://localhost:8069/api/auth/get_tokens',
    headers = {'Content-Type': 'text/html; charset=utf-8'},
    data = json.dumps({
        'username': 'admin',
        'password': 'admin',
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
access_token = r.json()['access_token']


print '\n 2. product.template - Create one:'
r = requests.post(
    'http://localhost:8069/api/product.template',
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'access_token': access_token
    },
    data = json.dumps({
        
        # simple field (non relational)
        'name': 'TEST Product (with attributes)',
        
        # one2many field (list of dictionaries of new records)
        'attribute_line_ids': [
            {
                # Database data description:
                # "Color" is 'product.attribute' ID: 2
                # "White" is 'product.attribute.value' ID: 3
                # "Black" is 'product.attribute.value' ID: 4
                
                # many2one field (EXISTING 'id', NOT dictionary of new record!)
                'attribute_id': 2,  # "Color"
                
                # For more than one level of nesting you should use the
                # special Odoo syntax, something like this:
                
                # many2many field
                # (here you can CREATE a NEW value(s) using a TECHNICAL PREFIX)
                'value_ids': [
                    (0, 0, {'name': 'Green', 'attribute_id': 2}),
                    (0, 0, {'name': 'Red', 'attribute_id': 2}),
                ],
                # (OR you can use an EXISTING ids with a TECHNICAL PREFIX)
                #'value_ids': [(6,0, [3, 4])],  # ["White", "Black"]
                # (or equivalent way)
                #'value_ids': [(4, 3), (4, 4)],
                
                # Here are more DETAILS on creating/updating x2many fields:
                #   https://www.odoo.com/documentation/16.0/developer/reference/addons/orm.html#odoo.fields.Command
                #   https://www.odoo.com/forum/help-1/question/how-to-insert-value-to-a-one2many-field-in-table-with-create-method-28714
                #   https://stackoverflow.com/questions/26011102/openerp-odoo-model-relationship-xml-syntax
                #   https://doc.odoo.com/v6.0/developer/2_5_Objects_Fields_Methods/methods.html
            },
            #...
        ],
        
    }),
    #verify = False      # for self-signed TLS/SSL certificates
)
print r.text
