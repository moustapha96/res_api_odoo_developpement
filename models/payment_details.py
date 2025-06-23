from odoo import models, fields, api

from odoo.http import request
import logging

_logger = logging.getLogger(__name__)



class PaymentDetails(models.Model):
    _name = 'payment.details'
    _description = 'Payment Details'

    transaction_id = fields.Char(string='Transaction ID', required=True)
    token_status = fields.Boolean(string='Token Status', required=True)
    url_facture = fields.Char(string='Url Facture', required=False)
    customer_name = fields.Char(string='Name Facture', required=False)
    customer_email = fields.Char(string='Email Facture', required=False)
    customer_phone = fields.Char(string='Phone Facture', required=False)
    amount = fields.Float(string='Amount', required=True)
    currency = fields.Char(string='Currency', required=False)
    payment_method = fields.Char(string='Payment Method', required=False)
    payment_token = fields.Char(string='Payment Token', required=True)
    order_name = fields.Char(string='Order Name', required=False)
    order_type = fields.Char(string='Order type', required=False)
    payment_date = fields.Datetime(string='Payment Date', required=True)

    order_id = fields.Integer(string='Order ID', required=True)
    partner_id = fields.Integer(string='Partner ID', required=True)
    # order_id = fields.Many2one('sale.order', string='Order', required=True)
    # partner_id = fields.Many2one('res.partner', string='Customer', required=True)


    payment_state = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Payment State', required=True)

    @api.model
    def set_payment_details(self, transaction_id, amount, payment_date, order_id,order_name,order_type, partner_id, payment_token, payment_state):
        # Enregistrer les détails du paiement
        p = self.create({
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': 'XOF',
            'payment_method': 'Inbound',
            'payment_date': payment_date,
            'order_id': order_id,
            'order_name': order_name,
            'order_type': order_type,
            'partner_id': partner_id,
            'payment_token': payment_token,
            'payment_state': payment_state,
            'token_status' : False
        })
        return p

    @api.model
    def get_payment_details(self, transaction_id):
        # Récupérer les détails du paiement
        payment_details = self.search([('transaction_id', '=', transaction_id)], limit=1)
        if payment_details:
            return {
                'transaction_id': payment_details.transaction_id,
                'amount': payment_details.amount,
                'currency': payment_details.currency,
                'payment_method': payment_details.payment_method,
                'payment_date': payment_details.payment_date,
                'order_id': payment_details.order_id,
                'order_name': payment_details.order_name,
                'order_type': payment_details.order_type,
                'partner_id': payment_details.partner_id,
                'payment_token': payment_details.payment_token,
                'payment_state': payment_details.payment_state,
                'url_facture': payment_details.url_facture,
                'customer_name' : payment_details.customer_name,
                'customer_email' : payment_details.customer_email,
                'customer_phone' : payment_details.customer_phone,
                'token_status': payment_details.token_status
            }
        return None

    @api.model
    def get_payment_partner(self, partner_id):
        payments = self.search([('partner_id', '=', partner_id)])
        if payments:
            payment_details = []
            for p in payments:
                payment_details.append({
                    'transaction_id': p.transaction_id,
                    'amount': p.amount,
                    'currency': p.currency,
                    'payment_method': p.payment_method,
                    'payment_date': p.payment_date.isoformat(),
                    'order_id': p.order_id,
                    'order_name': p.order_name,
                    'order_type': p.order_type,
                    'partner_id': p.partner_id,
                    'payment_token': p.payment_token,
                    'payment_state': p.payment_state,
                    'url_facture': p.url_facture,
                    'customer_name' : p.customer_name,
                    'customer_email' : p.customer_email,
                    'customer_phone' : p.customer_phone,
                    'token_status': p.token_status
                })
            return payment_details
        return []
    



class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    payment_details_ids = fields.One2many('payment.details', 'order_id', string='Payment Details')




