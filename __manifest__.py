# -*- coding: utf-8 -*-
{
    'name': 'REST API orbit',
    'version': '16.0.2',
    'category': 'Extra Tools',
    'author': "CCBM Technologies",
    'support': 'alhussein.khouma@ccbm.sn',
    'license': 'OPL-1',
    'website': 'https://app.swaggerhub.com/apis-docs/avs3/odoo_rest_api/1',
    'price': 55.00,
    'category': 'CCBM/',
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
        'modul-sms-odoo'
        # 'orbit'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        
        'views/ir_model_view.xml',
        'views/res_partner_view.xml',
        'views/product_template_view.xml',
        
        'views/ir_cron_data.xml',
        'views/crm_lead_view.xml',
        'views/pack_views.xml',
        'views/sale_order_view.xml',

        'views/res_partner_bank_model.xml'
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
