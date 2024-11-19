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
        
        partner.write({
            'parent_id': parent_partner.id,
            'adhesion': 'pending' ,
            'adhesion_submit': True
        })
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
            'adhesion_submit' : partner.adhesion_submit
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

        companies = request.env['res.company'].sudo().search([])

        resultats = []

        for company in companies:
            resultats.append({
                'id': company.id,
                'name': company.name,
                'email': company.email,
                'phone': company.phone
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
    @http.route('/api/companies/clients/<int:id>/liste', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_company(self, id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Entreprise non rencontrée"}))
        
        partners = request.env['res.partner'].sudo().search([('company_id', '=', company.id)])
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
                'adhesion_submit': partner.adhesion_submit
                
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

    # getCommande en cours de validation Clients Entreprise api/companies/clients/commandesECDV/${id}
    @http.route('/api/companies/clients/commandesECDV/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commande_en_cours_de_validation(self,id, **kw):
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
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'creditorder'), ('validation_rh_state' , '=' , 'pending') ])
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

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'creditorder' ) , ('validation_rh_state' , '=' , 'rejected') ])
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

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'creditorder' ) , ('validation_rh_state' , '=' , 'validated') ])
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
            res = order.action_validation_rh_state()
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

        company = request.env['res.company'].sudo().search([('id', '=', id)], limit=1)
        if not company:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('company_id','=', company.id ) , ('type_sale' , '=' , 'creditorder')  ])
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
        company_id = data.get('company_id')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        order = request.env['sale.order'].sudo().search([('id', '=', order_id),('company_id', '=', company_id)], limit=1)
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

            'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
            'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
            'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,
            'fourth_payment_date': order.fourth_payment_date.isoformat() if order.fourth_payment_date else None,

            'first_payment_amount': order.first_payment_amount,
            'second_payment_amount': order.second_payment_amount,
            'third_payment_amount': order.third_payment_amount,
            'fourth_payment_amount': order.fourth_payment_amount,

            'first_payment_state': order.first_payment_state,
            'second_payment_state': order.second_payment_state,
            'third_payment_state': order.third_payment_state,
            'fourth_payment_state': order.fourth_payment_state,
            
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
            'title': client.title or None,
            'adhesion': client.adhesion or None
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
            partner.write({
                'adhesion': state
            })
            res = partner.action_confirm_demande_adhesion()
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
            response=json.dumps({ 'status': "success", "message": "entreprise_code exist", "entreprise_code_exist": True})
        )
        
        




    