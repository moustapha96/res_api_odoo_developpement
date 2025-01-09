# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)


class PreCommandeREST(http.Controller):

    @http.route('/api/precommandes/<id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_preorders_user_GET(self, id, **kw):

        if id:
            orders = request.env['sale.order'].sudo().search([ ('type_sale' , '=' , 'preorder' ) ,  ( 'partner_id.id', '=', id ) ])
            order_data = []
            if orders:
                for o in orders:
                    order_data.append({
                         'id': o.id,
                         'type_sale':  o.type_sale,
                         'date_order': o.date_order.isoformat() if o.date_order else None,
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
                         'user_id': o.partner_id.user_id.id or None,
                         'user_name': o.partner_id.user_id.name or None,
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
                         
                         'advance_payment_status':o.advance_payment_status,
                         'note': o.note or None,
                         'order_line': [{
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
                response=json.dumps("pas de données")
            )
        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("user_id est obligatoire")
        )

    @http.route('/api/precommandes/details', methods=['POST'], type='http', auth='none', cors="*" , csrf=False)
    def api_preorders__GET_ONE(self,  **kw):
        data = json.loads(request.httprequest.data)
        partner_id = int( data.get('partner_id'))
        precommande_id = int (data.get('precommande_id'))
        order = request.env['sale.order'].sudo().search([('id','=', precommande_id) , ('type_sale' , '=' , 'preorder' ) , ( 'partner_id', '=', partner_id )])

        payment = request.env['account.payment'].sudo().search([ ( 'sale_id', '=' , order.id ) ])
        # invoice = request.env['account.move'].sudo().search([ ( 'id', '=' , payment.move_id ) ])
       
        if not order:
            return werkzeug.wrappers.Response(
                status=404,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Précommande introuvable")
            )

        invoice_p = []
        if len (payment) > 0:
            for pp in payment:
                inv = request.env['account.move'].sudo().search([ ( 'id', '=' , pp.move_id.id ) ])
                invoice_p.append( inv )
        if order:
            order_data = {
                'id': order.id,
                'type_sale':  order.type_sale,
                'date_order': order.date_order.isoformat() if order.date_order else None,
                'name': order.name,
                'partner_id': order.partner_id.id or None,
                'partner_name': order.partner_id.name or None,
                'partner_street': order.partner_id.street or None,
                'partner_street2': order.partner_id.street2 or None,
                'partner_city': order.partner_id.city or None,
                'partner_state_id': order.partner_id.state_id.id or None,
                'partner_state_name': order.partner_id.state_id.name or None,
                'partner_zip': order.partner_id.zip or None,
                'partner_country_id': order.partner_id.country_id.id or None,
                'partner_country_name': order.partner_id.country_id.name or None,
                'partner_vat': order.partner_id.vat or None,
                'partner_email': order.partner_id.email or None,
                'partner_phone': order.partner_id.phone or None,
                'amount_untaxed': order.amount_untaxed or None,
                'amount_tax': order.amount_tax or None,
                'amount_total': order.amount_total or None,
                'company_id': order.company_id.id,
                'commitment_date': order.commitment_date.isoformat(),
                'state': order.state,
                'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
                'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
                'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,

                'first_payment_amount': order.first_payment_amount,
                'second_payment_amount': order.second_payment_amount,
                'third_payment_amount': order.third_payment_amount,

                'first_payment_state': order.first_payment_state,
                'second_payment_state': order.second_payment_state,
                'third_payment_state': order.third_payment_state,

                'amount_residual': order.amount_residual,
                'advance_payment_status':order.advance_payment_status,
                'user_id': order.user_id.id or None,
                'user_name': order.user_id.name or None,
                'create_date': order.create_date.isoformat() if order.create_date else None,
                'payment': [
                    {
                        'payment_id' : p.id or None,
                        'payment_type' : p.payment_type,
                        'payment_amount' : p.amount,
                        'is_reconciled': p.is_reconciled
                    }  for p in payment
                ],
                'invoice' : [
                    {
                        'invoice_id' : i.id,
                        'invoice_name': i.name,
                        'invoice_state': i.state,
                        'payment_state': i.payment_state,
                        'invoice_payment_id': i.payment_id.id,
                        'ref': i.ref
                    } for i in invoice_p
                ],
                'order_lines': [
                    {
                        'id': l.id or None,
                        'product_id': l.product_id.id or None,
                        'product_name': l.product_id.name or None,
                        'product_uom_qty': l.product_uom_qty or None,
                        'product_uom': l.product_uom.id or None,
                        'product_uom_name': l.product_uom.name or None,
                        'image_1920': l.product_id.image_1920,
                        'image_128' : l.product_id.image_128,
                        'image_1024': l.product_id.image_1024,
                        'image_512': l.product_id.image_512,
                        'image_256': l.product_id.image_256,
                        'categ_id': l.product_id.categ_id.name,
                        'price_unit': l.price_unit or None,
                        'price_subtotal': l.price_subtotal or None,
                        'price_tax': l.price_tax or None,
                        'price_total': l.price_total or None,
                        'qty_delivered': l.qty_delivered or None,
                        'qty_to_invoice': l.qty_to_invoice or None,
                        'qty_invoiced': l.qty_invoiced or None,
                        'is_downpayment': l.is_downpayment or None,
                    } for l in order.order_line if not l.is_downpayment
                ]
            }

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(order_data)
            )
            return resp
        return  werkzeug.wrappers.Response(
            status=404,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Commande non trouvée")
        )


    # la fonction qu'on utilise
    @http.route('/api/precommandes',methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def api_create_preorder(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            partner_id = int(data.get('partner_id'))
            order_lines = data.get('order_lines')
            if not partner_id or not order_lines:
                raise ValueError('Invalid données pre-commande')
            
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)

            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            # company = request.env['res.company'].sudo().search([('id', '=', partner.company_id.id)], limit=1)

            previous_orders = request.env['sale.order'].sudo().search_count([('partner_id', '=', partner_id)])
            is_first_order = previous_orders == 0

            company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            if company:
                # Création de commande
                with request.env.cr.savepoint():
                    order = request.env['sale.order'].sudo().create({
                        'partner_id': partner_id,
                        'type_sale': 'preorder',
                        'currency_id': company.currency_id.id,
                        'company_id': company.id,
                        'commitment_date': datetime.datetime.now() + datetime.timedelta(days=60),
                        'payment_mode': 'domicile'
                        # 'state': 'sale'
                    })
                    # order.action_confirm()
                    for item in order_lines:
                        product_id = item.get('id')
                        product_uom_qty = item.get('quantity')
                        price_unit = item.get('list_price')
                        if not product_id or not product_uom_qty or not price_unit:
                            raise ValueError('Missing product data')
                        # Création de ligne de commande

                        if is_first_order:
                            price_unit *= 0.97 
                            
                        order_line = request.env['sale.order.line'].sudo().create({
                            'order_id': order.id,
                            'product_id': product_id,
                            'product_uom_qty': product_uom_qty,
                            'price_unit': price_unit,
                            'company_id': company.id,
                            'currency_id': company.currency_id.id,
                            'state': 'sale',
                            # 'type_sale': 'preorder',
                            'invoice_status': 'to invoice'
                        })
                    if order:
                        order.action_confirm()
            else:
                raise ValueError('Company not found')


            resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    'id': order.id,
                    'name': order.name,
                    'partner_id': order.partner_id.id,
                    'type_sale': order.type_sale,
                    'currency_id': order.currency_id.id,
                    'company_id': order.company_id.id,
                    'commitment_date': order.commitment_date.isoformat(),
                    'state': order.state,
                    'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
                    'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
                    'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,
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

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )


    @http.route('/api/precommandes/update', methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def api_update_preorder_order(self,**kwargs):
        try:
            data = json.loads(request.httprequest.data)
            partner_id = int(data.get('partner_id'))
            order_id = data.get('order_id')

            order = request.env['sale.order'].sudo().search([('id', '=', order_id), ( 'partner_id', '=', partner_id ) ], limit=1)
            # if not request.env.user or request.env.user._is_public():
            #     admin_user = request.env.ref('base.user_admin')
            #     request.env = request.env(user=admin_user.id)
            _logger.info(f"Order: {order}")
            if order:
                # Création de commande
                # with request.env.cr.savepoint():
                #     order.write({
                #         'state': 'sale'
                #     })
                order.action_confirm()
            else:
                raise ValueError('Order not found')


            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    'id': order.id,
                    'name': order.name,
                    'partner_id': order.partner_id.id,
                    'type_sale': order.type_sale,
                    'currency_id': order.currency_id.id,
                    'company_id': order.company_id.id,
                    'commitment_date': order.commitment_date.isoformat(),
                    'state': order.state,
                    'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
                    'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
                    'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,

                    'first_payment_amount': order.first_payment_amount,
                    'second_payment_amount': order.second_payment_amount,
                    'third_payment_amount': order.third_payment_amount,

                    'first_payment_state': order.first_payment_state,
                    'second_payment_state': order.second_payment_state,
                    'third_payment_state': order.third_payment_state,

                    'amount_residual': order.amount_residual,
                    'amount_total' : order.amount_total,
                    'amount_untaxed' : order.amount_untaxed,
                    'amount_tax': order.amount_tax,
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

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )

    def create_payment_preorder(self, order):

        if order:
            partner = request.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)], limit=1)

            company = request.env['res.company'].sudo().search([('id', '=', partner.company_id.id)], limit=1)
            journal = request.env['account.journal'].sudo().search([('type', 'in', ['bank', 'cash'])])
            journal_vr = journal[-1]
            _logger.info( f"journal  {journal} journal 6 : {journal_vr} " )

            payment_method_line_vr = request.env['account.payment.method.line'].sudo().search([
                ('id', '=', 9)], limit=1)
            account_payment = request.env['account.payment'].sudo().create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner.id,
                'amount': order.first_payment_amount,
                'journal_id': journal_vr.id,
                'currency_id': journal_vr.currency_id.id,
                'payment_method_line_id': payment_method_line_vr.id,
                # 'payment_method_id': 1,
                'sale_id': order.id,
                # 'move_id': new_invoice.id
            })
            if account_payment:
                _logger.info( f'id facture generere lors du payment {account_payment.move_id}')
                account_payment.action_post()
                return { 'invoice_id': account_payment.move_id.id , 'account_payment_id': account_payment.id  }
        else:
            return False



    @http.route('/api/precommandes/<id>', methods=['PUT'], type='http', cors="*", auth='none', csrf=False)
    @check_permissions
    def api_update_preorder(self, id, **kwargs):
        data = json.loads(request.httprequest.data)
        partner_id = int(data.get('partner_id'))
        order_lines = data.get('order_lines')

        current_user = request.env.user
        if not partner_id or not order_lines:
            return request.make_response(
                json.dumps({'status': 'erreur', 'message': 'Données de commande invalides'}),
                headers={'Content-Type': 'application/json'}
            )

        commande = request.env['sale.order'].sudo().search([('id', '=', id)], limit=1 )

        if not commande:
            return request.make_response(
                json.dumps({'status': 'erreur', 'message': 'Pre Commande non trouvée'}),
                headers={'Content-Type': 'application/json'}
            )

        commande.write({
            'commitment_date': datetime.datetime.now(),
            'state': 'sale'
        })

        # commande.action_confirm()
        response = werkzeug.wrappers.Response(
            status=204,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({
                'id': commande.id,
                'name': commande.name,
                'partner_id': commande.partner_id.id,
                'type_sale': commande.type_sale,
                'currency_id': commande.currency_id.id,
                'company_id': commande.company_id.id,
                'commitment_date': commande.commitment_date.isoformat(),
                'state': commande.state,
                'first_payment_date': commande.first_payment_date.isoformat() if commande.first_payment_date else None,
                'second_payment_date': commande.second_payment_date.isoformat() if commande.second_payment_date else None,
                'third_payment_date': commande.third_payment_date.isoformat() if commande.third_payment_date else None,
                'first_payment_amount': commande.first_payment_amount,
                'second_payment_amount': commande.second_paymen_tamount,
                'third_payment_amount': commande.third_payment_amount,

                'first_payment_state': commande.first_payment_state,
                'second_payment_state': commande.second_payment_state,
                'third_payment_state': commande.third_payment_state,
                'advance_payment_status': commande.advance_payment_status,
            })
        )
        return response


    @http.route('/api/precommandes_new', methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def api_create_preorder_new(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            partner_id = int(data.get('partner_id'))
            order_lines = data.get('order_lines')

            if not partner_id or not order_lines:
                raise ValueError('Invalid données pre-commande')

            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)

            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            company = request.env['res.company'].sudo().search([('id', '=', partner.company_id.id)], limit=1)
            journal = request.env['account.journal'].sudo().search([('company_id', '=', company.id),  ('type', '=', 'sale') ], limit=1)

            if company:
                # Création de commande
                with request.env.cr.savepoint():
                    order = request.env['sale.order'].sudo().create({
                        'partner_id': partner_id,
                        'type_sale': 'preorder',
                        'currency_id': company.currency_id.id,
                        'company_id': company.id,
                        'commitment_date': datetime.datetime.now() + datetime.timedelta(days=60),
                        # 'state': 'sale'
                    })
                    # order.action_confirm()
                    for item in order_lines:
                        product_id = item.get('id')
                        product_uom_qty = item.get('quantity')
                        price_unit = item.get('list_price')
                        if not product_id or not product_uom_qty or not price_unit:
                            raise ValueError('Missing product data')
                        # Création de ligne de commande
                        order_line = request.env['sale.order.line'].sudo().create({
                            'order_id': order.id,
                            'product_id': product_id,
                            'product_uom_qty': product_uom_qty,
                            'price_unit': price_unit,
                            'company_id': company.id,
                            'currency_id': company.currency_id.id,
                            'state': 'sale',
                            # 'type_sale': 'preorder',
                            'invoice_status': 'to invoice'
                        })
                     # Création de la facture
                    new_invoice = request.env['account.move'].sudo().create({
                        'move_type': 'out_invoice',
                        'amount_total' : order.amount_total,
                        'invoice_date': datetime.datetime.now() ,
                        'invoice_date_due': datetime.datetime.now(),
                        'invoice_line_ids': [],
                        'ref': 'Facture '+ order.name,
                        'journal_id': journal.id,
                        'partner_id': partner.id,
                        'company_id':company.id,
                        'currency_id': partner.currency_id.id,
                    })
                    for order_line in order_lines:

                        product_id = item.get('id')
                        quantity = item.get('quantity')
                        price_unit = item.get('list_price')

                        invoice_line = request.env['account.move.line'].sudo().create({
                            'move_id': new_invoice.id,
                            'product_id': product_id,
                            'quantity': quantity,
                            'price_unit': price_unit,
                            'company_id': company.id,
                            'currency_id': company.currency_id.id,
                            'partner_id': partner.id,
                            'ref': 'Facture ' + order.name,
                            'journal_id':journal.id,
                            'account_id': request.env['account.account'].sudo().search([('code', '=', '200000')], limit=1).id,
                            'credit': price_unit * quantity,
                            'name': order.name,
                            'debit': 0.0,
                        })
                    new_invoice.action_post()
                    order.action_confirm()
            else:
                raise ValueError('Company not found')

            resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    'id': order.id,
                    'name': order.name,
                    'partner_id': order.partner_id.id,
                    'type_sale': order.type_sale,
                    'currency_id': order.currency_id.id,
                    'company_id': order.company_id.id,
                    'commitment_date': order.commitment_date.isoformat(),
                    'state': order.state,

                    'first_payment_date': order.first_payment_date.isoformat() if order.first_payment_date else None,
                    'second_payment_date': order.second_payment_date.isoformat() if order.second_payment_date else None,
                    'third_payment_date': order.third_payment_date.isoformat() if order.third_payment_date else None,

                    'first_payment_amount': order.first_payment_amount,
                    'second_payment_amount': order.second_payment_amount,
                    'third_payment_amount': order.third_payment_amount,

                    'first_payment_state': order.first_payment_state,
                    'second_payment_state': order.second_payment_state,
                    'third_payment_state': order.third_payment_state,

                    'amount_residual': order.amount_residual,
                    'amount_total': order.amount_total,
                    'amount_tax': order.amount_tax,
                    'amount_untaxed': order.amount_untaxed,
                    'advance_payment_status': order.advance_payment_status,
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

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )





    def create_factures ( self, order , partner_id, company):
        if order:
            # Création de la première facture d'acompte
            first_invoice = request.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': order.first_payment_date,
            'invoice_date_due': order.first_payment_date,
            'company_id': order.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': False,
                'name': 'Acompte 1',
                'quantity': 1,
                'price_unit': order.first_payment_amount,
                'company_id': order.company_id.id,
                'currency_id': company.currency_id.id,
                'partner_id': partner_id,
                'date_maturity': datetime.datetime.now()
            })],
            'ref': 'Acompte 1 - ' + order.name,
            })
            first_invoice.action_post()

            # Création de la deuxième facture d'acompte
            second_invoice = request.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': order.second_payment_date,
            'invoice_date_due': order.second_payment_date,
            'company_id': order.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': False,
                'name': 'Acompte 2',
                'quantity': 1,
                'price_unit': order.second_payment_amount,
                'company_id': order.company_id.id,
                'currency_id': company.currency_id.id,
                'partner_id': partner_id,
                'date_maturity': datetime.datetime.now()
            })],
            'ref': 'Acompte 2 - ' + order.name,
            })
            second_invoice.action_post()

            # Création de la troisième facture d'acompte
            third_invoice = request.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': order.third_payment_date,
            'invoice_date_due': order.third_payment_date,
            'company_id': order.company_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': False,
                'name': 'Acompte 3',
                'quantity': 1,
                'price_unit': order.third_payment_amount,
                'company_id': order.company_id.id,
                'currency_id': company.currency_id.id,
                'partner_id': partner_id,
                'date_maturity': datetime.datetime.now()
            })],
            'ref': 'Acompte 3 - ' + order.name,
            })
            third_invoice.action_post()

            return True
        else:
            return False


