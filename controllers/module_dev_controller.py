# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
# import json
import json
_logger = logging.getLogger(__name__)
from odoo.http import request, Response

class ModuleDevController(http.Controller):


    @http.route('/api/dev/webhook', methods=['POST'], type='http', auth='none', cors="*",  csrf=False)
    def api_get_data_send_by_paydunya(self,**kw):

        data = json.loads(request.httprequest.data)
        _logger.info(f"Received data: {data}")

        message_id = data.get('messageId')
        from_number = data.get('from')
        message_type = data.get('type')
        processed_data = data.get('processedData', {})
        response_message = data.get('response')
        
        self.log_message(message_type, processed_data, message_id, from_number,response_message)

        return request.make_response(
                json.dumps({'status': 'success', 'message': 'Data received and processed'}),
                status=200,
                headers={'Content-Type': 'application/json'}
            )
    
    def log_message(self, message_type, processed_data, message_id, from_number,response_message):
        log_message = f"Message ID: {message_id}, From: {from_number}, Type: {message_type}"

        if message_type == 'text':
            content = processed_data.get('content', '')
            _logger.info(f"{log_message}, Content: {content}")

        elif message_type == 'image':
            image_url = processed_data.get('imageUrl', '')
            _logger.info(f"{log_message}, Image URL: {image_url}")

        elif message_type == 'document':
            document_url = processed_data.get('documentUrl', '')
            filename = processed_data.get('documentFilename', '')
            _logger.info(f"{log_message}, Document: {filename}, URL: {document_url}")

        elif message_type == 'interactive':
            interactive_type = processed_data.get('type', '')
            if interactive_type == 'button_reply':
                button_id = processed_data.get('buttonId', '')
                button_title = processed_data.get('buttonTitle', '')
                if button_id == 'btn_yes':
                    _logger.info(f"{log_message}, Interactive Button Reply: ID={button_id}, Title={button_title}")
                elif button_id == 'btn_no':
                    _logger.info(f"{log_message}, Interactive Button Reply: ID={button_id}, Title={button_title}")
                _logger.info(f"{log_message}, Interactive Button Reply: ID={button_id}, Title={button_title}")
            elif interactive_type == 'list_reply':
                list_id = processed_data.get('listId', '')
                list_title = processed_data.get('listTitle', '')
                _logger.info(f"{log_message}, Interactive List Reply: ID={list_id}, Title={list_title}")
            elif interactive_type == 'button':
                button_text = processed_data.get('buttonText', '')
                _logger.info(f"{log_message}, Interactive Button: Text={button_text}")
            else:
                _logger.info(f"{log_message}, Unknown Interactive Type: {interactive_type}")
        else:
            _logger.info(f"{log_message}, Unknown Message Type")

        _logger.info(f"Response Message: {response_message}")