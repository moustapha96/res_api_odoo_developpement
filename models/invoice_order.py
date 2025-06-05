

from odoo import models, fields, api
from odoo.exceptions import UserError

# class SaleOrderInherit(models.Model):
#     _inherit = 'sale.order'


#     def _get_company_journals(self, company):
#         journals = self.env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'sale')])
#         return journals

#     def action_create_invoice_order(self):
#         for order in self:
#             if not order.invoice_status != 'to invoice':
#                 raise UserError("La livraison n'a pas encore été faite.")

#             if order.invoice_ids:
#                 raise UserError("La commande a deja une facture.")
            
#             if order.state == "sale":
#                 partner = order.partner_id
#                 company = partner.company_id or self.env.company

#                 journals = self._get_company_journals(company)

#                 if not journals:
#                     raise UserError("Aucun journal de vente trouvé.")

#                 journal = journals[0]

#                 invoice_lines = []
#                 for line in order.order_line:
#                     invoice_lines.append((0, 0, {
#                         'product_id': line.product_id.id,
#                         'quantity': line.product_uom_qty,
#                         'price_unit': line.price_unit,
#                         'name': line.name,
#                         'tax_ids': [(6, 0, [])]
#                     }))

#                 invoice = self.env['account.move'].create({
#                     'move_type': 'out_invoice',
#                     'invoice_origin': order.name,
#                     'invoice_date': fields.Date.today(),
#                     'invoice_date_due': fields.Date.today(),
#                     'invoice_line_ids': invoice_lines,
#                     'ref': f"Facture {order.name}",
#                     'journal_id': journal.id,
#                     'partner_id': partner.id,
#                     'company_id': company.id,
#                     'currency_id': partner.currency_id.id or company.currency_id.id,
#                 })

#                 invoice.action_post()
#                 order.write({
#                     'invoice_ids': [(4, invoice.id)],
#                     'invoice_status': 'invoiced',
#                     'state': 'to_delivered',
#                 })
#                 return invoice

#     def action_confirm_credit_order(self):
#         res = super(SaleOrderInherit, self).action_confirm()
#         for order in self:
#             partner = order.partner_id
#             company = partner.company_id or self.env.company

#             journals = self._get_company_journals(company)

#             if not journals:
#                 raise UserError("Aucun journal de vente trouvé.")

#             journal = journals[0]

#             invoice_lines = []
#             for line in order.order_line:
#                 invoice_lines.append((0, 0, {
#                     'product_id': line.product_id.id,
#                     'quantity': line.product_uom_qty,
#                     'price_unit': line.price_unit,
#                     'name': line.name,
#                     'tax_ids': [(6, 0, [])]
#                 }))

#             invoice = self.env['account.move'].create({
#                 'move_type': 'out_invoice',
#                 'invoice_origin': order.name,
#                 'invoice_date': fields.Date.today(),
#                 'invoice_date_due': fields.Date.today(),
#                 'invoice_line_ids': invoice_lines,
#                 'ref': f"Facture {order.name}",
#                 'journal_id': journal.id,
#                 'partner_id': partner.id,
#                 'company_id': company.id,
#                 'currency_id': partner.currency_id.id or company.currency_id.id,
#                 'amount_total': order.first_payment_amount
#             })

#             invoice.action_post()
#             order.write({
#                 'invoice_ids': [(4, invoice.id)],
#                 'invoice_status': 'invoiced'
#             })

#         return res

#     def action_confirm(self):
#         self._create_invoices()
#         res = super(SaleOrderInherit, self).action_confirm()
#         self.action_create_invoice_order()
#         return res

# class CompanyJournals(models.Model):
#     _inherit = 'res.company'

#     def get_company_journals(self):
#         company_id = self.id
#         journals = self.env['account.journal'].search([('company_id', '=', company_id)])
#         return journals

#     def print_company_journals(self):
#         journals = self.get_company_journals()
#         for journal in journals:
#             print(f"Journal ID: {journal.id}, Journal Name: {journal.name}, Journal Type: {journal.type}")




class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model
    def _is_delivery_done(self, sale_order):
        """
        Vérifie si la livraison est effectuée pour une commande donnée.
        """
        for picking in sale_order.picking_ids:
            if picking.state != 'done':
                return False
        return True

    def action_post(self):
        for move in self:
            if move.move_type == 'out_invoice' and move.invoice_origin:
                sale_orders = self.env['sale.order'].search([('name', '=', move.invoice_origin)])
                for order in sale_orders:
                    if not self._is_delivery_done(order):
                        raise UserError("Impossible de valider la facture car la livraison n'est pas encore effectuée.")
        return super(AccountMoveInherit, self).action_post()
