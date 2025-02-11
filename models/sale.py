from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # payment_mode = fields.Char(string='Mode de Payment', required=False)

    type_order = fields.Selection([
        ('commande', 'Commande Simple'),
        ('pack', 'Pack promo'),
    ], string='Type de Commande', default='commande')

    payment_mode = fields.Selection([
        ('online', 'En ligne'),
        ('domicile', 'chez le client'),
        ('echelonne', 'Échelonné')
    ], string='Mode de Payment', required=False)