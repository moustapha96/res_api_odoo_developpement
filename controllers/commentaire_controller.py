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
                'date': comment.date.strftime('%Y-%m-%d %H:%M:%S') if comment.date else None,
                'product_id': comment.product_id.id,
                'review': comment.review
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
        produit_id = data.get('produit_id')
        review = data.get('review')
    
        if not author or not text:
            return http.Response('Missing required fields', status=200)
        
        produit = request.env['product.product'].sudo().search([('id', '=', int(produit_id))], limit=1)
        if not produit:
            return http.Response('Produit not found', status=404)
        
        comment = request.env['web.commentaire'].sudo().create({
            'author': author,
            'text': text,
            'date': date,
            'product_id': produit.product_tmpl_id.id,
            'review': review
        })
        resultat = {
            'author': comment.author,
            'text': comment.text,
            'date': comment.date.strftime('%Y-%m-%d %H:%M:%S') if comment.date else None,
            'product_id': comment.product_id.id,
            'review': comment.review
        }
        resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(resultat)
            )
        return resp
       

    # get commentaire by id product
    @http.route('/api/commentaires/produit/<id>', methods=['GET'], type='http', auth='none', cors="*")
    def get_comment_by_id(self, id):

        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        if not id:
            return http.Response('Missing required fields', status=200)

        produit =   request.env['product.product'].sudo().search([('id', '=', int(id))], limit=1)
        if not produit:
            return http.Response('Produit not found', status=404)
        
        # comment = request.env['web.commentaire'].sudo().search([('product_id.id', '=', id )])
        comment = request.env['web.commentaire'].sudo().search([('product_id.id', '=',   produit.product_tmpl_id.id )])

        if not comment:
            resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps([])
            )
            return resp
        datas = []
        for c in comment:
            datas.append({
                'id': c.id,
                'author': c.author,
                'text': c.text,
                'date': c.date.strftime('%Y-%m-%d %H:%M:%S') if c.date else None,
                'product_id': c.product_id.id,
                'review': c.review
            })
        resp = werkzeug.wrappers.Response(
            response=json.dumps(datas),
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')]
        )
        return resp


    @http.route('/api/commentaires/simple', methods=['GET'], type='http', auth='none', cors="*")
    def get_comments_simple(self):


        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        # Récupération des commentaires
        comments = request.env['web.commentaire.simple'].sudo().search([])

        # Préparer la réponse JSON
        response = []
        for comment in comments:
            response.append({   
                'id': comment.id,
                'author': comment.author,
                'text': comment.text,
                'date': comment.date.strftime('%Y-%m-%d %H:%M:%S') if comment.date else None,
            })
        
        # Créer une réponse HTTP
        resp = werkzeug.wrappers.Response(
            response=json.dumps(response),
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')]
        )
        return resp
    


    @http.route('/api/commentaires/simple', methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def post_comment_simple(self, **kw):
        
        data = json.loads(request.httprequest.data)
        author = data.get('author')
        text = data.get('text')
        date = datetime.datetime.now()
    
        if not author or not text:
            return http.Response('Missing required fields', status=200)
        
        comment = request.env['web.commentaire.simple'].sudo().create({
            'author': author,
            'text': text,
            'date': date,
        })
        resultat = {
            'author': comment.author,
            'text': comment.text,
            'date': comment.date.strftime('%Y-%m-%d %H:%M:%S') if comment.date else None,
        }
        resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(resultat)
            )
        return resp