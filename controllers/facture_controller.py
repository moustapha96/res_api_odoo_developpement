# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
_logger = logging.getLogger(__name__)


class FactureREST(http.Controller):


    @http.route('/api/partner/<id>/factures', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_get_facture_user(self, id, **kwargs):
        try:
            if id:
                invoices = request.env['account.move'].sudo().search([ ('partner_id', '=', id)])

                if not invoices:
                    raise ValueError('Aucune Facture non trouvé ' + id )

                resp = werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({
                        'invoices': [
                            {
                                'id': invoice.id,
                                'name': invoice.name,
                                'partner_id': invoice.partner_id.id,
                                'date': invoice.invoice_date.isoformat(),
                                'due_date': invoice.invoice_date_due.isoformat(),
                                'lines': [
                                    {
                                        'id': line.id,
                                        'product_id': line.product_id.id,
                                        'quantity': line.quantity,
                                        'price_unit': line.price_unit,
                                        'company_id': line.company_id.id,
                                        'currency_id': line.currency_id.id,
                                        'partner_id': line.partner_id.id,
                                        'ref': line.ref
                                    } for line in invoice.invoice_line_ids
                                ]
                            } for invoice in invoices
                        ]
                    })
                )

                return resp

            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Invalid user ID'}),
                headers={'Content-Type': 'application/json'}
            )

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


    @http.route('/api/factures/<id>/create', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_create_invoice(self, id , **kwargs):
        try:

            order = request.env['sale.order'].sudo().search([ ('id', '=', id ) ] , limit = 1)
            partner = request.env['res.partner'].sudo().search([('id', '=', order.partner_id.id)], limit=1)
            company = request.env['res.company'].sudo().search([('id', '=', partner.company_id.id)], limit=1)

            if order:
                # Création de commande
                with request.env.cr.savepoint():
                    # Création de la facture
                    new_invoice = request.env['account.move'].sudo().create({
                        'move_type': 'out_invoice',
                        'partner_id': partner.id,
                        'invoice_date': order.date_order,
                        'invoice_date_due': order.date_order,
                        'invoice_line_ids': [],
                        # 'name': 'Facture ' + order.name
                    })

                    # Création des lignes de facture
                    for order_line in order.order_lines:
                        product_id = order_line.get('id')
                        quantity = order_line.get('quantity')
                        price_unit = order_line.get('list_price')

                        invoice_line = request.env['account.move.line'].sudo().create({
                            'move_id': new_invoice.id,
                            'product_id': product_id,
                            'quantity': quantity,
                            'price_unit': price_unit,
                            'company_id': company.id,
                            'currency_id': company.currency_id.id,
                            'partner_id': partner.id,
                            # 'ref': 'Facture ' + order.name,
                        })
                        new_invoice.write({
                           'invoice_line_ids' : [invoice_line]
                        })

            else:
                raise ValueError('Order not found')


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
                    'invoice_id': new_invoice.id,
                    'invoice_lines': [
                        {
                            'id': invoice_line.id,
                            'product_id': invoice_line.product_id.id,
                            'quantity': invoice_line.quantity,
                            'price_unit': invoice_line.price_unit,
                            'company_id': invoice_line.company_id.id,
                            'currency_id': invoice_line.currency_id.id,
                            'partner_id': invoice_line.partner_id.id,
                            'ref': invoice_line.ref
                        } for invoice_line in new_invoice.invoice_line_ids
                    ],
                })
            )
            return resp

        except ValueError as e:
            _logger.error("Premier erreur "+ str(e))
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )
        except Exception as e:
            _logger.error("Premier erreur "+ str(e))
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )
