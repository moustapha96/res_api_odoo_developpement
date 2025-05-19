from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SmsFunctionOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Fonctionnalité SMS pour les commandes'
    _order = 'id desc'
    
    def action_send_sms(self):
        """
        Action pour envoyer les détails de la commande par SMS
        """
        sms_sender = self.env['orange.sms.sender']
        result = sms_sender.send_order_details_sms(self.id)

        if result['status'] == 'success':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Succès'),
                    'message': result['message'],
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erreur'),
                    'message': result['message'],
                    'type': 'danger',
                    'sticky': False,
                }
            }
