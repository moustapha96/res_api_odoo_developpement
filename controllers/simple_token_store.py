# -*- coding: utf-8 -*-

import time
import logging
import hashlib

_logger = logging.getLogger(__name__)


class SimpleTokenStore(object):
    
    def hash(self, token):
        return hashlib.sha1(token.encode('utf-8')).hexdigest()
    
    def save_all_tokens(self, env, access_token, expires_in,
                    refresh_token, refresh_expires_in, user_id):
        current_time = time.time()
        # access_token
        env['rest.api.access.token'].sudo().create({
            'access_token': self.hash(access_token),
            'user_id':      user_id,
            'expiry_time':  current_time + expires_in,
        })
        # refresh_token
        env['rest.api.refresh.token'].sudo().create({
            'refresh_token': self.hash(refresh_token),
            'access_token': self.hash(access_token),
            'user_id':      user_id,
            'expiry_time':  current_time + refresh_expires_in,
        })
    
    def fetch_by_token(self, env, type, token):
        table = 'rest.api.' + type + '.token'
        field = type + '_token'
        res = None
        token = self.hash(token)
        existing_token = env[table].sudo().search([
            (field, '=', token)], limit=1)
        if existing_token:
            # Check expiry time
            current_time = time.time()
            if existing_token.expiry_time >= current_time:
                res = existing_token
        return res
    
    def fetch_by_access_token(self, env, access_token):
        return self.fetch_by_token(env, 'access', access_token)
    
    def fetch_by_refresh_token(self, env, refresh_token):
        return self.fetch_by_token(env, 'refresh', refresh_token)
    
    def delete_by_token(self, env, type, token):
        table = 'rest.api.' + type + '.token'
        field = type + '_token'
        if type != 'access':
            token = self.hash(token)
        existing_token = env[table].sudo().search([
            (field, '=', token)])
        if existing_token:
            existing_token.unlink()
    
    def delete_access_token(self, env, access_token):
        self.delete_by_token(env, 'access', access_token)
    
    def delete_refresh_token(self, env, refresh_token):
        self.delete_by_token(env, 'refresh', refresh_token)
    
    def update_access_token(self, env, old_access_token,
                            new_access_token, expires_in,
                            refresh_token, user_id):
        current_time = time.time()
        # Delete old access token
        self.delete_access_token(env, old_access_token)
        # Create new access token
        env['rest.api.access.token'].sudo().create({
            'access_token': self.hash(new_access_token),
            'user_id':      user_id,
            'expiry_time':  current_time + expires_in,
        })
        # Update refresh token
        refresh_token = self.hash(refresh_token)
        env['rest.api.refresh.token'].sudo().search([
            ('refresh_token', '=', refresh_token)], limit=1)\
                .write({
                    'access_token': self.hash(new_access_token)
                })
    
    def delete_all_tokens_by_refresh_token(self, env, refresh_token):
        refresh_token_data = self.fetch_by_refresh_token(env, refresh_token)
        if refresh_token_data:
            access_token = refresh_token_data.access_token
            # Delete tokens
            self.delete_access_token(env, access_token)
            self.delete_refresh_token(env, refresh_token)
