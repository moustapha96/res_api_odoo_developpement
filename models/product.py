
from odoo import models, fields

class Product(models.Model):
    _inherit = 'product.template'
  
    rang = fields.Char(string='Numero de rang', required=False)
  