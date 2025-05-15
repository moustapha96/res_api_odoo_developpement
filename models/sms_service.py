# from odoo import models, fields, api, _
# from odoo.exceptions import UserError
# import requests
# import hashlib
# import hmac
# import time
# import urllib.parse
# import logging

# _logger = logging.getLogger(__name__)

# class SmsConfig(models.Model):
#     _name = 'orange.sms.config'
#     _description = 'Configuration SMS'

#     login = fields.Char('Login', required=True)
#     token = fields.Char('Token', required=True)
#     api_key = fields.Char('API Key', required=True)
#     signature = fields.Char('Signature', required=True)
#     subject = fields.Char('Sujet', default="CCBM-SHOP")

#     @api.model
#     def get_config(self):
#         """Récupérer la configuration SMS"""
#         config = self.search([], limit=1)
#         if not config:
#             raise UserError(_("Veuillez configurer les paramètres SMS."))
#         return config

# class SmsSender(models.AbstractModel):
#     _name = 'orange.sms.sender'
#     _description = 'Service d\'envoi de SMS'

#     @api.model
#     def send_sms(self, recipient, message):
#         """
#         Méthode pour envoyer un SMS
#         :param recipient: Numéro de téléphone du destinataire
#         :param message: Contenu du message
#         :return: dict avec status (success/error) et message
#         """
#         _logger.info(f"SMS envoyé à {recipient} : {message}")
#         config = self.env['orange.sms.config'].get_config()
        
#         # Préparation des paramètres
#         login = config.login
#         token = config.token
#         api_key = config.api_key
#         signature = config.signature
#         subject = config.subject
#         timestamp = int(time.time())
        
#         # Encodage du message
#         content = urllib.parse.quote_plus(message.encode('utf-8'), safe='')
        
#         # Création de la signature
#         msg_to_encrypt = f"{token}{subject}{signature}{recipient}{content}{timestamp}"
#         key = hmac.new(api_key.encode('utf-8'), msg_to_encrypt.encode('utf-8'), hashlib.sha1).hexdigest()
        
#         try:
#             parameters = {
#                 'token': token,
#                 'subject': subject,
#                 'signature': signature,
#                 'recipient': recipient,
#                 'content': message,
#                 'timestamp': timestamp,
#                 'key': key
#             }
            
#             headers = {
#                 'Content-Type': 'application/x-www-form-urlencoded',
#             }
            
#             uri = "https://api.orangesmspro.sn:8443/api"
#             response = requests.post(uri, data=parameters, headers=headers, auth=(login, token))
            
#             _logger.info(f"Réponse API SMS: {response.text}")
            
#             # Analyse de la réponse
#             response_lines = response.text.strip().split('\n')
#             response_dict = {}
            
#             for line in response_lines:
#                 if ':' in line:
#                     key, value = line.split(':', 1)
#                     response_dict[key.strip()] = value.strip()
            
#             if response_dict.get('STATUS_CODE') == '200':
#                 return {
#                     'status': 'success',
#                     'message': 'SMS envoyé avec succès'
#                 }
#             else:
#                 return {
#                     'status': 'error',
#                     'message': f"Erreur: {response_dict.get('STATUS_TEXT', 'Erreur inconnue')}",
#                     'code': response_dict.get('STATUS_CODE')
#                 }
                
#         except Exception as e:
#             _logger.error(f"Erreur d'envoi SMS: {str(e)}")
#             return {
#                 'status': 'error',
#                 'message': str(e)
#             }

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import hashlib
import hmac
import time
import urllib.parse
import logging

_logger = logging.getLogger(__name__)

class SmsConfig(models.Model):
    _name = 'orange.sms.config'
    _description = 'Configuration SMS'

    login = fields.Char('Login', required=True)
    token = fields.Char('Token', required=True)
    api_key = fields.Char('API Key', required=True)
    signature = fields.Char('Signature', required=True)
    subject = fields.Char('Sujet', default="CCBM-SHOP")

    @api.model
    def get_config(self):
        """Récupérer la configuration SMS"""
        config = self.search([], limit=1)
        if not config:
            raise UserError(_("Veuillez configurer les paramètres SMS."))
        return config

class SmsSender(models.TransientModel):
    _name = 'orange.sms.sender'
    _description = 'Service d\'envoi de SMS'

    recipient = fields.Char('Destinataire', required=True, help="Numéro de téléphone du destinataire")
    message = fields.Text('Message', required=True, help="Contenu du message à envoyer")

    @api.model
    def send_sms(self, recipient, message):
        """
        Méthode pour envoyer un SMS
        :param recipient: Numéro de téléphone du destinataire
        :param message: Contenu du message
        :return: dict avec status (success/error) et message
        """
        _logger.info(f"SMS envoyé à {recipient} : {message}")
        config = self.env['orange.sms.config'].get_config()
        
        # Préparation des paramètres
        login = config.login
        token = config.token
        api_key = config.api_key
        signature = config.signature
        subject = config.subject
        timestamp = int(time.time())
        
        # Encodage du message
        content = urllib.parse.quote_plus(message.encode('utf-8'), safe='')
        
        # Création de la signature
        msg_to_encrypt = f"{token}{subject}{signature}{recipient}{content}{timestamp}"
        key = hmac.new(api_key.encode('utf-8'), msg_to_encrypt.encode('utf-8'), hashlib.sha1).hexdigest()
        
        try:
            parameters = {
                'token': token,
                'subject': subject,
                'signature': signature,
                'recipient': recipient,
                'content': message,
                'timestamp': timestamp,
                'key': key
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            uri = "https://api.orangesmspro.sn:8443/api"
            response = requests.post(uri, data=parameters, headers=headers, auth=(login, token))
            
            _logger.info(f"Réponse API SMS: {response.text}")
            
            # Analyse de la réponse
            response_lines = response.text.strip().split('\n')
            response_dict = {}
            
            for line in response_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    response_dict[key.strip()] = value.strip()
            
            if response_dict.get('STATUS_CODE') == '200':
                return {
                    'status': 'success',
                    'message': 'SMS envoyé avec succès'
                }
            else:
                return {
                    'status': 'error',
                    'message': f"Erreur: {response_dict.get('STATUS_TEXT', 'Erreur inconnue')}",
                    'code': response_dict.get('STATUS_CODE')
                }
                
        except Exception as e:
            _logger.error(f"Erreur d'envoi SMS: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def send_sms_action(self):
        """Action pour envoyer un SMS depuis l'interface utilisateur"""
        self.ensure_one()
        result = self.send_sms(self.recipient, self.message)
        
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