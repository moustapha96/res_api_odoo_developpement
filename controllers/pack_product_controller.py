from odoo import http
from odoo.http import request

import json
import base64
import logging


class PackProductController(http.Controller):

    @http.route('/api/pack_product2/<string:code>', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def get_pack_product_by_code2(self, code):
        
        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        pack = request.env['pack.produit'].sudo().search([('code', '=', code)], limit=1)
        # sommeTotal = 0
        # for line in pack.product_line_ids:
        #     sommeTotal += line.price_unit
        sommeTotal = sum(line.price_unit * line.quantity for line in pack.product_line_ids)
       
        if pack:
            return request.make_response(
                json.dumps({
                    'id': pack.id,
                    'name': pack.name,
                    'start_date': pack.start_date.strftime('%Y-%m-%d') if pack.start_date else None,
                    'end_date': pack.end_date.strftime('%Y-%m-%d') if pack.end_date else None,
                    'state': pack.state,
                    'sommeTotal': sommeTotal,
                    'produits': [
                        {
                            'id': line.id,
                            'category': line.product_id.categ_id.name if line.product_id.categ_id else None,
                            'product_id': line.product_id.id,
                            'image': base64.b64encode(line.product_id.image_1920).decode('utf-8') if line.product_id.image_1920 else None,
                            'name': line.product_id.name,
                            'price_unit': line.price_unit,
                            'quantity': line.quantity
                        }
                        for line in pack.product_line_ids
                    ]
                }),
                status=200,
                headers={'Content-Type': 'application/json'}
            )
        else:
            return request.make_response(json.dumps({'error': 'Pack not found'}), status=404)



    @http.route('/api/pack_product/<string:code>', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def get_pack_product_by_code(self, code):
        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        pack = request.env['pack.produit'].sudo().search([('code', '=', code)], limit=1)
        sommeTotal = sum(line.price_unit * line.quantity for line in pack.product_line_ids)

        if pack:
            produits = []
            for line in pack.product_line_ids:

                image_base64 = line.product_id.image_1920.decode('utf-8') if line.product_id.image_1920 else ''
                image_data = f"data:image/jpeg;base64,{image_base64}" 

                produits.append({
                    'id': line.id,
                    'category': line.product_id.categ_id.name if line.product_id.categ_id else None,
                    'product_id': line.product_id.id,
                    'image': image_data, 
                    'name': line.product_id.name,
                    'price_unit': line.price_unit,
                    'quantity': line.quantity
                })

            response_data = {
                'id': pack.id,
                'name': pack.name,
                'start_date': pack.start_date.strftime('%Y-%m-%d') if pack.start_date else None,
                'end_date': pack.end_date.strftime('%Y-%m-%d') if pack.end_date else None,
                'state': pack.state,
                'sommeTotal': sommeTotal,
                'produits': produits
            }

            return request.make_response(
                json.dumps(response_data),
                status=200,
                headers={'Content-Type': 'application/json'}
            )
        else:
            return request.make_response(json.dumps({'error': 'Pack not found'}), status=404)

