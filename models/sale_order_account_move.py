from odoo import models, fields, api

class SaleOrderAccountMove(models.Model):
    _inherit = 'sale.order'

    def create_invoice(self):
        for order in self:
        # Vérifiez si la commande est confirmée
            if order.state == 'sale' and order.type_sale == "order":
                # Vérifiez si la commande a déjà une facture associée
                if not order.invoice_ids:
                    partner = order.partner_id
                    company = partner.company_id
                    # Créez une facture basée sur la commande de vente
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

                    # Validez la facture
                    invoice.action_post()
                    # Comptez le nombre de factures associées à la commande
                    invoice_count = self.env['account.move'].search([('invoice_origin', '=', order.name)])
                    # Comptez le nombre de factures associées à la commande
                   
                    if invoice:
                        order.write({'invoice_ids': [(4, invoice.id, None)], 'invoice_count': len (invoice_count)})
                        # Trouvez le paiement effectué sur la commande
                    payment = self.env['account.payment'].search([('partner_id', '=', order.partner_id.id), ('amount', '=', order.amount_total)], limit=1)
                    # Reliez le paiement à la facture en utilisant le champ payment_id
                    if payment:
                        invoice.write({'payment_id': payment.id})

    # @api.model
    def action_confirm(self):
        res = super(SaleOrderAccountMove, self).action_confirm()
        self.create_invoice()
        return res
