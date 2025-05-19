from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SmsFunctionPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Fonctionnalité SMS pour les partenaires'

    def action_send_sms(self):
        """
        Action pour envoyer un SMS au partenaire
        """
        sms_sender = self.env['orange.sms.sender']
        recipient = self.mobile or self.phone

        if not recipient:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erreur'),
                    'message': 'Numéro de téléphone du client non trouvé',
                    'type': 'danger',
                    'sticky': False,
                }
            }

        # Créer un message par défaut
        message = f"Bonjour {self.name},\n\n"
        message += "Merci pour votre confiance.\n"
        message += "Nous sommes à votre disposition pour toute question."

        result = sms_sender.send_sms(recipient, message)

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
