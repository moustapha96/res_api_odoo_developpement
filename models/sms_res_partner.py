

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64
_logger = logging.getLogger(__name__)


class SmsResPartner(models.Model):
    _inherit = 'res.partner'
    

    def action_send_sms(self):
        for partner in self:
            if not partner.phone:
                raise UserError(_("Ce contact n'a pas de numéro de téléphone."))

            message = f"Bonjour {partner.name}, ceci est un message depuis CCBM."
            sms_service = self.env['orange.sms.sender']
            result = sms_service.send_sms(partner.phone, message)

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
