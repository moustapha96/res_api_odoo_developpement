# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
# import json
import json
_logger = logging.getLogger(__name__)
from odoo.http import request, Response

import requests
from bs4 import BeautifulSoup


class GestionnaireController(http.Controller):



    # get partner by id
    @http.route('/api/gestion/clients/liste', methods=['GET'], type='http', auth='none', cors="*" )
    def api_get_clients(self, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partners = request.env['res.partner'].sudo().search([('is_company', '=', False)])

        resultats = []
        # convert to json
        for partner in partners:
            resultats.append({
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'company_id': partner.company_id.id,
                'partner_id': partner.id,
                'company_name': partner.company_id.name,
                'partner_city': partner.city,
                'partner_phone': partner.phone,
                'country_id': partner.country_id.id,
                'country_name': partner.country_id.name,
                'country_code': partner.country_id.code,
                'country_phone_code': partner.country_id.phone_code,
                'is_verified': partner.is_verified,
                'avatar': partner.avatar,
                'role': partner.role,
                'adhesion': partner.adhesion,
                'adhesion_submit': partner.adhesion_submit,
                'function': partner.function,
                'parent_id': partner.parent_id.id,
                
            })

        if partners:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(resultats))


    # enable desable is_verified partner
    @http.route('/api/gestion/clients/<int:id>/compte', methods=['GET'], type='http', auth='none', cors="*")
    def api_update_client(self, id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Client non trouvé"}))

        partner.write({'is_verified': not partner.is_verified})

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({ "status": "success", "message": "Client mis à jour"}))

        
    @http.route('/api/gestion/orders/liste', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_order(self, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        order_data = []
        orders = request.env['sale.order'].sudo().search([])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_rh_state': o.validation_rh_state,
                    'validation_admin_state': o.validation_admin_state,
                    'type_sale':  o.type_sale,
                    'date_order': o.date_order.isoformat() if o.date_order else None,
                    'name': o.name,
                    'payment_mode': o.payment_mode,
                    'partner_id': o.partner_id.id or None,
                    'partner_name': o.partner_id.name or None,
                    'partner_street': o.partner_id.street or None,
                    'partner_street2': o.partner_id.street2 or None,
                    'partner_city': o.partner_id.city or None,
                    'partner_country_id': o.partner_id.country_id.id or None,
                    'partner_country_name': o.partner_id.country_id.name or None,
                    'partner_email': o.partner_id.email or None,
                    'partner_phone': o.partner_id.phone or None,
                    'amount_untaxed': o.amount_untaxed or None,
                    'amount_tax': o.amount_tax or None,
                    'amount_total': o.amount_total or None,
                    'state': o.state or None,
                    'user_id': o.user_id.id or None,
                    'user_name': o.user_id.name or None,
                    'create_date': o.create_date.isoformat() if o.create_date else None,
                    'advance_payment_status':o.advance_payment_status,
                    'amount_residual': o.amount_residual,
                    'commitment_date': o.commitment_date.isoformat() if o.commitment_date else None,

                    # 'first_payment_date': o.first_payment_date.isoformat() if o.first_payment_date else None,
                    # 'second_payment_date': o.second_payment_date.isoformat() if o.second_payment_date else None,
                    # 'third_payment_date': o.third_payment_date.isoformat() if o.third_payment_date else None,
                    # 'fourth_payment_date': o.fourth_payment_date.isoformat() if o.fourth_payment_date else None,

                    # 'first_payment_amount': o.first_payment_amount,
                    # 'second_payment_amount': o.second_payment_amount,
                    # 'third_payment_amount': o.third_payment_amount,
                    # 'fourth_payment_amount': o.fourth_payment_amount,

                    # 'first_payment_state': o.first_payment_state,
                    # 'second_payment_state': o.second_payment_state,
                    # 'third_payment_state': o.third_payment_state,
                    # 'fourth_payment_state': o.fourth_payment_state,

                    'payment_lines': o.get_sale_order_credit_payment(),

                    'order_lines': [{
                        'id': l.id or None,
                        'product_id': l.product_id.id or None,
                        'product_name': l.product_id.name or None,
                        'product_uom_qty': l.product_uom_qty or None,
                        'product_uom': l.product_uom.id or None,
                        'product_uom_name': l.product_uom.name or None,
                        'price_unit': l.price_unit or None,
                        'price_subtotal': l.price_subtotal or None,
                        'price_tax': l.price_tax or None,
                        'price_total': l.price_total or None,
                        'qty_delivered': l.qty_delivered or None,
                        'qty_to_invoice': l.qty_to_invoice or None,
                        'qty_invoiced': l.qty_invoiced or None
                    } for l in o.order_line]
                })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(order_data)
            )
            return resp
        
        return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps([])
            )
    

    @http.route('/api/gestion/commande/changeStateRH/<int:id>',  methods=['PUT'], type='http', auth='none', cors="*",  csrf=False )
    def api_change_state_rh_validation(self,id , **kw):
        # requets state in body 
        data = json.loads(request.httprequest.data)
        state = data.get('state')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        order = request.env['sale.order'].sudo().search([('id','=', id )], limit=1 )
        if not order:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        else:
            order.write({
                'validation_rh_state': state
            })
            _logger.info(res)
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "message": "Commandes mise à jour avec succés"}))

    @http.route('/api/gestion/commande/changeStateAdmin/<int:id>',  methods=['PUT'], type='http', auth='none', cors="*",  csrf=False )
    def api_change_state_admin_validation(self,id , **kw):
        # requets state in body 
        data = json.loads(request.httprequest.data)
        state = data.get('state')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        order = request.env['sale.order'].sudo().search([('id','=', id )], limit=1 )
        if not order:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        else:
            order.write({
                'validation_admin_state': state
            })
            _logger.info(res)
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "message": "Commandes mise à jour avec succés"}))



    @http.route('/api/gestion/commandes/<int:order_id>/details', methods=['GET'], type='http', auth='none', cors="*" )
    def api_get_commande_details(self,order_id, **kw):
       

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        order = request.env['sale.order'].sudo().search([('id', '=', order_id)], limit=1)
        if not order:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commande non trouvé"}))

        order_data = {
            'id': order.id,
            'validation_rh_state': order.validation_rh_state,
            'validation_admin_state': order.validation_admin_state,
            'type_sale':  order.type_sale,
            'date_order': order.date_order.isoformat() if order.date_order else None,
            'name': order.name,
            'payment_mode': order.payment_mode,
            'partner_id': order.partner_id.id or None,
            'partner_name': order.partner_id.name or None,
            'partner_city': order.partner_id.city or None,
            'partner_country_id': order.partner_id.country_id.id or None,
            'partner_country_name': order.partner_id.country_id.name or None,
            'partner_email': order.partner_id.email or None,
            'partner_phone': order.partner_id.phone or None,
            'amount_untaxed': order.amount_untaxed or None,
            'amount_tax': order.amount_tax or None,
            'amount_total': order.amount_total or None,
            'state': order.state or None,
            'user_id': order.user_id.id or None,
            'user_name': order.user_id.name or None,
            'advance_payment_status':order.advance_payment_status,
            'amount_residual': order.amount_residual,
            'create_date': order.create_date.isoformat() if order.create_date else None,

            # 'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
            # 'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
            # 'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,
            # 'fourth_payment_date': order.fourth_payment_date.isoformat() if order.fourth_payment_date else None,

            # 'first_payment_amount': order.first_payment_amount,
            # 'second_payment_amount': order.second_payment_amount,
            # 'third_payment_amount': order.third_payment_amount,
            # 'fourth_payment_amount': order.fourth_payment_amount,

            # 'first_payment_state': order.first_payment_state,
            # 'second_payment_state': order.second_payment_state,
            # 'third_payment_state': order.third_payment_state,
            # 'fourth_payment_state': order.fourth_payment_state,


            'credit_month_rate': order.credit_month_rate,
            'creditorder_month_count': order.creditorder_month_count,
            'payment_lines': order.get_sale_order_credit_payment(),
            
            'order_lines': [{
                'id': l.id or None,
                'product_id': l.product_id.id or None,
                'product_name': l.product_id.name or None,
                'product_uom_qty': l.product_uom_qty or None,
                'product_uom': l.product_uom.id or None,
                'product_uom_name': l.product_uom.name or None,
                'price_unit': l.price_unit or None,
                'price_subtotal': l.price_subtotal or None,
                'price_tax': l.price_tax or None,
                'price_total': l.price_total or None,
                'qty_delivered': l.qty_delivered or None,
                'qty_to_invoice': l.qty_to_invoice or None,
                'qty_invoiced': l.qty_invoiced or None
            } for l in order.order_line]
        }

        resp = werkzeug.wrappers.Response(    
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(order_data)
        )
        return resp;



    @http.route('/api/gestion/entreprises', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_entreprise_liste(self, **kw):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        companies = request.env['res.company'].sudo().search([])
        resultats = []
        for company in companies:
            company_data = {
                'id': company.id,
                'name': company.name or None,
                'city': company.city or None,
                'street': company.street or None,
                'country_name': {
                    'id': company.country_id.id or None,
                    'name': company.country_id.name or None
                },
                'email': company.email or None,
                'website': company.website or None,
                'mobile': company.mobile or None,
                'phone': company.phone or None,
                'company_details': company.company_details or None,
            }

            resultats.append(company_data)

        resp = werkzeug.wrappers.Response(    
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(resultats)
        )
        return resp;
 

    @http.route('/api/gestion/entreprises/<int:id>/details', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_entreprise(self, id, **kw):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Entreprise non trouvé"}))

        company_data = {
            'id': company.id,
            'name': company.name or None,
            'city': company.city or None,
            'street': company.street or None,
            'country_name': {
                'id': company.country_id.id or None,
                'name': company.country_id.name or None
            },
            'email': company.email or None,
            'website': company.website or None,
            'mobile': company.mobile or None,
            'phone': company.phone or None,
            'company_details': company.company_details or None,
        }

        resp = werkzeug.wrappers.Response(    
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(company_data)
        )
        return resp;

    
    # details partner
    @http.route('/api/gestion/clients/<int:id>/details', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_client(self, id, **kw):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        client = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not client:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Client non trouvé"}))

        client_data = {
            'id': client.id,
            'name': client.name or None,
            'city': client.city or None,
            'street': client.street or None,
            'country_name': {
                'id': client.country_id.id or None,
                'name': client.country_id.name or None
            },
            'email': client.email or None,
            'website': client.website or None,
            'mobile': client.mobile or None,
            'phone': client.phone or None,
            'function': client.function or None,
            'title': client.title or None,
            'adhesion': client.adhesion or None,
            'function': client.function
        }

        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(client_data)
        )
        return resp;
    


    @http.route('/api/gestion/clients/<int:id>/changeAdhesion',  methods=['PUT'], type='http', auth='none', cors="*",  csrf=False )
    def api_change_state_adhesion(self,id , **kw):
        # requets state in body 
        data = json.loads(request.httprequest.data)
        state = data.get('state')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        partner = request.env['res.partner'].sudo().search([('id','=', id )], limit=1 )
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        else:
           
            state_submit =  None 
            if state == "accepted":
                state_submit = False
            elif state == "pending": 
                state_submit = True
            elif state == "rejected":
                state_submit = False
                partner.write({
                    'parent_id': None,
                    'adhesion_submit': False
                })
            partner.write({
                'adhesion': state  ,
                'adhesion_submit': state_submit
            })
            # res = partner.action_confirm_demande_adhesion(state)
            _logger.info(res)
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "message": "Client mise à jour avec succés"}))
        

    
    @http.route('/api/gestion/clients/<int:id>/commandes', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandes_partner(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id.id','=', partner.id )])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_rh_state': o.validation_rh_state,
                    'validation_admin_state': o.validation_admin_state,
                    'type_sale':  o.type_sale,
                    'date_order': o.date_order.isoformat() if o.date_order else None,
                    'name': o.name,
                    'payment_mode': o.payment_mode,
                    'partner_id': o.partner_id.id or None,
                    'partner_name': o.partner_id.name or None,
                    'partner_city': o.partner_id.city or None,
                    'partner_country_id': o.partner_id.country_id.id or None,
                    'partner_country_name': o.partner_id.country_id.name or None,
                    'partner_email': o.partner_id.email or None,
                    'partner_phone': o.partner_id.phone or None,
                    'amount_untaxed': o.amount_untaxed or None,
                    'amount_tax': o.amount_tax or None,
                    'amount_total': o.amount_total or None,
                    'state': o.state or None,
                    'user_id': o.user_id.id or None,
                    'user_name': o.user_id.name or None,
                    'advance_payment_status':o.advance_payment_status,
                    'amount_residual': o.amount_residual,
                    'create_date': o.create_date.isoformat() if o.create_date else None,
                    'first_payment_date': o.first_payment_date.isoformat() if o.first_payment_date else None,
                    'second_payment_date': o.second_payment_date.isoformat() if o.second_payment_date else None,
                    'third_payment_date': o.third_payment_date.isoformat() if o.third_payment_date else None,
                    'fourth_payment_date': o.fourth_payment_date.isoformat() if o.fourth_payment_date else None,

                    'first_payment_amount': o.first_payment_amount,
                    'second_payment_amount': o.second_payment_amount,
                    'third_payment_amount': o.third_payment_amount,
                    'fourth_payment_amount': o.fourth_payment_amount,

                    'first_payment_state': o.first_payment_state,
                    'second_payment_state': o.second_payment_state,
                    'third_payment_state': o.third_payment_state,
                    'fourth_payment_state': o.fourth_payment_state,
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,
                    'payment_lines': o.get_sale_order_credit_payment(),
                    
                    'order_lines': [{
                        'id': l.id or None,
                        'product_id': l.product_id.id or None,
                        'product_name': l.product_id.name or None,
                        'product_uom_qty': l.product_uom_qty or None,
                        'product_uom': l.product_uom.id or None,
                        'product_uom_name': l.product_uom.name or None,
                        'price_unit': l.price_unit or None,
                        'price_subtotal': l.price_subtotal or None,
                        'price_tax': l.price_tax or None,
                        'price_total': l.price_total or None,
                        'qty_delivered': l.qty_delivered or None,
                        'qty_to_invoice': l.qty_to_invoice or None,
                        'qty_invoiced': l.qty_invoiced or None
                    } for l in o.order_line]
                })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(order_data)
            )
            return resp
        
        return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps([])
            )


    # liste des contacts
    @http.route('/api/gestion/commentaires/liste', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commentaires(self, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        commentaires = request.env['web.commentaire.simple'].sudo().search([])
        resultats = []
        for contact in commentaires:
            resultats.append({
                'id': contact.id,
                'author': contact.author,
                'text': contact.text,
                'date': contact.date.isoformat() if contact.date else None,
                # 'phone': contact.phone
            })

        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(resultats)
        )
        return resp
          


    # une fonction pour reccupere les données dans le fichier data/terme_recherche.json
    FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/termes_recherche.json")

    @http.route('/api/gestion/terme_recherche', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_terme_recherche(self, **kw):
        """ Récupérer les termes de recherche depuis le fichier JSON. """

        # Vérification si l'utilisateur est public et le remplacer par admin si nécessaire
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        # Vérifier et créer le fichier s'il n'existe pas
        if not os.path.exists(self.FILE_PATH):
            os.makedirs(os.path.dirname(self.FILE_PATH), exist_ok=True)
            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f)  # Initialise avec un JSON vide

        # Lire le fichier JSON
        try:
            with open(self.FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return http.Response(json.dumps({"error": "Erreur lors de la lecture du fichier JSON"}), 
                                 status=500, content_type="application/json")

        # Retourner les données en JSON
        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(data, ensure_ascii=False, indent=4)
        )
        return resp
    
   
            