# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
# import json
import json
_logger = logging.getLogger(__name__)
from odoo.http import request, Response

class EntrepriseController(http.Controller):


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
    @http.route('/api/companies/clients/<int:id>', methods=['GET'], type='http', auth='none', cors="*")
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
        orders = request.env['sale.order'].sudo().search([('partner_id.id','=', id ) , ('type_sale' , '=' , 'order' )])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'type_sale':  o.type_sale,
                    'validation_state': o.validation_state,
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
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'order'), ('validation_state' , '=' , 'pending') ])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_state': o.validation_state,
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
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'order' ) , ('validation_state' , '=' , 'rejected') ])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_state': o.validation_state,
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
        orders = request.env['sale.order'].sudo().search([('company_id.id','=', company.id ) , ('type_sale' , '=' , 'order' ) , ('validation_state' , '=' , 'validated') ])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_state': o.validation_state,
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
                'validation_state': state
            })
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
                    'validation_state': o.validation_state,
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

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"}))
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id.id','=', partner.id )  ])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_state': o.validation_state,
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
