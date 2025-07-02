# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
# import json
import json
_logger = logging.getLogger(__name__)
from odoo.http import request, Response

class PaymentREST(http.Controller):


    @http.route('/api/facture/paydunya', methods=['POST'], type='http', auth='none', cors="*",  csrf=False)
    def api_get_data_send_by_paydunya(self,**kw):

        headers = request.httprequest.headers
        form_data = request.httprequest.form
        _logger.info(f"Form data: {form_data}")

        data_dict = {key: value for key, value in form_data.items()}

        # Informations sur la transaction
        status = data_dict['data[status]']
        token = data_dict['data[invoice][token]']

        receipt_url = data_dict['data[receipt_url]']

        response_code = data_dict['data[response_code]']
        response_text = data_dict['data[response_text]']
        # Informations sur le client
        customer_name = data_dict['data[customer][name]']
        customer_phone = data_dict['data[customer][phone]']
        customer_email = data_dict['data[customer][email]']
        total_amount = data_dict['data[invoice][total_amount]']
        
        # Affichage des informations extraites
        _logger.info(f'Status: {status}')
        _logger.info(f'Response Code: {response_code}')
        _logger.info(f'Response Text: {response_text}')
        _logger.info(f'Total Amount: {total_amount}')
        _logger.info(f'Customer Name: {customer_name}')
        _logger.info(f'Customer Phone: {customer_phone}')
        _logger.info(f'Customer Email: {customer_email}')
        
        

        content_type = headers.get('Content-Type', '')
        if 'application/x-www-form-urlencoded' in content_type and token and status:

            try:
                # Début de la transaction
                with request.env.cr.savepoint():
                    user = request.env['res.users'].sudo().browse(request.env.uid)
                    if not user or user._is_public():
                        admin_user = request.env.ref('base.user_admin')
                        request.env = request.env(user=admin_user.id)
                            
                    if response_code == "00" and status == "completed":
                        
                        payment_details = request.env['payment.details'].sudo().search([('payment_token', '=', token)], limit=1)
                        if payment_details and payment_details.token_status == False:
                            facture = f"https://paydunya.com/checkout/receipt/{token}"
                            url_facture = facture
                            payment_details.write({
                                'url_facture': url_facture,
                                'customer_email': customer_email,
                                'customer_phone': customer_phone,
                                'customer_name': customer_name,
                                'payment_state': "completed"
                            })
                            order = request.env['sale.order'].sudo().search([('id', '=',  payment_details.order_id )], limit=1)
                            if order:

                                partner = order.partner_id
                                company = partner.company_id

                                if order.type_sale == "order":
                                    journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
                                    payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
                                    payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)
                                    
                                    if order.advance_payment_status != 'paid':
                                        payment_details.write({'token_status': True})
                                        _logger.info(f'payment order : {status }')
                                        if order.payment_mode == "echelonne":
                                            return self._create_payment_and_confirm_order(order, payment_details.amount , partner, journal, payment_method, payment_method_line)
                                        else:
                                            return self._create_payment_and_confirm_order(order, order.amount_total , partner, journal, payment_method, payment_method_line)

                                    return self._make_response({'status': 'success'}, 200)

                                elif order.type_sale == "preorder":
                                    journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'),( 'company_id', '=', company.id ) ], limit=1)  # type = sale id= 1 & company_id = 1  ==> journal id = 1 / si journal id = 7 : CASH
                                    payment_method = request.env['account.payment.method'].sudo().search([ ( 'payment_type', '=',  'inbound' ) ], limit=1) # payement method : TYPE Inbound & id = 1
                                    payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)

                                    payment_details.write({'token_status': True})
                                    if order.amount_residual >  0:
                                        account_payment = request.env['account.payment'].sudo().create({
                                            'payment_type': 'inbound',
                                            'partner_type': 'customer',
                                            'partner_id': partner.id,
                                            'amount': total_amount,
                                            'journal_id': journal.id,
                                            'currency_id': partner.currency_id.id,
                                            'payment_method_line_id': 1,
                                            'payment_method_id': payment_method.id,
                                            'sale_id': order.id,
                                            'is_reconciled': True,
                                        })
                                        if order.state == "draft":
                                            order.action_confirm()
                                        if account_payment:
                                            account_payment.action_post()
                                            _logger.info(f'payment preorder : {status }')
                                        return self._make_response({'status': 'success'}, 200)
                                    return self._make_response({'status': 'success'}, 200)
                                else:
                                    return self._make_response({'status': 'success'}, 200)
                            else:
                                return self._make_response({'status': 'success'}, 200)
                        else:
                            return self._make_response({'status': 'success'}, 200)
                    else:
                        return self._make_response({'status': 'success', 'message': 'Payment failed'}, 200)
            
            except Exception as e:
                _logger.error(f"Error processing payment: {e}")
                return self._make_response({'status': 'success', 'message': 'Les informations sont invalides'}, 200)
            
        else:
            return self._make_response({'status': 'success', 'message': 'Invalid request'}, 200)


    
    # methode qu'on utilise
    @http.route('/api/precommande/<id>/payment/<amount>/<token>', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_create_payment_rang_preorder(self, id , amount , token):


        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        try:
            order = request.env['sale.order'].sudo().search([ ('id', '=', id) ], limit=1)
            partner = request.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)], limit=1)
            company = request.env['res.company'].sudo().search([('id', '=', partner.company_id.id)], limit=1)
            # payment_method = request.env['account.payment.method'].sudo().search([ ( 'payment_type', '=',  'inbound' ) ], limit=1)
            # journal = request.env['account.journal'].sudo().search([('company_id', '=', company.id),  ('type', '=', 'sale') ])
            # payment_method_line_vr = request.env['account.payment.method.line'].sudo().search([
            #         ('payment_method_id', '=', payment_method.id),( 'journal_id', '=', journal.id )], limit=1)

            journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'),( 'company_id', '=', company.id ) ], limit=1)  # type = sale id= 1 & company_id = 1  ==> journal id = 1 / si journal id = 7 : CASH
            
            # journal = request.env['account.journal'].sudo().search([('id', '=', 6 )] , limit=1) # type = sale id= 1 & company_id = 1  ==> journal id = 1 / si journal id = 7 : CASH
            payment_method = request.env['account.payment.method'].sudo().search([ ( 'payment_type', '=',  'inbound' ) ], limit=1) # payement method : TYPE Inbound & id = 1
            # payment_method_line_vr = request.env['account.payment.method.line'].sudo().search([ ('payment_method_id', '=', payment_method.id), ( 'journal_id', '=', journal.id ) ], limit=1)  # si journal est cash (id = 7)  et payment method inbound ==> payment method line id  = 1

            # user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
            # if not user or user._is_public():
            #     admin_user = request.env.ref('base.user_admin')
            #     request.env = request.env(user=admin_user.id)

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

                                    'first_payment_amount': order.first_payment_amount,
                                    'second_payment_amount': order.second_payment_amount,
                                    'third_payment_amount': order.third_payment_amount,

                                    'first_payment_state': order.first_payment_state,
                                    'second_payment_state': order.second_payment_state,
                                    'third_payment_state': order.third_payment_state,

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
        

    #methode pour enregistrer un payement
    @http.route('/api/payment/set',  methods= ['POST'] , type="http" , cors="*" , auth="none", csrf=False  )
    def set_payment_details(self, **kw):
        try:
            data = json.loads(request.httprequest.data)
            transaction_id = data.get('transaction_id')
            amount = data.get('amount')
            order_id = data.get('order_id')
            partner_id = data.get('partner_id')
            payment_token = data.get('payment_token')
            payment_state = data.get('payment_state')
            payment_date = datetime.datetime.now()

            if not all([transaction_id, amount, order_id,  partner_id]):
                return request.make_response(
                    json.dumps({"error": "Missing required fields"}),
                    status=400,
                    headers={'Content-Type': 'application/json'}
                )

            order = request.env['sale.order'].sudo().search([('id','=', order_id )], limit=1)
            if not order:
                return request.make_response(
                    json.dumps({"error": "Order not found"}),
                    status=404,
                    headers={'Content-Type': 'application/json'}
                )
             
            if order.type_sale == "order":
                payment_details_existe = request.env['payment.details'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
                if payment_details_existe:
                    payment_details_existe.write({
                        'amount': amount,
                        'payment_date': payment_date,
                        'payment_token': payment_token,
                        'payment_state': payment_state
                    })
                    return request.make_response(
                        json.dumps({
                            'id': payment_details_existe.id,
                            'transaction_id': payment_details_existe.transaction_id,
                            'amount': payment_details_existe.amount,
                            'currency': payment_details_existe.currency,
                            'payment_method': payment_details_existe.payment_method,
                            'payment_date': payment_details_existe.payment_date.isoformat(),
                            'order_id': payment_details_existe.order_id,
                            'order_name': payment_details_existe.order_name,
                            'type_sale' : order.type_sale,
                            'order_type': payment_details_existe.order_type,
                            'partner_id': payment_details_existe.partner_id,
                            'payment_token': payment_details_existe.payment_token,
                            'url_facture': payment_details_existe.url_facture,
                            'customer_name' : payment_details_existe.customer_name,
                            'customer_email' : payment_details_existe.customer_email,
                            'customer_phone' : payment_details_existe.customer_phone,
                            'payment_state': payment_details_existe.payment_state,
                            'token_status': payment_details_existe.token_status}),
                        status=200,
                        headers={'Content-Type': 'application/json'}
                    )
            if  order.type_sale == "preorder":
                payment_details_existe = request.env['payment.details'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
                if payment_details_existe:
                    if  payment_details_existe.payment_state == "completed":
                        minutes = payment_date.minute
                        new_transaction_id = payment_details_existe.transaction_id + '-' + str(minutes)

                        payment_details = request.env['payment.details'].sudo().set_payment_details(
                            transaction_id=new_transaction_id,
                            amount=amount,
                            payment_date=payment_date,
                            order_id=order_id,
                            order_name=order.name,
                            order_type=order.type_sale,
                            partner_id=partner_id,
                            payment_token=payment_token,
                            payment_state=payment_state
                        )
                        return request.make_response(
                            json.dumps({
                                    'id': payment_details.id,
                                    'transaction_id': payment_details.transaction_id,
                                    'amount': payment_details.amount,
                                    'currency': payment_details.currency,
                                    'payment_method': payment_details.payment_method,
                                    'payment_date': payment_details.payment_date.isoformat(),
                                    'order_id': payment_details.order_id,
                                    'order_name': payment_details.order_name,
                                    'order_type': payment_details.order_type,
                                    'partner_id': payment_details.partner_id,
                                    'payment_token': payment_details.payment_token,
                                    'url_facture': payment_details.url_facture,
                                    'customer_name' : payment_details.customer_name,
                                    'customer_email' : payment_details.customer_email,
                                    'customer_phone' : payment_details.customer_phone,
                                    'payment_state': payment_details.payment_state,
                                    'token_status': payment_details.token_status,}),
                            status=200,
                            headers={'Content-Type': 'application/json'}
                        )
                    else:
                        payment_details_existe.write({
                            'amount': amount,
                            'payment_date': payment_date,
                            'payment_token': payment_token,
                            'payment_state': payment_state
                        })    
                        return request.make_response(
                            json.dumps({
                                'id': payment_details_existe.id,
                                'transaction_id': payment_details_existe.transaction_id,
                                'amount': payment_details_existe.amount,
                                'currency': payment_details_existe.currency,
                                'payment_method': payment_details_existe.payment_method,
                                'payment_date': payment_details_existe.payment_date.isoformat(),
                                'order_id': payment_details_existe.order_id,
                                'order_name': payment_details_existe.order_name,
                                'order_type': payment_details_existe.order_type,
                                'type_sale' : order.type_sale,
                                'partner_id': payment_details_existe.partner_id,
                                'payment_token': payment_details_existe.payment_token,
                                'url_facture': payment_details_existe.url_facture,
                                'customer_name' : payment_details_existe.customer_name,
                                'customer_email' : payment_details_existe.customer_email,
                                'customer_phone' : payment_details_existe.customer_phone,
                                'payment_state': payment_details_existe.payment_state,
                                'token_status': payment_details_existe.token_status}),
                            status=200,
                            headers={'Content-Type': 'application/json'}
                        )
                    

            if order.type_sale == "creditorder":
                payment_details_existe = request.env['payment.details'].sudo().search([('transaction_id', '=', transaction_id)], limit=1)
                if payment_details_existe:
                    payment_details_existe.write({
                        'amount': amount,
                        'payment_date': payment_date,
                        'payment_token': payment_token,
                        'payment_state': payment_state
                    })
                    return request.make_response(
                        json.dumps({
                            'id': payment_details_existe.id,
                            'transaction_id': payment_details_existe.transaction_id,
                            'amount': payment_details_existe.amount,
                            'currency': payment_details_existe.currency,
                            'payment_method': payment_details_existe.payment_method,
                            'payment_date': payment_details_existe.payment_date.isoformat(),
                            'order_id': payment_details_existe.order_id,
                            'order_name': payment_details_existe.order_name,
                            'order_type': payment_details_existe.order_type,
                            'type_sale' : order.type_sale,
                            'partner_id': payment_details_existe.partner_id.id,
                            'payment_token': payment_details_existe.payment_token,
                            'url_facture': payment_details_existe.url_facture,
                            'customer_name' : payment_details_existe.customer_name,
                            'customer_email' : payment_details_existe.customer_email,
                            'customer_phone' : payment_details_existe.customer_phone,
                            'payment_state': payment_details_existe.payment_state,
                            'token_status': payment_details_existe.token_status}),
                        status=200,
                        headers={'Content-Type': 'application/json'}
                    )

            payment_details = request.env['payment.details'].sudo().set_payment_details(
                transaction_id=transaction_id,
                amount=amount,
                payment_date=payment_date,
                order_id=order_id,
                order_name=order.name,
                order_type=order.type_sale,
                partner_id=partner_id,
                payment_token=payment_token,
                payment_state=payment_state
            )

            return request.make_response(
                json.dumps({
                        'id': payment_details.id,
                        'transaction_id': payment_details.transaction_id,
                        'amount': payment_details.amount,
                        'currency': payment_details.currency,
                        'payment_method': payment_details.payment_method,
                        'payment_date': payment_details.payment_date.isoformat(),
                        'order_id': payment_details.order_id,
                        'order_name': payment_details.order_name,
                        'order_type': payment_details.order_type,
                        'type_sale' : order.type_sale,
                        'partner_id': payment_details.partner_id,
                        'payment_token': payment_details.payment_token,
                        'url_facture': payment_details.url_facture,
                        'customer_name' : payment_details.customer_name,
                        'customer_email' : payment_details.customer_email,
                        'customer_phone' : payment_details.customer_phone,
                        'payment_state': payment_details.payment_state,
                        'token_status': payment_details.token_status}),
                status=200,
                headers={'Content-Type': 'application/json'}
            )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=500,
                headers={'Content-Type': 'application/json'}
            )

    # get payment details
    @http.route('/api/payment/get/<transaction>', methods=['GET'], type='http', auth='none', cors='*')
    def get_payment_details(self, transaction, **kw):
        try:
            # payment_details = request.env['payment.details'].sudo().get_payment_details(transaction)
            payment_details = request.env['payment.details'].sudo().search([('transaction_id', '=', transaction)], limit=1)
            if payment_details:
                return request.make_response(
                    json.dumps({
                        'id': payment_details.id,
                        'transaction_id': payment_details.transaction_id,
                        'amount': payment_details.amount,
                        'currency': payment_details.currency,
                        'payment_method': payment_details.payment_method,
                        'payment_date': payment_details.payment_date.isoformat(),
                        'order_id': payment_details.order_id,
                        'order_name': payment_details.order_name,
                        'order_type': payment_details.order_type,
                        'partner_id': payment_details.partner_id.id,
                        'partner_name': payment_details.partner_id.name,
                        'payment_token': payment_details.payment_token,
                        'payment_state': payment_details.payment_state,
                        'url_facture': payment_details.url_facture,
                        'customer_name' : payment_details.customer_name,
                        'customer_email' : payment_details.customer_email,
                        'customer_phone' : payment_details.customer_phone,
                        'token_status': payment_details.token_status
                    }),
                    status=200,
                    headers={'Content-Type': 'application/json'}
                )
            else:
                return request.make_response(
                    json.dumps({"error": "Payment details not found"}),
                    status=404,
                    headers={'Content-Type': 'application/json'}
                )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=500,
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/api/payment/partner/<id>', methods=['GET'], type='http', auth='none', cors='*')
    def get_payment_partner(self, id, **kw):
        try:
            payment_details = request.env['payment.details'].sudo().get_payment_partner(id)
            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(payment_details)
            )
            return resp

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=400,
                headers={'Content-Type': 'application/json'}
            )


    @http.route('/api/payment/byId/<id>', methods=['GET'], type='http', auth='none', cors='*')
    def get_payment_by_id(self, id, **kw):
        try:
            payment_details = request.env['payment.details'].sudo().search([('id', '=', id)], limit=1)
            return request.make_response(
                    json.dumps({
                        'id': payment_details.id,
                        'transaction_id': payment_details.transaction_id,
                        'amount': payment_details.amount,
                        'currency': payment_details.currency,
                        'payment_method': payment_details.payment_method,
                        'payment_date':  payment_details.payment_date.isoformat() if payment_details.payment_date else None,
                        'order_id': payment_details.order_id,
                        'order_name': payment_details.order_name,
                        'order_type': payment_details.order_type,
                        'partner_id': payment_details.partner_id,
                        'payment_token': payment_details.payment_token,
                        'payment_state': payment_details.payment_state,
                        'url_facture': payment_details.url_facture,
                        'customer_name' : payment_details.customer_name,
                        'customer_email' : payment_details.customer_email,
                        'customer_phone' : payment_details.customer_phone,
                        'token_status': payment_details.token_status
                    }),
                    status=200,
                    headers={'Content-Type': 'application/json'}
                )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=400,
                headers={'Content-Type': 'application/json'}
            )


    @http.route('/api/payment/byOrder/<order_id>', methods=['GET'], type='http', auth='none', cors='*')
    def get_payment_by_name_order(self, order_id, **kw):
        try:
            order = request.env['sale.order'].sudo().search([('id','=', order_id )], limit=1)
            if not order:
                return request.make_response(
                    json.dumps({"error": "Order not found"}),
                    status=404,
                    headers={'Content-Type': 'application/json'}
                )
            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)
            if order:
                if order.type_sale == "preorder":
                    payment_details = request.env['payment.details'].sudo().search([('order_id', '=', order_id),( 'payment_state', '=', 'completed' )])
                    resultat = []
                    for payment in payment_details:
                        resultat.append({
                            'id': payment.id,
                            'transaction_id': payment.transaction_id,
                            'amount': payment.amount,
                            'currency': payment.currency,
                            'payment_method': payment.payment_method,
                            'payment_date':  payment.payment_date.isoformat() if payment.payment_date else None,
                            'order_id': payment.order_id,
                            'order_name': payment.order_name,
                            'order_type': payment.order_type,
                            'partner_id': payment.partner_id,
                            'payment_token': payment.payment_token,
                            'payment_state': payment.payment_state,
                            'url_facture': payment.url_facture,
                            'customer_name' : payment.customer_name,
                            'customer_email' : payment.customer_email,
                            'customer_phone' : payment.customer_phone,
                            'token_status': payment.token_status
                        })
                    return request.make_response(
                        json.dumps(resultat),
                        status=200,
                        headers={'Content-Type': 'application/json'}
                    )
                else:
                    payment_details = request.env['payment.details'].sudo().search([('order_id', '=', order_id)], limit=1)
                    return request.make_response(
                            json.dumps({
                                'id': payment_details.id,
                                'transaction_id': payment_details.transaction_id,
                                'amount': payment_details.amount,
                                'currency': payment_details.currency,
                                'payment_method': payment_details.payment_method,
                                'payment_date':  payment_details.payment_date.isoformat() if payment_details.payment_date else None,
                                'order_id': payment_details.order_id,
                                'order_name': payment_details.order_name,
                                'order_type': payment_details.order_type,
                                'partner_id': payment_details.partner_id,
                                'payment_token': payment_details.payment_token,
                                'payment_state': payment_details.payment_state,
                                'url_facture': payment_details.url_facture,
                                'customer_name' : payment_details.customer_name,
                                'customer_email' : payment_details.customer_email,
                                'customer_phone' : payment_details.customer_phone,
                                'token_status': payment_details.token_status
                            }),
                            status=200,
                            headers={'Content-Type': 'application/json'}
                        )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=400,
                headers={'Content-Type': 'application/json'}
            )
        

    @http.route('/api/payment/byToken/<token>', methods=['GET'], type='http', auth='none', cors='*')
    def get_payment_by_token(self, token, **kw):
        try:
            payment_details = request.env['payment.details'].sudo().search([('payment_token', '=', token)], limit=1)
            if not payment_details:
                return request.make_response(
                    json.dumps({"error": "Payment details not found"}),
                    status=404,
                    headers={'Content-Type': 'application/json'}
                )
            else:
                return request.make_response(
                        json.dumps({
                            'id': payment_details.id,
                            'transaction_id': payment_details.transaction_id,
                            'amount': payment_details.amount,
                            'currency': payment_details.currency,
                            'payment_method': payment_details.payment_method,
                            'payment_date':  payment_details.payment_date.isoformat() if payment_details.payment_date else None,
                            'order_id': payment_details.order_id,
                            'order_name': payment_details.order_name,
                            'order_type': payment_details.order_type,
                            'partner_id': payment_details.partner_id,
                            'payment_token': payment_details.payment_token,
                            'payment_state': payment_details.payment_state,
                            'url_facture': payment_details.url_facture,
                            'customer_name' : payment_details.customer_name,
                            'customer_email' : payment_details.customer_email,
                            'customer_phone' : payment_details.customer_phone,
                            'token_status': payment_details.token_status
                        }),
                        status=200,
                        headers={'Content-Type': 'application/json'}
                    )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=400,
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/api/payment/update/<id>', methods=['PUT'], type='http', auth='none', cors='*' ,csrf=False)
    def update_payment_by_id(self, id, **kw):

        try:
            data = json.loads(request.httprequest.data)
            payment_state = data.get('payment_state')
            url_facture = data.get('url_facture')
            customer_name  = data.get('customer_name') , 
            customer_email = data.get('customer_email'),
            customer_phone = data.get('customer_phone'),
            token_status = data.get('token_status')
            payment_date = datetime.datetime.now()


            payment_details = request.env['payment.details'].sudo().search([('id', '=', id)], limit=1)

            if not payment_details:
                return request.make_response(
                    json.dumps({"error": "Payment details not found"}),
                    status=404,
                    headers={'Content-Type': 'application/json'}
                )
            else:
            
                if payment_details.payment_state == "completed":
                    return request.make_response(
                    json.dumps({
                            'id': payment_details.id,
                            'transaction_id': payment_details.transaction_id,
                            'amount': payment_details.amount,
                            'currency': payment_details.currency,
                            'payment_method': payment_details.payment_method,
                            'payment_date':  payment_details.payment_date.isoformat() if payment_details.payment_date else None,
                            'order_id': payment_details.order_id,
                            'order_name': payment_details.order_name,
                            'order_type': payment_details.order_type,
                            'partner_id': payment_details.partner_id,
                            'payment_token': payment_details.payment_token,
                            'payment_state': payment_details.payment_state,
                            'url_facture': payment_details.url_facture,
                            'customer_name' : payment_details.customer_name,
                            'customer_email' : payment_details.customer_email,
                            'customer_phone' : payment_details.customer_phone,
                            'token_status': payment_details.token_status
                        }),
                        status=200,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                #  si payment details existe et payment_state est different de completed

                # Mettre à jour les champs avec les nouvelles valeurs
                payment_details.write({
                    'payment_state': payment_state,
                    'payment_date': payment_date,
                    'url_facture': url_facture,
                    'customer_name' : customer_name,
                    'customer_email' : customer_email,
                    'customer_phone' : customer_phone,
                    # 'token_status': True
                })

                return request.make_response(
                    json.dumps({
                            'id': payment_details.id,
                            'transaction_id': payment_details.transaction_id,
                            'amount': payment_details.amount,
                            'currency': payment_details.currency,
                            'payment_method': payment_details.payment_method,
                            'payment_date':  payment_details.payment_date.isoformat() if payment_details.payment_date else None,
                            'order_id': payment_details.order_id,
                            'order_name': payment_details.order_name,
                            'order_type': payment_details.order_type,
                            'partner_id': payment_details.partner_id,
                            'payment_token': payment_details.payment_token,
                            'payment_state': payment_details.payment_state,
                            'url_facture': payment_details.url_facture,
                            'customer_name' : payment_details.customer_name,
                            'customer_email' : payment_details.customer_email,
                            'customer_phone' : payment_details.customer_phone,
                            'token_status': payment_details.token_status
                        }),
                        status=200,
                        headers={'Content-Type': 'application/json'}
                    )

        except Exception as e:
            return request.make_response(
                json.dumps({"error": str(e)}),
                status=400,
                headers={'Content-Type': 'application/json'}
            )
        

    # autre fonction 
    @http.route('/api/commande/<int:id>/payment', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_create_payment_orderp(self, id):

        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        try:
            order = request.env['sale.order'].sudo().browse(id)
            if not order:
                return self._make_response({'error': 'Commande non trouvé'}, 404)

            partner = order.partner_id
            company = partner.company_id

            _logger.info(f'Partner: {partner.email}, Company: {company.name}')

            journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
            payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
            payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)

            _logger.info(f'Journal: {journal.id}')

            payment_details = request.env['payment.details'].search([('order_id', '=', order.id)], limit=1)
            _logger.info(f'payment : {payment_details.payment_state, payment_details.token_status }')
            if payment_details and payment_details.token_status == False and payment_details.payment_state == "completed":
                payment_details.write({'token_status': True})
                if order.advance_payment_status == 'paid':
                    return self._make_response(self._order_to_dict(order), 200)
                else:
                    if order.payment_mode =="echelonne":
                        return self._create_payment_and_confirm_order(order, payment_details.amount, partner, journal, payment_method, payment_method_line)
                    else:
                        return self._create_payment_and_confirm_order(order, order.amount_total, partner, journal, payment_method, payment_method_line)

            elif payment_details and payment_details.token_status == True:
                return self._make_response({'message': 'Payment deja valide'}, 200)

            else:
                return self._make_response({'message': 'Payment non valide'}, 200)

        except ValueError as e:
            return self._make_response({'status': 'error', 'message': str(e)}, 400)

    def _create_payment_and_confirm_order(self, order, amount ,partner, journal, payment_method, payment_method_line):
        account_payment = request.env['account.payment'].sudo().create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': partner.id,
            'amount': amount,
            'journal_id': journal.id,
            'currency_id': journal.currency_id.id,
            'payment_method_line_id': payment_method_line.id,
            'payment_method_id': payment_method.id,
            'sale_id': order.id,
        })
        account_payment.action_post()
        order.action_confirm()
        return self._make_response(self._order_to_dict(order), 200)


    def _order_to_dict(self, order):
        return {
            'id': order.id,
            'type_sale': order.type_sale,
            'name': order.name,
            'partner_id': order.partner_id.id,
            'type_sale': order.type_sale,
            'currency_id': order.currency_id.id,
            'company_id': order.company_id.id,
            'state': order.state,
            'amount_total': order.amount_total,
            'invoice_status': order.invoice_status,
            'amount_total': order.amount_total,
            'advance_payment_status': order.advance_payment_status
        }

    def _make_response(self, data, status):
        return request.make_response(
            json.dumps(data),
            status=status,
            headers={'Content-Type': 'application/json'}
        )

       
    @http.route('/api/payment/verify/<token>', methods=['PUT'], type='http', auth='none', cors="*", csrf=False)
    def api_get_paydunya_by_token(self, token, **kw):
        try:
            data = json.loads(request.httprequest.data)
            url_facture = data.get('url_facture')
            customer_name = data.get('customer_name')
            customer_email = data.get('customer_email')
            customer_phone = data.get('customer_phone')
            token_status = data.get('token_status')
            payment_date = datetime.datetime.now()
            payment_state = data.get('payment_state')

            user = request.env['res.users'].sudo().browse(request.env.uid)
            if not user or user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            payment_details = request.env['payment.details'].sudo().search([('payment_token', '=', token)], limit=1)
            if not payment_details:
                return self._make_response({'message': 'Paiement non trouvé'}, 400)

            total_amount = payment_details.amount
            order_id = payment_details.order_id
            order = request.env['sale.order'].sudo().browse(order_id)
            if not order:
                return self._make_response({'message': 'Commande non trouvée'}, 400)

            partner = order.partner_id
            company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)

            if payment_details.token_status == False and payment_state == "completed":
                facture = f"https://paydunya.com/checkout/receipt/{token}"
                url_facture = facture

                if order.type_sale == "order":
                    journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
                    payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
                    payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)

                    if order.advance_payment_status == 'paid':
                        return self._make_response(self._order_to_dict(order), 200)

                    payment = request.env['account.payment'].sudo().create({
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'partner_id': partner.id,
                        'amount': total_amount,
                        'journal_id': journal.id,
                        'currency_id': partner.currency_id.id,
                        'payment_method_line_id': payment_method_line.id,
                        'payment_method_id': payment_method.id,
                        'ref': order.name,
                        'destination_account_id': partner.property_account_receivable_id.id,
                    })
                    payment.action_post()
                  

                    payment_details.write({
                        'token_status': True,
                        'url_facture': url_facture,
                        'customer_name': customer_name,
                        'customer_email': customer_email,
                        'customer_phone': customer_phone,
                        'payment_date': payment_date,
                        'payment_state': "completed"
                    })

                    if order.payment_mode == "echelonne":
                        return self._create_payment_and_confirm_order(order, payment_details.amount, partner, journal, payment_method, payment_method_line)
                    else:
                        return self._create_payment_and_confirm_order(order, order.amount_total, partner, journal, payment_method, payment_method_line)

                elif order.type_sale == "preorder":
                    journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
                    payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
                    payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)

                    if order.amount_residual > 0:
                        account_payment = request.env['account.payment'].sudo().create({
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_id': partner.id,
                            'amount': total_amount,
                            'journal_id': journal.id,
                            'currency_id': partner.currency_id.id,
                            'payment_method_line_id': payment_method_line.id,
                            'payment_method_id': payment_method.id,
                            'sale_id': order.id,
                            'is_reconciled': True,
                        })
                        if order.state == "draft":
                            order.action_confirm()

                        payment_details.write({
                            'token_status': True,
                            'url_facture': url_facture,
                            'customer_name': customer_name,
                            'customer_email': customer_email,
                            'customer_phone': customer_phone,
                            'payment_date': payment_date,
                            'payment_state': "completed"
                        })
                        if account_payment:
                            account_payment.action_post()
                            return self._make_response(self._order_to_dict(order), 200)
                    else:
                        return self._make_response(self._order_to_dict(order), 200)

                elif order.type_sale == "creditorder":
                    journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
                    payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
                    payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)

                    if order.amount_residual > 0:
                        order.write({
                            'state': "sale"
                        })
                        payment = request.env['account.payment'].sudo().create({
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'partner_id': partner.id,
                            'amount': total_amount,
                            'journal_id': journal.id,
                            'currency_id': partner.currency_id.id,
                            'payment_method_line_id': payment_method_line.id,
                            'payment_method_id': payment_method.id,
                            'ref': order.name,
                            'sale_id': order.id,
                            'is_reconciled': True,
                            'destination_account_id': partner.property_account_receivable_id.id,
                        })
                       
                        payment.action_post()
                        payment_details.write({
                            'token_status': True,
                            'url_facture': url_facture,
                            'customer_name': customer_name,
                            'customer_email': customer_email,
                            'customer_phone': customer_phone,
                            'payment_date': payment_date,
                            'payment_state': "completed"
                        })

                        return self._make_response(self._order_to_dict(order), 200)
                    else:
                        return self._make_response(self._order_to_dict(order), 200)

                else:
                    return self._make_response(self._order_to_dict(order), 200)

            elif payment_details.token_status == True and payment_details.payment_state == "completed":
                return self._make_response(self._order_to_dict(order), 200)

            else:
                return self._make_response({'message': 'Paiement non valide'}, 400)

        except Exception as e:
            return self._make_response({'message': str(e)}, 400)



    # @http.route('/api/payment/create-invoice-afterPaided/<string:token>', methods=['PUT'], type='http', cors="*", auth='none', csrf=False)
    # def api_create_invoice_afterPaided(self, token):
         
    #     try:
    #         request.env.cr.execute('SAVEPOINT ENREGISTREMENT PAIEMENT ET CREATION FACTURE')

    #         payment_details = request.env['payment.details'].sudo().search([('payment_token', '=', token)], limit=1)
    #         if not payment_details:
    #             return self._make_response({'message': 'Paiement non trouvé'}, 400)
            
    #         payment_date = datetime.datetime.now()

    #         total_amount = payment_details.amount
    #         order_id = payment_details.order_id
    #         order = request.env['sale.order'].sudo().browse(order_id)
    #         if not order:
    #             return self._make_response({'message': 'Commande non trouvée'}, 400)

    #         partner = order.partner_id
    #         company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
    #         if order.type_sale == "order":
    #             journal = request.env['account.journal'].sudo().search([('code', '=', 'CSH1'), ('company_id', '=', company.id)], limit=1)
    #             payment_method = request.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound')], limit=1)
    #             payment_method_line = request.env['account.payment.method.line'].sudo().search([('payment_method_id', '=', payment_method.id), ('journal_id', '=', journal.id)], limit=1)

    #             invoice_lines = []
    #             for line in order.order_line:
    #                 invoice_lines.append((0, 0, {
    #                     'name': line.name,
    #                     'quantity': line.product_uom_qty,
    #                     'price_unit': line.price_unit,
    #                     'product_id': line.product_id.id,
    #                     'tax_ids': [(6, 0, line.tax_id.ids)],
    #                 }))

    #             invoice = request.env['account.move'].sudo().create({
    #                 'partner_id': partner.id,
    #                 'move_type': 'out_invoice',
    #                 'invoice_date': payment_date,
    #                 'invoice_date_due': payment_date,
    #                 'currency_id': partner.currency_id.id or order.currency_id.id or journal.currency_id.id,
    #                 'journal_id': journal.id,
    #                 'invoice_line_ids': invoice_lines,
    #             })

    #             invoice.action_post()
    #             if invoice:
    #                 payment = request.env['account.payment'].sudo().create({
    #                     'payment_type': 'inbound',
    #                     'partner_type': 'customer',
    #                     'partner_id': partner.id,
    #                     'amount': total_amount,
    #                     'journal_id': journal.id,
    #                     'currency_id': partner.currency_id.id or order.currency_id.id or journal.currency_id.id,
    #                     'payment_method_line_id': payment_method_line.id,
    #                     'payment_method_id': payment_method.id,
    #                     'ref': order.name,
    #                     'destination_account_id': partner.property_account_receivable_id.id,
    #                 })
    #                 # Reconcile the payment with the invoice
    #                 if payment:
    #                     payment.action_post()
    #                     invoice.js_assign_outstanding_line(payment.line_ids[0].id)
    #                     return self._make_response(self._order_to_dict(order), 200)
    #                 else:
    #                     return self._make_response({'message': 'Paiement non validé'}, 400)
    #             else :
    #                 return self._make_response({'message': 'Facture non comptablisée'}, 400)
    #         else:
    #             return self._make_response({'message': 'Commande non trouvée'}, 400)

            
    #     except Exception as e:
    #         return self._make_response({'message': str(e)}, 400)