# my_module/controllers/controllers.py
from odoo import http


from .main import *
import pdb
import datetime
import logging
# import json
import json

from odoo.http import request

import werkzeug



class CommentaireController(http.Controller):

    @http.route('/api/commentaires', methods=['GET'], type='http', auth='none', cors="*")
    def get_comments(self):


        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        # Récupération des commentaires
        comments = request.env['web.commentaire'].sudo().search([])

        # Préparer la réponse JSON
        response = []
        for comment in comments:
            response.append({   
                'id': comment.id,
                'author': comment.author,
                'text': comment.text,
                'date': comment.date.strftime('%Y-%m-%d %H:%M:%S') if comment.date else None  # Sérialisation des dates
            })
        
        # Créer une réponse HTTP
        resp = werkzeug.wrappers.Response(
            response=json.dumps(response),
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')]
        )
        return resp

        


    @http.route('/api/commentaires', methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def post_comment(self, **kw):
        
        data = json.loads(request.httprequest.data)
        author = data.get('author')
        text = data.get('text')
        date = datetime.datetime.now()
    
        if not author or not text:
            return http.Response('Missing required fields', status=400)
        
        comment = request.env['web.commentaire'].sudo().create({
            'author': author,
            'text': text,
            'date': date
        })
        resultat = {
            'author': comment.author,
            'text': comment.text,
            'date': comment.date.strftime('%Y-%m-%d %H:%M:%S') if comment.date else None
        }
        resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(resultat)
            )
        return resp
       
