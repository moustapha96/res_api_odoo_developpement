

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model
    def _are_all_products_delivered(self, sale_order):
        for line in sale_order.order_line:
            delivered_qty = sum(
                move.qty_done
                for picking in sale_order.picking_ids.filtered(lambda p: p.state == 'done')
                for move in picking.move_line_ids_without_package
                if move.product_id == line.product_id
            )
            if delivered_qty < line.product_uom_qty:
                return False
        return True

    def action_post(self):
        for move in self:
            if move.move_type == 'out_invoice' and move.invoice_origin:
                sale_orders = self.env['sale.order'].search([('name', '=', move.invoice_origin)])
                for order in sale_orders:
                    if order.state == 'cancel':
                        raise UserError("Impossible de valider la facture car la commande a été annulée.")
                    if not self._are_all_products_delivered(order):
                        raise UserError("Impossible de valider la facture car tous les produits n'ont pas encore été livrés.")
                    if order.amount_residual <= 0:
                        order.write({'state': 'to_delivered'})

        res = super().action_post()
        return res
    
    def action_send_invoice_email(self):
        """
        Envoyer la facture par email.
        
        Cette méthode lance un wizard pour envoyer la facture par email. Le wizard utilise 
        le modèle d'email 'account.email_template_edi_invoice' pour générer le contenu de l'email.
        Le modèle est paramétré pour contenir
        les informations de la facture.
        
        Returns:
            dict: Un dictionnaire qui décrit l'action à lancer pour afficher le wizard.
        """
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        if not template:
            raise UserError("Template d'email introuvable")

        compose_form = self.env.ref('account.view_account_move_send_wizard', False)
        ctx = {
            'default_model': 'account.move',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
        }
        return {
            'name': 'Envoyer la facture par email',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if order.state == 'sale':
                existing_invoices = self.env['account.move'].search([
                    ('invoice_origin', '=', order.name),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel')
                ])
                for invoice in existing_invoices:
                    for payment in invoice.payment_ids:
                        payment.action_draft()
                        payment.action_cancel()
                    invoice.invoice_line_ids.unlink()
                    for line in order.order_line:
                        invoice.write({'invoice_line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'quantity': line.product_uom_qty,
                            'price_unit': line.price_unit,
                            'name': line.name,
                        })]})
                    invoice.write({'state': 'draft'})
                if not existing_invoices:
                    invoice_lines = [(0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'name': line.name,
                    }) for line in order.order_line]
                    self.env['account.move'].create({
                        'move_type': 'out_invoice',
                        'partner_id': order.partner_id.id,
                        'invoice_origin': order.name,
                        'invoice_line_ids': invoice_lines,
                    })
        return res

    def action_cancel(self):
        for order in self:
            order.state = 'cancel'
            for picking in order.picking_ids:
                if picking.state == 'done':
                    for move in picking.move_line_ids_without_package:
                        move.qty_done = 0
                    picking.write({'state': 'cancel'})
            invoices = self.env['account.move'].search([
                ('invoice_origin', '=', order.name),
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel')
            ])
            for invoice in invoices:
                invoice.write({'state': 'cancel'})
                for payment in invoice.payment_ids:
                    payment.action_draft()
                    payment.action_cancel()
        return True

