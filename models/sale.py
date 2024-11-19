from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    # first_payment_amount = fields.Float(string='First Payment Amount (50%)')
    # second_payment_amount = fields.Float(string='Second Payment Amount (15%)')
    # third_payment_amount = fields.Float(string='Third Payment Amount (15%)')
    # fourth_payment_amount = fields.Float(string='Fourth Payment Amount (20%)')

    # first_payment_date = fields.Date(string='First Payment Date')
    # second_payment_date = fields.Date(string='Second Payment Date')
    # third_payment_date = fields.Date(string='Third Payment Date')
    # fourth_payment_date = fields.Date(string='Fourth Payment Date')

    payment_mode = fields.Char(string='Mode de Payment', required=False)
    validation_state = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='État de Validation', required=True, default='pending')
    validation_rh = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='Etat de validation RH', required=True, default='pending')
    validation_admin = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='Etat de validation Admin', required=True, default='pending')
