
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64
_logger = logging.getLogger(__name__)
class SmsSaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_send_sms(self):
        for order in self:
            if not order.partner_id.phone:
                raise UserError(_("Le client n'a pas de numéro de téléphone."))

            message = f"Bonjour {order.partner_id.name}, votre commande {order.name} a été enregistrée."
            sms_service = self.env['orange.sms.sender']
            result = sms_service.send_sms(order.partner_id.phone, message)

            if result['status'] == 'success':
                message = _("SMS envoyé avec succès.")
            else:
                message = _("Échec de l'envoi du SMS : %s") % result.get('message')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Résultat de l'envoi SMS"),
                    'message': message,
                    'type': 'success' if result['status'] == 'success' else 'danger',
                    'sticky': False,
                }
            }
