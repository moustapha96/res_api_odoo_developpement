from odoo import models, fields, api

class SalePreOrderAccountMove(models.Model):
    _inherit = 'sale.order'


    amount_paid = fields.Monetary(string='Total Amount Paid', compute='_compute_amount_paid')
    def _compute_amount_paid(self):
        for order in self:
            payments = self.env['account.payment'].search([('sale_id', '=', order.id)])
            order.amount_paid = sum(payments.mapped('amount'))


    def create_invoice(self):
        for order in self:
            if order.state == 'sale' and order.type_sale == "preorder":
                if not order.invoice_ids:
                    if order.amount_total == order.amount_paid:
                        partner = order.partner_id
                        company = partner.company_id
                        journal = self.env['account.journal'].sudo().search([('id', '=', 1)], limit=1)

                        invoice = self.env['account.move'].create({
                            'sale_id': order.id,
                            'partner_id': order.partner_id.id,
                            'move_type': 'out_invoice',
                            'invoice_origin': order.name,
                            'journal_id': journal.id,
                            'currency_id': journal.currency_id.id,
                            'invoice_line_ids': [(0, 0, {
                                'product_id': line.product_id.id,
                                'quantity': line.product_uom_qty,
                                'price_unit': line.price_unit,
                                'name': line.name,
                                'account_id': line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id,
                            }) for line in order.order_line],
                        })

                        invoice.action_post()
                        invoice_count = self.env['account.move'].search([('invoice_origin', '=', order.name)])

                        if invoice:
                            order.write({'invoice_ids': [(4, invoice.id, None)], 'invoice_count': len(invoice_count)})
                            payment = self.env['account.payment'].search([('partner_id', '=', order.partner_id.id), ('amount', '=', order.amount_total)], limit=1)
                            if payment:
                                invoice.write({'payment_id': payment.id})

    def _compute_amount_paid(self):
        for order in self:
            payments = self.env['account.payment'].search([('sale_id', '=', order.id)])
            order.amount_paid = sum(payments.mapped('amount'))
            # order.amount_paid = sum(order.payment_ids.mapped('amount'))

    @api.depends('amount_paid', 'amount_total')
    def _compute_invoice_status(self):
        for order in self:
            if order.amount_total == order.amount_paid:
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'to invoice'

    @api.onchange('amount_paid', 'amount_total')
    def _onchange_payment_status(self):
        for order in self:
            if order.amount_total == order.amount_paid:
                order.create_invoice()