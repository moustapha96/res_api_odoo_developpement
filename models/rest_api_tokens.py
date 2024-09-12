# -*- coding: utf-8 -*-

import time
import sys
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)
_is_used_simple_token_store = sys.modules.get('odoo.addons.rest_api.controllers.simple_token_store')


class RestApiAccessToken(models.Model):
    _name = "rest.api.access.token"
    _description = "Access Tokens ('rest_api')"
    
    access_token = fields.Char(index=True)
    # ID of Odoo user which is assigned with 'access_token'
    user_id = fields.Integer()
    # absolute expiry time of 'access_token' (in global seconds)
    expiry_time = fields.Float(index=True)
    
    @api.model
    def _cron_delete_expired_tokens(self):
        _logger.debug('_cron_delete_expired_tokens()...')
        if _is_used_simple_token_store:
            _logger.debug('delete_expired_tokens()... time: %s' % time.time())
            self.delete_expired_tokens_in_table('access')
            self.delete_expired_tokens_in_table('refresh')
    
    def delete_expired_tokens_in_table(self, table):
        model_name = 'rest.api.' + table + '.token'
        current_time = time.time()
        _logger.debug('delete_expired_tokens_in_table(): %s' % table)
        expired_tokens = self.env[model_name].sudo().search([
            ('expiry_time', '<', current_time)
        ])
        if expired_tokens:
            _logger.debug('len(expired_tokens) == %s' % len(expired_tokens))
            expired_tokens.unlink()


class RestApiRefreshToken(models.Model):
    _name = "rest.api.refresh.token"
    _description = "Refresh Tokens ('rest_api')"
    
    refresh_token = fields.Char(index=True)
    # 'access_token' which is assigned with 'refresh_token'
    access_token = fields.Char()
    # ID of Odoo user which is assigned with 'refresh_token'
    user_id = fields.Integer()
    # absolute expiry time of 'refresh_token' (in global seconds)
    expiry_time = fields.Float(index=True)
