# -*- coding: utf-8 -*-

from odoo import models, fields


class IrModel(models.Model):
    _inherit = "ir.model"
    
    rest_api__used = fields.Boolean(string='Use in REST API', default=True, help="Use this model in REST API ('rest_api' module)")
    rest_api__read_all__schema = fields.Text(string="'Read all' schema", help="'Read all' predefined response SCHEMA. If empty - will return 'id', 'name'.")
    rest_api__read_one__schema = fields.Text(string="'Read one' schema", help="'Read one' predefined response SCHEMA. If empty - will return all fields (not hierarchical).")
    rest_api__create_one__schema = fields.Text(string="'Create one' response schema", help="'Create one' predefined response SCHEMA. If empty - will return 'id'.")
    rest_api__create_one__defaults = fields.Text(string="'Create one' defaults", help="'Create one' DEFAULTS values (dictionary)")
