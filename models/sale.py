from odoo import models, fields, api
from odoo.http import request
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    type_order = fields.Selection([
        ('commande', 'Commande Simple'),
        ('pack', 'Pack promo'),
    ], string='Type de Commande', default='commande')


    payment_mode = fields.Selection([
        ('online', 'En ligne'),
        ('domicile', 'chez le client'),
        ('echelonne', 'Échelonné')
    ], string='Mode de Payment', required=False)



    def send_mail(self, mail_server, partner, subject, body_html):
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{partner.email}, {additional_email}'
        # email_to = f'{partner.email}'

        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }

        mail_mail = self.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def send_sms_notification(self, notification_type):
        message_templates = {
            'validation': f"Bonjour {self.partner_id.name},\nVotre commande à crédit numéro {self.name} a été créée avec succès.",
            'rejection': f"Bonjour {self.partner_id.name},\nNous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.",
            'rh_rejection': f"Bonjour {self.partner_id.name},\nNous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par votre service des Ressources Humaines.",
            'admin_rejection': f"Bonjour {self.partner_id.name},\nNous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre administration.",
            'admin_validation': f"Bonjour {self.partner_id.name},\nNous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre administration.",
            'rh_validation': f"Bonjour {self.partner_id.name},\nNous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par votre service des Ressources Humaines.",
            'request': f"Bonjour {self.partner_id.name},\nNous avons bien reçu votre demande de commande à crédit numéro {self.name} .Elle est actuellement en cours de validation par nos services.",
            'creation': f"Bonjour {self.partner_id.name},\nVotre commande à crédit numéro {self.name} a été créée avec succès. Elle est actuellement en attente de validation par votre service des ressources humaines.",
            'hr_notification': f"Bonjour,\nUne nouvelle demande de validation de commande à crédit numéro {self.name} nécessite votre validation."
        }

        message = message_templates.get(notification_type, "")
        if message:
            recipient = self.partner_id.phone
            # result = self.env['send.sms'].sudo().send_sms(recipient, message)
            result = self.env['send.sms'].create({
                'recipient': recipient,
                'message': message,
            }).send_sms()

            _logger.info(f"SMS result: {result}")
