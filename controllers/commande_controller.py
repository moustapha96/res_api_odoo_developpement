# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)


class CommandeREST(http.Controller):

    @http.route('/api/commandes/<id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_orders_user_GET(self, id, **kw):

        if id:
            orders = request.env['sale.order'].sudo().search([('partner_id.id','=', id ) , ('type_sale' , '=' , 'order' )])
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
                        'state': o.state or None,
                        'user_id': o.user_id.id or None,
                        'user_name': o.user_id.name or None,
                        'create_date': o.create_date.isoformat() if o.create_date else None,
                        'payment_term_id': o.payment_term_id.id or None,
                        'advance_payment_status':o.advance_payment_status,
                        'commitment_date': o.commitment_date.isoformat() if o.commitment_date else None,
                        'note': o.note or None,
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
            else:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps([])
                )
        else:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("partner id non valide")
            )


    @http.route('/api/commandes/details', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_orders__GET_ONE(self,**kw):
        data = json.loads(request.httprequest.data)
        partner_id = int( data.get('partner_id'))
        commande_id = int (data.get('commande_id'))

        order = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner_id),
            ('id', '=', commande_id),
            ('type_sale', '=', 'order')
        ])
        if not order:
            return werkzeug.wrappers.Response(
                status=404,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Commande introuvable")
            )
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
                'state': order.state or None,
                'user_id': order.user_id.id or None,
                'user_name': order.user_id.name or None,
                'create_date': order.create_date.isoformat() if order.create_date else None,
                'amount_untaxed': order.amount_untaxed or None,
                'amount_tax': order.amount_tax or None,
                'amount_total': order.amount_total or None,
                'state': order.state or None,
                'user_id': order.user_id.id or None,
                'payment_term_id': order.payment_term_id.id or None,
                'advance_payment_status':order.advance_payment_status,
                'commitment_date': order.commitment_date.isoformat() if order.commitment_date else None,
                'note': order.note or None,
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
            return resp
        return  werkzeug.wrappers.Response(
            status=404,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Commande non trouvée")
        )

    @http.route('/api/commandes', methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def api_create_order(self, **kwargs):
        data = json.loads(request.httprequest.data)
        partner_id = int( data.get('partner_id'))
        order_lines = data.get('order_lines')
        state = data.get('state')

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        if not partner_id or not order_lines:
            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Invalid order data'}),
                headers={'Content-Type': 'application/json'}
            )

        partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
        company = request.env['res.company'].sudo().search([('id', '=', partner.company_id.id)], limit=1)

        order = request.env['sale.order'].sudo().create({
                'partner_id': partner_id,
                'type_sale': 'order',
                'currency_id' : company.currency_id.id,
                'company_id' : company.id,
                'commitment_date': datetime.datetime.now() + datetime.timedelta(days=30),
                # 'state': 'sale'
            })

        for item in order_lines:
            product_id = item.get('id')
            product_uom_qty = item.get('quantity')
            price_unit = item.get('list_price')

            if not product_id or not product_uom_qty or not price_unit:
                return request.make_response(
                    json.dumps({'status': 'error', 'message': 'Missing product data'}),
                    headers={'Content-Type': 'application/json'}
                )

            request.env['sale.order.line'].sudo().create({
                'order_id': order.id,
                'product_id': product_id,
                'product_uom_qty': product_uom_qty,
                'price_unit': price_unit,
                'state': 'sale'
            })

        # if order:
            # order.action_confirm()
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
                        'name': order_line.product_id.name,
                        'image_1920': order_line.product_id.image_1920,
                        'image_128' : order_line.product_id.image_128,
                        'image_1024': order_line.product_id.image_1024,
                        'image_512': order_line.product_id.image_512,
                        'image_256': order_line.product_id.image_256,
                        'categ_id': order_line.product_id.categ_id.name,
                        'type': order_line.product_id.type,
                        'description': order_line.product_id.description,
                        'price_total': order_line.price_total,
                    } for order_line in order.order_line
                ],
            })
        )
        return resp


    @http.route('/api/getcommande/<id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_orders_preorder_GET(self, id , **kw):
        order = request.env['sale.order'].sudo().search([('id','=', id)])
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
                'state': order.state or None,
                'user_id': order.user_id.id or None,
                'user_name': order.user_id.name or None,
                'create_date': order.create_date.isoformat() if order.create_date else None,
                'state': order.state or None,
                'user_id': order.user_id.id or None,
                'payment_term_id': order.payment_term_id.id or None,
                'advance_payment_status':order.advance_payment_status,
               
                'commitment_date': order.commitment_date.isoformat() if order.commitment_date else None,
                'note': order.note or None,
               
                'company_id': order.company_id.id,
               
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
               
                'user_id': order.user_id.id or None,
                'user_name': order.user_id.name or None,

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
                } for l in order.order_line if l.product_id and l.product_id.name != 'Acompte']
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


    @http.route('/api/tracking', methods=['POST'] , type='http', auth='none' , cors="*" , csrf=False )
    def api_orders_trackink_GET(self , **kw):
        data = json.loads(request.httprequest.data)
        email = data.get('email')
        name = data.get('name')

        if email is None or name is None:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Missing email or name")
            )
        partner = request.env['res.partner'].sudo().search([ ( 'email', '=', email ) ] , limit=1)
        if not partner:
            return  werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Utilisateur n'existe pas")
            )
        if partner:
            order = request.env['sale.order'].sudo().search([('partner_id','=', partner.id), ('name','=', name)], limit=1)
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
                'state': order.state or None,
                'user_id': order.user_id.id or None,
                'user_name': order.user_id.name or None,
                'create_date': order.create_date.isoformat() if order.create_date else None,
                'state': order.state or None,
                'user_id': order.user_id.id or None,
                'payment_term_id': order.payment_term_id.id or None,
                'advance_payment_status':order.advance_payment_status,
               
                'commitment_date': order.commitment_date.isoformat() if order.commitment_date else None,
                'note': order.note or None,
               
                'company_id': order.company_id.id,
               
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
               
                'user_id': order.user_id.id or None,
                'user_name': order.user_id.name or None,

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
                } for l in order.order_line if l.product_id and l.product_id.name != 'Acompte']
            }

                resp = werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps(order_data)
                )
                return resp

        return  werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Commande non trouvée")
        )
    

    @http.route('/api/commande/<id>/delete', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_delete_order(self, id):
        try:
            order = request.env['sale.order'].sudo().search([('id', '=', id)], limit=1)
            if not order:
                return request.make_response(
                    json.dumps({'erreur': 'Commande non trouvée'}),
                    headers={'Content-Type': 'application/json'}
                )

            order.write({'state': 'cancel'})
            res_cancel = order.action_cancel()
            # Supprimer la commande
            if  res_cancel:
                order.unlink()
                return request.make_response(
                    json.dumps({
                        'id': id,
                        'message': 'Commande supprimée avec succès'
                    }),
                    headers={'Content-Type': 'application/json'}
                )

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'})
