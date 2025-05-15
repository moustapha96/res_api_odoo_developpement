from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SendSms(models.TransientModel):  # Utilise TransientModel pour un wizard
    _name = 'orange.send.sms'
    _description = 'Envoyer un SMS'

    recipient = fields.Many2one('res.partner', string="Destinataire", required=True)
    phone = fields.Char(related='recipient.phone', string="Téléphone", readonly=True)
    message = fields.Text(string="Message", required=True)

    def send_sms(self):
        for record in self:
            if not record.recipient.phone:
                raise UserError("Ce contact n'a pas de numéro de téléphone.")
            _logger.info(f"Envoi du SMS à {record.recipient.phone} : {record.message}")
            # ICI tu peux appeler ton API (ex: Twilio, Orange, etc.)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Succès',
                    'message': f'SMS envoyé à {record.recipient.name}',
                    'type': 'success',
                    'sticky': False,
                }
            }
