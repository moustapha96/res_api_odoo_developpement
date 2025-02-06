# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)


class CreditCommandeREST(http.Controller):

    @http.route('/api/creditcommandes/details', methods=['POST'], type='http', auth='none', cors="*",  csrf=False)
    def api_get_credit_order_details(self, **kw):
        data = json.loads(request.httprequest.data)
        partner_id = int(data.get('partner_id'))
        order_id = int(data.get('order_id'))

        if not partner_id or not order_id:
            return request.make_response(
                json.dumps({'status': 'erreur', 'message': 'Données de commande invalides'}),
                headers={'Content-Type': 'application/json'}
            )
        
        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
        o = request.env['sale.order'].sudo().search([('id', '=', order_id),( 'partner_id', '=', partner_id ),( 'type_sale' , '=' , 'creditorder' )  ], limit=1)
        
        if partner and o:

            data = {
                        'id': o.id,
                        'type_sale':  o.type_sale,
                        'date_order': o.date_order.isoformat() if o.date_order else None,
                        'validation_rh_state': o.validation_rh_state,
                        'validation_admin_state': o.validation_admin_state,
                        'commitment_date': o.commitment_date.isoformat() if o.commitment_date else None,
                        'name': o.name,
                        'partner_id': o.partner_id.id or None,
                        'partner_name': o.partner_id.name or None,
                        'partner_street': o.partner_id.street or None,
                        'partner_street2': o.partner_id.street2 or None,
                        'partner_city': o.partner_id.city or None,
                        'partner_state_id': o.partner_id.state_id.id or None,
                        'partner_state_name': o.partner_id.state_id.name or None,
                        'partner_zip': o.partner_id.zip or None,
                        'partner_country_id': o.partner_id.country_id.id or None,
                        'partner_country_name': o.partner_id.country_id.name or None,
                        'partner_vat': o.partner_id.vat or None,
                        'partner_email': o.partner_id.email or None,
                        'partner_phone': o.partner_id.phone or None,
                        'amount_untaxed': o.amount_untaxed or None,
                        'amount_tax': o.amount_tax or None,
                        'amount_total': o.amount_total or None,
                        'amount_residual': o.amount_residual,
                        'state': o.state or None,
                        'create_date': o.create_date.isoformat() if o.create_date else None,
                        'payment_line_ids': o.payment_term_id or None,

                        'first_payment_date': o.first_payment_date.isoformat() if o.first_payment_date else None,
                        'second_payment_date': o.second_payment_date.isoformat() if o.second_payment_date else None,
                        'third_payment_date': o.third_payment_date.isoformat() if o.third_payment_date else None,

                        'first_payment_amount': o.first_payment_amount,
                        'second_payment_amount': o.second_payment_amount,
                        'third_payment_amount': o.third_payment_amount,

                        'first_payment_state': o.first_payment_state,
                        'second_payment_state': o.second_payment_state,
                        'third_payment_state': o.third_payment_state,

                        'fourth_payment_amount': o.fourth_payment_amount,
                        'fourth_payment_date': o.fourth_payment_date.isoformat() if o.fourth_payment_date else None,
                        'fourth_payment_state': o.fourth_payment_state,
                        
                        'advance_payment_status':o.advance_payment_status,
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
                            'qty_invoiced': l.qty_invoiced or None,
                            'is_downpayment' : l.is_downpayment or None,
                    } for l in o.order_line if not l.is_downpayment]
            }
                    

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(data)
            )
            return resp
            
            
        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Client et commande invalide")
        )
    
    @http.route('/api/creditcommandes', methods=['POST'], type='http', auth='none', cors="*" , csrf=False)
    def api_create_credit_order(self, **kw):
        data = json.loads(request.httprequest.data)
        partner_id = int(data.get('partner_id'))
        order_lines = data.get('order_lines')
        type_sale = data.get('type_sale')
        payment_mode = data.get('payment_mode')
        state = data.get('state')
        commitment_date = data.get('commitment_date')
        parent_id = data.get('parent_id')

        if not partner_id or not order_lines:
            raise ValueError('Invalid données commande crédit')
        
        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
        partner_parent = request.env['res.partner'].sudo().search([('id', '=', parent_id)], limit=1)

       

        if not partner_parent or (partner_parent.id != partner.parent_id.id):
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Vous n'etes pas autoriser à faire des commandes à crédit"))


        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        # company = request.env['res.company'].sudo().search([('id', '=', company_id)], limit=1)
        previous_orders = request.env['sale.order'].sudo().search_count([('partner_id', '=', partner_id)])
        is_first_order = previous_orders == 0
        
        company = request.env['res.company'].sudo().search([('id', '=', 1 )], limit=1)
        if  company and partner and partner.adhesion == "accepted" :
            # Création de commande
            order = request.env['sale.order'].sudo().create({
                'state': "draft",
                'partner_id': partner_id,
                'type_sale': 'creditorder',
                'company_id': company.id,
                'currency_id': company.currency_id.id,
                'company_id': company.id,
                'commitment_date': datetime.datetime.now() + datetime.timedelta(days=3),
                'payment_mode': 'online',
                'validation_rh_state': 'pending',
                'validation_admin_state': 'pending',
                'date_approved_creditorder': datetime.datetime.now()
            })
            _logger.info("Commande créee avec successe: %s", order.name)
            for item in order_lines:

                product_id = item.get('id')
                product_uom_qty = item.get('quantity')
                price_unit = item.get('list_price')
                
                if not product_id or not product_uom_qty or not price_unit:
                    raise ValueError('Missing product data')
                

                 # je recuperer le produit a travers son id
                le_produit = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
                if not le_produit:
                    return request.make_response(
                        json.dumps({'status': 'error', 'message': 'Product not found'}),
                        headers={'Content-Type': 'application/json'}
                    )

                if is_first_order and not le_produit.product_tmpl_id.en_promo:
                    price_unit *= 0.97  # Réduction de 3 %
                

                order_line = request.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'product_id': product_id,
                    'product_uom_qty': product_uom_qty,
                    'price_unit': price_unit,
                    'company_id': company.id,
                    'currency_id': company.currency_id.id,
                    'state': 'sale',
                    'invoice_status': 'to invoice'
                })
                _logger.info("Ligne de commande ajoutée avec successe: %s", order_line.name)
            if order:
                order.send_credit_order_validation_mail()
                order.send_credit_order_to_rh_for_confirmation()
                order.state = "validation"
                _logger.info("Commande validée : %s", order.state)

                resp = werkzeug.wrappers.Response(
                    status=201,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({
                        'id': order.id,
                        'name': order.name,
                        'partner_id': order.partner_id.id,
                        'type_sale': order.type_sale,
                        'validation_rh_state': order.validation_rh_state,
                        'validation_admin_state': order.validation_admin_state,
                        'currency_id': order.currency_id.id,
                        'company_id': order.company_id.id,
                        'commitment_date': order.commitment_date.isoformat(),
                        'state': order.state,
                        'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
                        'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
                        'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,

                        'fourth_payment_amount': order.fourth_payment_amount,
                        'fourth_payment_date': order.fourth_payment_date.isoformat() if order.fourth_payment_date else None,
                        'fourth_payment_state': order.fourth_payment_state,

                        'first_payment_amount': order.first_payment_amount,
                        'second_payment_amount': order.second_payment_amount,
                        'third_payment_amount': order.third_payment_amount,
                        'first_payment_state': order.first_payment_state,
                        'second_payment_state': order.second_payment_state,
                        'third_payment_state': order.third_payment_state,
                        'amount_residual': order.amount_residual,
                        'amount_total' : order.amount_total,
                        'amount_tax': order.amount_tax,
                        'amount_untaxed' : order.amount_untaxed,
                        'advance_payment_status':order.advance_payment_status,
                        'order_lines': [
                            {
                                'id': order_line.id,
                                'quantity': order_line.product_uom_qty,
                                'list_price': order_line.price_unit,
                            } for order_line in order.order_line
                        ]
                    })
                )
                return resp

            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Client et commande invalide")
            )
        else:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Vous n'etes pas autoriser à faire cette opération"))


    # methode qu'on utilise
    @http.route('/api/creditcommande/<id>/payment/<amount>/<token>', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_create_payment_rang_creditorder(self, id , amount , token):


        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        try:
            order = request.env['sale.order'].sudo().search([ ('id', '=', id) ], limit=1)
            partner = request.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)], limit=1)
            company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            
            journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'),( 'company_id', '=', company.id ) ], limit=1)  # type = sale id= 1 & company_id = 1  ==> journal id = 1 / si journal id = 7 : CASH
            
            # journal = request.env['account.journal'].sudo().search([('id', '=', 6 )] , limit=1) # type = sale id= 1 & company_id = 1  ==> journal id = 1 / si journal id = 7 : CASH
            payment_method = request.env['account.payment.method'].sudo().search([ ( 'payment_type', '=',  'inbound' ) ], limit=1) # payement method : TYPE Inbound & id = 1
            
            # enregistrement payment
            if order :

                payment_details = request.env['payment.details'].search([('order_id', '=', order.id), ('payment_token', '=', token) ], limit=1)

                if payment_details.token_status == False and payment_details.payment_state == "completed":
                    account_payment = request.env['account.payment'].sudo().create({
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'partner_id': partner.id,
                        'amount': amount,
                        'journal_id': journal.id,
                        'currency_id': partner.currency_id.id,
                        'payment_method_line_id': 1,
                        'payment_method_id': payment_method.id, # inbound
                        'sale_id': order.id,
                        'is_reconciled': True,
                        # 'move_id': new_invoice.id
                    })
                    if account_payment:
                        account_payment.action_post()
                        payment_details.write({'token_status': True})

                        return request.make_response(
                                json.dumps({
                                    'id': order.id,
                                    'name': order.name,
                                    'validation_rh_state': order.validation_rh_state,
                                    'validation_admin_state': order.validation_admin_state,
                                    'partner_id': order.partner_id.id,
                                    'type_sale': order.type_sale,
                                    'currency_id': order.currency_id.id,
                                    'company_id': order.company_id.id,
                                    'commitment_date': order.commitment_date.isoformat(),
                                    'state': order.state,
                                    'invoice_status': order.invoice_status,
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

                                    'invoice_id': account_payment.move_id.id or None ,
                                    'is_reconciled': account_payment.is_reconciled,
                                    'payment_id': account_payment.id,
                                    'payment_name': account_payment.name,
                                    'sale_order': account_payment.sale_id.id,
                                    'move_id': account_payment.move_id.id,
                                    'move_name': account_payment.move_id.name,
                                    'amount_untaxed': order.amount_untaxed or None,
                                    'amount_tax': order.amount_tax or None,
                                    'amount_total': order.amount_total or None,
                                    'amount_residual': order.amount_residual,
                                    
                                }),
                                headers={'Content-Type': 'application/json'}
                            )
                elif payment_details.token_status == True and payment_details.payment_state == "completed":
                    return self._make_response({'error': 'Payment déja valide'}, 400)
                else:
                    return self._make_response({'error': 'Payment non valide'}, 400)

            else:
                return request.make_response(
                            json.dumps({'erreur': 'précommande non trouvé' }),
                            headers={'Content-Type': 'application/json'}
                        )

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )


    @http.route('/api/creditcommandes/clients/<int:id>/liste', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandesCredit_liste(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"})
            )
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id','=', partner.id ) , ('type_sale' , '=' , 'creditorder')  ])
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


    # check if the partner has order type creditorder not paid total
    @http.route('/api/creditcommandes/clients/<int:id>/stateCommande', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandesCredit_existe(self,id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Client non rencontré"}))

        orders = request.env['sale.order'].sudo().search([('partner_id','=', partner.id ) , ('type_sale' , '=' , 'creditorder')  , ( 'amount_residual' , '>' , '0' ) ])
        if orders:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "code": 400, "message": "Vous avez des commandes à crédit non payées"})
            )
        else:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "code": 200, "message": "Vous n'avez aucune commande à crédit non payée"})
            )