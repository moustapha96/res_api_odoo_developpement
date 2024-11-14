from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_mode = fields.Char(string='Mode de Payment', required=False)
    validation_state = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='État de Validation', required=True, default='pending')
    validation_rh = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='Etat de validation RH', required=True, default='pending')
    validation_admin = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='Etat de validation Admin', required=True, default='pending')


    def action_validate_credit_order_rh(self):
        """Validate the credit order by RH and send a confirmation email."""
        if self.validation_state == 'pending' and self.validation_rh == 'pending':
            self.validation_rh = 'validated'
            self.send_credit_order_validation_rh_mail()
        else:
            raise ValidationError(_("La commande est déjà validée ou rejetée par RH."))

    def send_credit_order_validation_rh_mail(self):
        """Send confirmation email for RH validation of credit order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_credit_order_validation_rh').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour la validation RH de la commande à crédit est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def action_reject_credit_order_rh(self):
        """Reject the credit order by RH and send a rejection email."""
        if self.validation_state == 'pending' and self.validation_rh == 'pending':
            self.validation_rh = 'rejected'
            self.send_credit_order_rejection_rh_mail()
        else:
            raise ValidationError(_("La commande est déjà validée ou rejetée par RH."))

    def send_credit_order_rejection_rh_mail(self):
        """Send rejection email for RH rejection of credit order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_credit_order_rejection_rh').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour le rejet RH de la commande à crédit est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def action_validate_credit_order_admin(self):
        """Validate the credit order by Admin and send a confirmation email."""
        if self.validation_state == 'pending' and self.validation_admin == 'pending':
            self.validation_admin = 'validated'
            self.send_credit_order_validation_admin_mail()
        else:
            raise ValidationError(_("La commande est déjà validée ou rejetée par l'administrateur."))

    def send_credit_order_validation_admin_mail(self):
        """Send confirmation email for Admin validation of credit order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_credit_order_validation_admin').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour la validation de l'administrateur de la commande à crédit est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def action_reject_credit_order_admin(self):
        """Reject the credit order by Admin and send a rejection email."""
        if self.validation_state == 'pending' and self.validation_admin == 'pending':
            self.validation_admin = 'rejected'
            self.send_credit_order_rejection_admin_mail()
        else:
            raise ValidationError(_("La commande est déjà validée ou rejetée par l'administrateur."))

    def send_credit_order_rejection_admin_mail(self):
        """Send rejection email for Admin rejection of credit order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_credit_order_rejection_admin').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour le rejet de l'administrateur de la commande à crédit est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}
        
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        # Adjust invoice state based on credit order validations
        if self.validation_state == 'validated' and self.validation_rh == 'validated' and self.validation_admin == 'validated':
            invoice_vals['state'] = 'draft'
        else:
            invoice_vals['state'] = 'cancel'
        return invoice_vals

    def _create_invoices(self, grouped=True, final=False):
        # Override the invoice creation logic
        invoices = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)
        for invoice in invoices:
            # Update invoice state based on order validation status
            if self.validation_state == 'validated' and self.validation_rh == 'validated' and self.validation_admin == 'validated':
                invoice.action_post()
            else:
                invoice.action_cancel()
        return invoices
    