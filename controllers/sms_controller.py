from odoo import http
from odoo.http import request
import requests
import hashlib
import hmac
import time
import urllib.parse
import logging
import json

_logger = logging.getLogger(__name__)

class SmsController(http.Controller):
    
    @http.route('/api/sms/<telephone>/envoyer', methods=['GET'], type='http', auth='none', cors="*")
    def tester_envoi_sms(self, telephone, **kwargs):
        """
        Route pour tester l'envoi de SMS via URL
        Exemple d'utilisation: /api/sms/221XXXXXXXX/envoyer?message=Votre+message+de+test
        """
        # Authentification comme admin si utilisateur public
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        # Récupération du message depuis les paramètres de l'URL
        message = kwargs.get('message', 'Ceci est un message de test')
        
        try:
            # Utilisation du service d'envoi de SMS
            result = request.env['orange.sms.sender'].sudo().send_sms(telephone, message)
            
            # Log du résultat
            _logger.info(f"Test d'envoi SMS: {result}")
            
            # Réponse JSON
            return request.make_response(
                json.dumps(result),
                status=200,
                headers={'Content-Type': 'application/json'}
            )
            
        except Exception as e:
            error_message = str(e)
            _logger.error(f"Erreur lors du test d'envoi SMS: {error_message}")
            
            return request.make_response(
                json.dumps({
                    'status': 'error',
                    'message': error_message
                }),
                headers={'Content-Type': 'application/json'}
            )
