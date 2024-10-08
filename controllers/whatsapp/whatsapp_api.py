# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
import requests
import json
import logging
import base64

_logger = logging.getLogger(__name__)

class WhatsAppAPI:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v17.0/"
        self.phone_number_id = "376923278848154"
        self.access_token = "EAB6ggRjDQpsBO97Hduv9Imf8TjbO8tzPDiW7tSb0O6s5CpqYlUhcLxpON7u0cc8EBmL8mjeWWVnn6DmEcsIlg4AZBE8jk2ZCoph3lyth94f4QtSELZAZCLJGGh1dfZBL4oGuoXFdj3eL3jBDCP7ZAWZBer6WZBxhPrjZAduhHZBVKDC70yjm6KSW8joX6IN3DsuJFSRbo3EnXAWDtVnZBW5LUIW3z99g8YZD"

    def _make_request(self, method, endpoint, data=None):
        """
        Utility function to make HTTP requests to the WhatsApp API
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error in API request: {str(e)}")
            return None

    def send_text_message(self, to, message):
        """
        Send a text message to a WhatsApp user
        """
        endpoint = f"{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        return self._make_request("POST", endpoint, data)

    def send_image_message(self, to, image_url, caption=None):
        """
        Send an image message to a WhatsApp user
        """
        endpoint = f"{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": image_url}
        }
        if caption:
            data["image"]["caption"] = caption
        return self._make_request("POST", endpoint, data)

    def send_document_message(self, to, document_url, filename, caption=None):
        """
        Send a document message to a WhatsApp user
        """
        endpoint = f"{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }
        if caption:
            data["document"]["caption"] = caption
        return self._make_request("POST", endpoint, data)

    def send_template_message(self, to, template_name, language_code, components):
        """
        Send a template message to a WhatsApp user
        """
        endpoint = f"{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components
            }
        }
        return self._make_request("POST", endpoint, data)

    def send_interactive_message(self, to, message, buttons):
        """
        Send an interactive message with buttons to a WhatsApp user
        """
        endpoint = f"{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
                "action": {
                    "buttons": buttons
                }
            }
        }
        return self._make_request("POST", endpoint, data)

    def get_media_url(self, media_id):
        """
        Get the URL for a media file
        """
        endpoint = f"{media_id}"
        return self._make_request("GET", endpoint)

    def mark_message_as_read(self, message_id):
        """
        Mark a message as read
        """
        endpoint = f"{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        return self._make_request("POST", endpoint, data)

class ApiWhatsappREST(http.Controller):

    @http.route('/api/whatsapp/send_message', type='json', auth='user', methods=['POST'])
    def send_whatsapp_message(self, **post):
        """
        Endpoint to send a WhatsApp message
        """
        whatsapp_api = WhatsAppAPI()
        to = post.get('to')
        message = post.get('message')
        if not to or not message:
            return {'error': 'Missing required parameters'}
        result = whatsapp_api.send_text_message(to, message)
        return result

    @http.route('/api/whatsapp/send_image', type='json', auth='user', methods=['POST'])
    def send_whatsapp_image(self, **post):
        """
        Endpoint to send a WhatsApp image message
        """
        whatsapp_api = WhatsAppAPI()
        to = post.get('to')
        image_url = post.get('image_url')
        caption = post.get('caption')
        if not to or not image_url:
            return {'error': 'Missing required parameters'}
        result = whatsapp_api.send_image_message(to, image_url, caption)
        return result

    @http.route('/api/whatsapp/send_document', type='json', auth='user', methods=['POST'])
    def send_whatsapp_document(self, **post):
        """
        Endpoint to send a WhatsApp document message
        """
        whatsapp_api = WhatsAppAPI()
        to = post.get('to')
        document_url = post.get('document_url')
        filename = post.get('filename')
        caption = post.get('caption')
        if not to or not document_url or not filename:
            return {'error': 'Missing required parameters'}
        result = whatsapp_api.send_document_message(to, document_url, filename, caption)
        return result

    @http.route('/api/whatsapp/send_template', type='json', auth='user', methods=['POST'])
    def send_whatsapp_template(self, **post):
        """
        Endpoint to send a WhatsApp template message
        """
        whatsapp_api = WhatsAppAPI()
        to = post.get('to')
        template_name = post.get('template_name')
        language_code = post.get('language_code')
        components = post.get('components')
        if not to or not template_name or not language_code or not components:
            return {'error': 'Missing required parameters'}
        result = whatsapp_api.send_template_message(to, template_name, language_code, components)
        return result

    @http.route('/api/whatsapp/send_interactive', type='json', auth='user', methods=['POST'])
    def send_whatsapp_interactive(self, **post):
        """
        Endpoint to send a WhatsApp interactive message with buttons
        """
        whatsapp_api = WhatsAppAPI()
        to = post.get('to')
        message = post.get('message')
        buttons = post.get('buttons')
        if not to or not message or not buttons:
            return {'error': 'Missing required parameters'}
        result = whatsapp_api.send_interactive_message(to, message, buttons)
        return result

    @http.route('/api/whatsapp/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def whatsapp_webhook(self, **post):
        """
        Webhook to receive WhatsApp events
        """
        _logger.info("Received WhatsApp webhook")
        data = json.loads(request.httprequest.data)
        _logger.info(f"Webhook data: {data}")

        # Process the webhook data
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        messages = change.get('value', {}).get('messages', [])
                        for message in messages:
                            self._process_incoming_message(message)

        return {'status': 'success'}

    def _process_incoming_message(self, message):
        """
        Process an incoming WhatsApp message
        """
        message_type = message.get('type')
        from_number = message.get('from')
        
        if message_type == 'text':
            text = message.get('text', {}).get('body')
            _logger.info(f"Received text message from {from_number}: {text}")
            # Add your logic to handle text messages here
        elif message_type == 'image':
            image_id = message.get('image', {}).get('id')
            _logger.info(f"Received image message from {from_number}, image ID: {image_id}")
            # Add your logic to handle image messages here
        elif message_type == 'document':
            document_id = message.get('document', {}).get('id')
            _logger.info(f"Received document message from {from_number}, document ID: {document_id}")
            # Add your logic to handle document messages here
        elif message_type == 'interactive':
            interactive_type = message.get('interactive', {}).get('type')
            if interactive_type == 'button_reply':
                button_reply = message.get('interactive', {}).get('button_reply', {})
                button_id = button_reply.get('id')
                button_text = button_reply.get('title')
                _logger.info(f"Received button reply from {from_number}: ID={button_id}, Text={button_text}")
                # Add your logic to handle button replies here
            else:
                _logger.info(f"Received unsupported interactive message type from {from_number}: {interactive_type}")
        else:
            _logger.info(f"Received unsupported message type from {from_number}: {message_type}")

        # Mark the message as read
        whatsapp_api = WhatsAppAPI()
        whatsapp_api.mark_message_as_read(message.get('id'))
