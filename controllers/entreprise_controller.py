# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
# import json
import random
import string
import json

import werkzeug.wrappers
_logger = logging.getLogger(__name__)
from odoo.http import request, Response

import requests
from bs4 import BeautifulSoup


class EntrepriseController(http.Controller):


    @http.route('/api/companies/clients/demandeAdhesion', methods=['POST'], type='http', auth='none', cors="*",  csrf=False)
    def api_send_demande_adhesion(self, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        data = json.loads(request.httprequest.data)

        parter_id = data.get('partner_id')
        codeEntreprise = data.get('entreprise_code')

        partner = request.env['res.partner'].sudo().search([('id', '=', parter_id)], limit=1)
        parent_partner = request.env['res.partner'].sudo().search([('entreprise_code', '=', codeEntreprise)], limit=1)

        if not parent_partner:
            return  werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Code entreprise incorrect"}))
        
        if not partner:
            return  werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Partenaire incorrect"}))
        
        if partner.parent_id.id == parent_partner.id and partner.adhesion == "accepted":

            return  werkzeug.wrappers.Response(
                status=302,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Vous êtes déja adhérent de cette entreprise"})
            )
        
        
        partner.write({
            'parent_id': parent_partner.id,
            'adhesion': 'pending' ,
            'adhesion_submit': True
        })
        partner.action_confirm_demande_adhesion('pending')
        resultat =  {
            'id': partner.id,
            'uid': partner.id,
            'name': partner.name,
            'email': partner.email,
            'partner_id': partner.id,
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
            'adhesion_submit' : partner.adhesion_submit,
            'role': partner.role
        }
        
        return  werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(resultat)
        )


    @http.route('/api/companies', methods=['GET'], type='http', auth='none', cors="*",  csrf=False)
    def api_get_all_companies(self,**kw):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        # type sociéte
        companies = request.env['res.partner'].sudo().search([('is_company', '=', True)])

        resultats = []

        for company in companies:
            resultats.append({
                'id': company.id,
                'name': company.name,
                'email': company.email,
                'phone': company.phone,
                'mobile': company.mobile,
                'website': company.website,
                'street': company.street,
                'city': company.city
            })
        if companies:
            return  werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(resultats))
        else:
            return  werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Pas de données"}))

    # function to create a new company and add journal type CASH1 to this company
    @http.route('/api/companies', methods=['POST'], type='http', auth='none', cors="*",  csrf=False)
    def api_create_company(self, **kw):
        data = json.loads(request.httprequest.data)

        if not data:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Données invalides"}))

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        country = request.env['res.country'].sudo().search([('id', '=', 204)], limit=1)
        # fid currency with code XOF
        currency = request.env['res.currency'].sudo().search([('name', '=', 'XOF')], limit=1)

        # this company become a society     
        company = request.env['res.company'].sudo().create({
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'website': data.get('website'),
            'currency_id': currency.id,
        })
        partner = company.partner_id
        partner.write({
            'name': data.get('name'),
            'city': data.get('city'),
            'phone': data.get('phone'),
            'country_id': country.id,
            'password': 'password',
            "role": "main_user"
        })

        # find journal with type CASH1
        journal = request.env['account.journal'].sudo().create({
            'name': 'CASH1 -%s ' % data.get('name'),
            'code': 'CSH1',
            'type': 'cash',
            'company_id': company.id,
            'currency_id': currency.id
        })

        if company and journal:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "message": "Entreprise creée"}))
        
        return werkzeug.wrappers.Response(  
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({ "status": "success", "message": "Entreprise créée"}))
    

    # get partner by id
    @http.route('/api/companies/clients/liste', methods=['POST'], type='http', auth='none', cors="*" , csrf=False)
    def api_get_company(self, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        data = json.loads(request.httprequest.data)
        partner_id = data.get('partner_id')
        parent_id = data.get('parent_id')

        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Utilisateur non autorisé"}))

        partners = request.env['res.partner'].sudo().search([('parent_id', '=', parent_id)])
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
                'role': partner.role
                
            })

        if partners:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(resultats))

    # enable desable is_verified partner
    @http.route('/api/companies/clients/compte/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_update_company(self, id, **kw):
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

        
    #  get precommande by id partner
    @http.route('/api/companies/clients/commandes/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_precommande(self, id, **kw):
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

        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id.id','=', id ) , ('type_sale' , '=' , 'creditorder' )])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'type_sale':  o.type_sale,
                    'validation_rh_state': o.validation_rh_state,
                    'validation_admin_state': o.validation_admin_state,
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
                    'fourth_payment_amount': o.fourth_payment_amount,
                    'fourth_payment_date': o.fourth_payment_date.isoformat() if o.fourth_payment_date else None,
                    'fourth_payment_state': o.fourth_payment_state,

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

    @http.route('/api/companies/clients/commandesECDV/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commande_en_cours_de_validation(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        parent = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not parent:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id.parent_id','=', parent.id ) , ('type_sale' , '=' , 'creditorder'), ('validation_rh_state' , '=' , 'pending') ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,


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

    @http.route('/api/companies/clients/commandesRejete/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commande_rejete(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        parent = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not parent:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id.parent_id','=', parent.id ) , ('type_sale' , '=' , 'creditorder' ) , ('validation_rh_state' , '=' , 'rejected') ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,

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
    

    @http.route('/api/companies/clients/commandesOrder/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commande_order(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'creditorder' ) ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,

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
    


    @http.route('/api/companies/clients/commandesPreOrder/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commande_preorder(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'preorder' ) ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,
                    
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




    @http.route('/api/companies/clients/commandesApprouve/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commande_approuve(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        parent = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not parent:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []

        orders = request.env['sale.order'].sudo().search([('partner_id.parent_id','=', parent.id ) , ('type_sale' , '=' , 'creditorder' ) , ('validation_rh_state' , '=' , 'validated') ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,

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

    
    @http.route('/api/companies/clients/commande/changeState/<int:id>',  methods=['PUT'], type='http', auth='none', cors="*",  csrf=False )
    def api_change_state_validation(self,id , **kw):
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
            # order.validate_rh()
            # res = order.action_validation_rh_state()
            _logger.info(res)
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "message": "Commandes mise à jour avec succés"}))


    @http.route('/api/companies/clients/commandes/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandes(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'order' )  ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,

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



    @http.route('/api/companies/clients/commandesCredit/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandesCredit(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        parent = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not parent:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id.parent_id','=', parent.id ) , ('type_sale' , '=' , 'creditorder')  ])
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
                    'advance_payment_status':o.advance_payment_status,
                    'amount_residual': o.amount_residual,
                    'create_date': o.create_date.isoformat() if o.create_date else None, 
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,

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
    

    # get details commande 
    @http.route('/api/companies/clients/commandes/details', methods=['POST'], type='http', auth='none', cors="*", csrf=False )
    def api_get_commande(self, **kw):
        data = json.loads(request.httprequest.data)
        order_id = data.get('order_id')
        parent_id = data.get('parent_id')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        order = request.env['sale.order'].sudo().search([('id', '=', order_id),('partner_id.parent_id','=', parent_id )], limit=1)
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
            'credit_month_rate': order.credit_month_rate,
            'creditorder_month_count': order.creditorder_month_count,

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


    # get details entreprise
    @http.route('/api/companies/<int:id>/details', methods=['GET'], type='http', auth='none', cors="*")
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

    # update details
    @http.route('/api/companies/update', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_update_entreprise(self,  **kw):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        data = json.loads(request.httprequest.data)
        id = data.get('id')
        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Entreprise non trouvé"}))

        company_data = {
            'name': data.get('name') or None,
            'city': data.get('city') or None,
            'street': data.get('street') or None,
            'country_id': data.get('country_name')['id'] or None,
            'email': data.get('email') or None,
            'website': data.get('website') or None,
            'mobile': data.get('mobile') or None,
            'phone': data.get('phone') or None,
            'company_details': data.get('company_details') or None,
        }
        _logger.info(company_data)
        company.write(company_data)

        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({ "status": "success", "message": "Entreprise mise à jour"}))

        return resp;


    # details partner
    @http.route('/api/companies/clients/compte/<int:id>/details', methods=['GET'], type='http', auth='none', cors="*")
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
            'adhesion': client.adhesion or None,
            'function': client.function,
            'parent_id': client.parent_id.id or None,
            'role': client.role,
            # 'company': {
            #     'id': client.company_id.id or None,
            #     'name': client.company_id.name or None
            # },
            'parent':{
                'id': client.parent_id.id,
                'name': client.parent_id.name or None,
                'city': client.parent_id.city or None,
                'phone': client.parent_id.phone or None,
                'email': client.parent_id.email or None,
              
            }
        }

        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(client_data)
        )
        return resp;


    # update details partner
    @http.route('/api/companies/clients/compte/update', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_update_client(self,  **kw):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        data = json.loads(request.httprequest.data)
        id = data.get('id')
        client = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not client:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Client non найд"}))

        client_data = {
            'name': data.get('name') or None,
            'city': data.get('city') or None,
            'street': data.get('street') or None,
            'country_id': data.get('country_name')['id'] or None,
            'email': data.get('email') or None,
            'website': data.get('website') or None,
            'mobile': data.get('mobile') or None,
            'phone': data.get('phone') or None,
            'function': data.get('function') or None,
            'title': data.get('title') or None,
            'adhesion': data.get('adhesion') or None
        }
        _logger.info(client_data)
        client.write(client_data)

        resp = werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({ "status": "success", "message": "Client mis à jour"}))

        return resp;
        


    @http.route('/api/companies/clients/commande/changeAdhesion/<int:id>',  methods=['PUT'], type='http', auth='none', cors="*",  csrf=False )
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
            res = partner.action_confirm_demande_adhesion(state)
            _logger.info(res)
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "message": "Client mise à jour avec succés"}))


    @http.route('/api/companies/clients/commandesPartenaire/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
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
        orders = request.env['sale.order'].sudo().search([('partner_id.id','=', partner.id ), ( 'type_sale','=','creditorder' )  ])
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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,

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
                    'credit_month_rate': o.credit_month_rate,
                    'creditorder_month_count': o.creditorder_month_count,
                    
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
    

    # fonction pour faire une demande d'adhesion
    @http.route('/api/partner/demande_adhesion', methods=['POST'], type='http', auth='none', cors="*")
    def api_demande_adhesion(self, **kw):
        data = json.loads(request.httprequest.data)
        partner_id = data.get('partner_id')
        entreprise_code = data.get('entreprise_code')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Client non trouvé"}))

        company = request.env['res.company'].sudo().search([('entreprise_code', '=', entreprise_code )], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Entreprise non trouvé"}))
        
        partner.write({
            'adhesion': 'pending',
            'company_id': company.id
        })
        partner.send_adhesion_request_mail()

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({ "status": "success", "message": "Votre demande d'adhésion est bien envoyé"}))


    # check if entrepris_code exist
    @http.route('/api/companies/check_entreprise_code', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_check_entreprise_code(self, **kw):
        data = json.loads(request.httprequest.data)
        entreprise_code = data.get('entreprise_code')
        partner_id = data.get('partner_id')

        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)

        if not partner:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ 'status': "success", "message": "entreprise_code exist", "entreprise_code_exist": False})
            )
        

        company = request.env['res.company'].sudo().search([('entreprise_code', '=', entreprise_code ),('id','=',partner.company_id.id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ 'status': "success", "message": "entreprise_code exist", "entreprise_code_exist": False})
            )

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({ 'status': "success", "message": "Entreprise existe", "entreprise_code_exist": True})
        )


    
    @http.route('/api/companies/new_compte', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_companies_new_compte(self, **kw):
        data = json.loads(request.httprequest.data)
        if not data:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Données invalides")
            )

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        city = data.get('city')
        phone = data.get('phone')
        # company_id = data.get('company_id')

        # company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
        country = request.env['res.country'].sudo().search([('id', '=', 204)], limit=1)
        partner_email = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)

        if partner_email:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Utilisateur avec cet adresse mail existe déjà")
            )
        
        company_choice = None
      
        company_choice = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)


        if not partner_email :
            user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
            if not user or user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            partner = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email,
                'customer_rank': 1,
                'company_id': company_choice.id,
                'city': city,
                'phone': phone,
                'is_company': False,
                'active': True,
                'type': 'contact',
                'company_name': company_choice.name,
                'country_id': country.id or None,
                'password': password,
                'is_verified': False,
                'role' : 'secondary_user',
            })
            if partner:
                # self.send_verification_mail(partner.email)
                otp_code = partner.send_otp()

                return werkzeug.wrappers.Response(
                    status=201,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({
                        'id': partner.id,
                        'name': partner.name,
                        'email': partner.email,
                        'partner_id':partner.id,
                        'company_id': partner.company_id.id,
                        'company_name': partner.company_id.name,
                        'partner_city': partner.city,
                        'partner_phone': partner.phone,
                        'country_id': partner.country_id.id or None,
                        'country_name': partner.country_id.name or None,
                        'country_code': partner.country_id.code,
                        'country_phone_code': partner.country_id.phone_code,
                        'is_verified': partner.is_verified,
                        'avatar': partner.avatar or None,
                        'image_1920': partner.image_1920 or None,
                        'role': partner.role,
                    })
                    )

        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Compte client non créer, veuillez reessayer")
        )
    
    @http.route('/api/companies/clients/set_compte', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_companies_client_set_compte(self, **kw):
        data = json.loads(request.httprequest.data)

        company_id = data.get('company_id')
        client_id = data.get('client_id')
        role = data.get('role')

        if not company_id or not client_id:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Données invalides")
            )
        try:
            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            compagny = request.env['res.partner'].sudo().search([('id', '=', int(company_id))], limit=1)
            partner = request.env['res.partner'].sudo().search([('id', '=', int(client_id))], limit=1)

            if compagny and partner:

                partner.write({
                    'parent_id': compagny.id,
                    'adhesion': 'accepted',
                    'adhesion_submit': False,
                    'role': role,
                    'is_verified': True
                })
                # lui envoyé un message sms pour lui dire qu'il est le rh de la compagny
                if role == "main_user":
                    message = (
                        f"Bonjour ,\n"
                        f"Vous avez été assigné comme Responsable des Ressources Humaines de la société {compagny.name} .\n"
                        f"Merci de ne pas répondre à ce message.\n"
                        f"Equipe de CCBM Shop"
                    )
                else :
                    message = (
                        f"Bonjour ,\n"
                        f"Vous avez été ajouter comme employé de la société {compagny.name}.\n"
                        f"Merci de ne pas/respondre à ce message.\n"
                        f"Equipe de CCBM Shop"
                    )    
               
                sms_record = request.env['send.sms'].create({
                    'recipient': partner.phone,
                    'message': message,
                }).send_sms()
            
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps("Assignation effectuée avec succès !")
                )
        except Exception as e:
            _logger.error(f"Error while assigning client to company: {e}")
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps( f"Assignation non effectuée, veuillez reessayer :  {e}" )
            )
        


    @http.route('/api/companies/create-compte', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_companies_create_compte(self, **kw):
        data = json.loads(request.httprequest.data)
        if not data:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Données invalides")
            )

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        city = data.get('city')
        phone = data.get('phone')
        parent_id = data.get('parent_id')
        pass_claire = data.get('password')

        country = request.env['res.country'].sudo().search([('id', '=', 204)], limit=1)
        partner_email = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)

        if partner_email:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Utilisateur avec cet adresse mail existe déjà")
            )
        
        company_choice = request.env['res.partner'].sudo().search([('id', '=', int(parent_id))], limit=1)
        if not company_choice:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Société parent non trouvée")
            )


        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

     
        # passwordg = self.generate_password()
        password = self.hash_password(pass_claire)
    
        partner = request.env['res.partner'].sudo().create({
            'name': name,
            'email': email,
            'customer_rank': 1,
            'parent_id': company_choice.id,
            'city': city,
            'phone': phone,
            'is_company': False,
            'active': True,
            'type': 'contact',
            'company_name': company_choice.name,
            'country_id': country.id or None,
            'password': password,
            'is_verified': True,
            'role' : 'main_user',
            'adhedion': 'accepted'
        })
        if partner:
            # self.send_verification_mail(partner.email)
            # otp_code = partner.send_otp()
            message = "Bonjour {} , Votre compte RH a été créé avec succès sur CCBM Shop pour le compte de l'entreprise {}, \n\n Voici vos identifiants : \n Email : {} \n Mot de passe : {} \n Url de connexion : {}".format(partner.name, company_choice.name ,partner.email, pass_claire , 'https://grh.ccbme.sn?mail='+partner.email )
           
            request.env['send.sms'].create({
                    'recipient': phone,
                    'message': message,
            }).send_sms()
            
            partner.send_mail_create_account(partner, pass_claire, company_choice)

            return werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    'id': partner.id,
                    'name': partner.name,
                    'email': partner.email,
                    'partner_id':partner.id,
                    'company_id': partner.company_id.id,
                    'company_name': partner.company_id.name,
                    'partner_city': partner.city,
                    'partner_phone': partner.phone,
                    'country_id': partner.country_id.id or None,
                    'country_name': partner.country_id.name or None,
                    'country_code': partner.country_id.code,
                    'country_phone_code': partner.country_id.phone_code,
                    'is_verified': partner.is_verified,
                    'avatar': partner.avatar or None,
                    'image_1920': partner.image_1920 or None
                })
                )


        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Compte client non créer, veuillez reessayer")
        )
    
    @http.route('/api/companies/<id>/otp-resend', methods=['GET'], type='http', auth='none', cors="*")
    def api_companie_partner_resend_otp(self, id, **kw):

        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        
        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            
            return self._json_response("Compte client non trouvé", status=404)

        # Generate OTP code
        # otp_code = partner.get_otp()
        otp_code = partner.send_otp()
        return self._json_response("Code OTP envoyé avec succès", status=200)
      

    

    @http.route('/api/companies/otp-verification-compte', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_companie_partner_otp_verify(self, **kw):

        data = json.loads(request.httprequest.data)
        if not data:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Données invalides")
            )
        
        otp_code = data.get('otp_code')
        client_id = data.get('client_id')

        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('id', '=', client_id)], limit=1)
        if not partner:
            return self._json_response("Compte client non trouvé", status=404)

        # Verify OTP code
        if not partner.verify_otp(otp_code):
            return self._json_response("Code OTP invalide", status=400)
        else :
            partner.write({'is_verified': True})
            return self._json_response("Code OTP valide", status=200)

        

    def generate_password(self):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(8))

    def hash_password(self, password):
        # Remplace cette logique par celle utilisée dans ton projet (ex: bcrypt, passlib, etc.)
        from passlib.context import CryptContext

        # Créez un contexte de hachage similaire à celui d'Odoo
        pwd_context = CryptContext(schemes=["pbkdf2_sha512", "md5_crypt"], deprecated="md5_crypt")
        # Hache le mot de passe
        hashed_password = pwd_context.hash(password)
        return hashed_password
    

    def _json_response(self, message, status=200):
        return werkzeug.wrappers.Response(
            status=status,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({"message": message})
        )

    # update avatar
    @http.route('/api/companies/clients/compte/avatar/<int:id>', methods=['PUT'], type='http', auth='none', cors="*")
    def update_avatar_partner(self, id):
        data = json.loads(request.httprequest.data)
        avatar_url = data.get('avatar')

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': 'Utilisateur non trouvé pour l\'e-mail donné'})
            )

        if avatar_url and partner:
            partner.write({
               'avatar': avatar_url
            })
            user_data = {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'company_id': partner.company_id.id,
                'partner_id':partner.id,
                'company_id': partner.company_id.id,
                'company_name': partner.company_id.name,
                'partner_city':partner.city,
                'partner_phone':partner.phone,
                'country_id':partner.country_id.id,
                'country_name':partner.country_id.name,
                'country_code':partner.country_id.code,
                'country_phone_code':partner.country_id.phone_code,
                'is_verified' : partner.is_verified,
                'avatar': partner.avatar,
                'role': partner.role,
                'adhesion': partner.adhesion,
                'adhesion_submit' : partner.adhesion_submit,
                'function': partner.function or "",
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(user_data)
            )

    @http.route('/api/companies/new-password', methods=['POST'], type='http', auth='none', cors="*", csrf=False )
    def api_companies_new_password(self, **kw):
        data = json.loads(request.httprequest.data)
        if not data:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Données invalides")
            )

        email = data.get('email')
        password = data.get('password')

        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Utilisateur non trouvé")
            )

        partner.write({'password': self.hash_password(password)})

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Mot de passe mis à jour")
        )
