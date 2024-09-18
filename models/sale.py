from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_mode = fields.Char(string='Mode de Payment', required=False)
  