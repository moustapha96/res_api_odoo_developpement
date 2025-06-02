from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    

    def _get_company_journals(self, company):
        journals = self.env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'sale')])
        return journals
    
    def action_confirm(self):
        # Confirmation de la commande
        res = super(SaleOrderInherit, self).action_confirm()

        # Création de la facture
        for order in self:
            partner = order.partner_id
            company = partner.company_id or self.env.company

            # Récupérer les journaux de la société
            journals = self._get_company_journals(company)

            if not journals:
                raise UserError("Aucun journal de vente trouvé.")
            
            journal = journals[0]

            invoice_lines = []
            for line in order.order_line:
                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'name': line.name,
                    'tax_ids': [(6, 0, [])]
                }))

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'invoice_origin': order.name,
                'invoice_date': fields.Date.today(),
                'invoice_date_due': fields.Date.today(),
                'invoice_line_ids': invoice_lines,
                'ref': f"Facture {order.name}",
                'journal_id': journal.id,
                'partner_id': partner.id,
                'company_id': company.id,
                'currency_id': partner.currency_id.id or company.currency_id.id,
            })

           
            # Validation de la facture
            invoice.action_post()
            order.write({
                'invoice_ids': [(4, invoice.id)],
                'invoice_status': 'invoiced',
                'state': 'sale',
            })
        return res

    def action_confirm_credit_order(self):
        # Confirmation de la commande
        res = super(SaleOrderInherit, self).action_confirm()

        # Création de la facture
        for order in self:
            partner = order.partner_id
            company = partner.company_id or self.env.company

            # Récupérer les journaux de la société
            journals = self._get_company_journals(company)

            if not journals:
                raise UserError("Aucun journal de vente trouvé.")
            
            # Utiliser le premier journal trouvé ou appliquer une logique pour choisir le journal approprié
            journal = journals[0]

            invoice_lines = []
            for line in order.order_line:
                # pas de TVA
                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'name': line.name,
                    'tax_ids': [(6, 0, [])]
                }))

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'invoice_origin': order.name,
                'invoice_date': fields.Date.today(),
                'invoice_date_due': fields.Date.today(),
                'invoice_line_ids': invoice_lines,
                'ref': f"Facture {order.name}",
                'journal_id': journal.id,
                'partner_id': partner.id,
                'company_id': company.id,
                'currency_id': partner.currency_id.id or company.currency_id.id,
                'amount_total': order.first_payment_amount
            })

            invoice.action_post()
            order.write({
                'invoice_ids': [(4, invoice.id)],
                'invoice_status': 'invoiced'
            })

        return res


class CompanyJournals(models.Model):
    _inherit = 'res.company'

    def get_company_journals(self):
        # Récupérer l'ID de la société actuelle ou spécifier l'ID de la société souhaitée
        company_id = self.id
        # Rechercher les journaux associés à la société
        journals = self.env['account.journal'].search([('company_id', '=', company_id)])
        # Retourner les journaux trouvés
        return journals

    def print_company_journals(self):
        # Récupérer les journaux de la société
        journals = self.get_company_journals()
        # Afficher les journaux
        for journal in journals:
            print(f"Journal ID: {journal.id}, Journal Name: {journal.name}, Journal Type: {journal.type}")
