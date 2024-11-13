from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_mode = fields.Char(string='Mode de Payment', required=False)
    validation_state = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='État de Validation', required=True, default='pending')
    