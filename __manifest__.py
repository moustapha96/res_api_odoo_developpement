# -*- coding: utf-8 -*-
{
    'name': 'Odoo REST API DEV',
    'version': '16.0.1.14.8',
    'category': 'Extra Tools',
    'author': "AVS'",
    'support': 'avs3.help@gmail.com',
    'license': 'OPL-1',
    'website': 'https://app.swaggerhub.com/apis-docs/avs3/odoo_rest_api/1',
    'price': 55.00,
    'currency': 'EUR',
    'summary': """Enhanced RESTful API access to Odoo resources with (optional) predefined and tree-like schema of response Odoo fields
        ============================
        Tags: restapi, connector, connection, integration, endpoint, endpoints, route, routes, call method, calling method, openapi, oauth, swagger, webhook, webhooks, report, reports
        """,
    'live_test_url': 'https://app.swaggerhub.com/apis-docs/avs3/odoo_rest_api/1',
    'external_dependencies': {
        'python': ['simplejson'],
    },
    'depends': [
        'base',
        'web',
        'mail',
        'sale',
        'account',
        'product',
        'crm',
        'orbit'
    ],
    'data': [
        'data/ir_configparameter_data.xml',
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'views/ir_model_view.xml',
        'views/product_template_view.xml',
        'views/res_partner_view.xml',
        'views/ir_cron_data.xml',
        # 'views/pack_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
