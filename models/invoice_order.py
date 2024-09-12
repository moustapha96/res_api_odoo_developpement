from odoo import models, fields, api

class InvoiceOrder(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, vals):
        payment = super(InvoiceOrder, self).create(vals)
        order = self.env['sale.order'].sudo().search([('id', '=', vals.get('sale_id'))], limit=1)
        if order:
            self._create_and_link_invoice(payment, order)
        return payment

    def _create_and_link_invoice(self, payment, order):
        partner = order.partner_id
        company = partner.company_id
        journal_facture = self.env['account.journal'].sudo().search([('type', '=', 'sale')], limit=1)

        # Création de la facture
        new_invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'amount_total': order.amount_total,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': fields.Date.today(),
            'invoice_line_ids': [],
            'ref': 'Facture ' + order.name,
            'journal_id': journal_facture.id,
            'partner_id': partner.id,
            'company_id': company.id,
            'currency_id': partner.currency_id.id,
            'sale_id': order.id
        })

        if new_invoice:
            # Création des lignes de facture
            order_lines = self.env['sale.order.line'].sudo().search([('order_id', '=', order.id)])
            for order_line in order_lines:
                product_id = order_line.product_id.id
                quantity = order_line.product_uom_qty
                price_unit = order_line.price_unit

                self.env['account.move.line'].sudo().create({
                    'move_id': new_invoice.id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'price_unit': price_unit,
                    'company_id': company.id,
                    'currency_id': company.currency_id.id,
                    'partner_id': partner.id,
                    'ref': 'Facture ' + order.name,
                    'journal_id': journal_facture.id,
                    'name': order.name,
                })

            new_invoice.action_post()

            # Lier le paiement à la facture
            payment.write({
                'move_id': new_invoice.id,
                # 'invoice_ids': [(4, new_invoice.id)],
            })

        order.action_confirm()
