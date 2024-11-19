from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64

_logger = logging.getLogger(__name__)

# Company Model Inherit
class Company(models.Model):
    _inherit = 'res.company'

    entreprise_code = fields.Char(string='Code Entreprise',  required=False)

# Partner Model Inherit
class Partner(models.Model):
    _inherit = 'res.partner'

    password = fields.Char(string='Mot de passe de connexion sur la partie web', widget='password', required=False)
    is_verified = fields.Boolean(string='Etat verification compte mail', default=False)
    avatar = fields.Char(string='Photo profil Client', required=False)
    role = fields.Selection([
        ('main_user', 'Utilisateur Principal'),
        ('secondary_user', 'Utilisateur Secondaire')
    ], string='Rôle', default='secondary_user')
    adhesion = fields.Selection([
        ('pending', 'En cours de validation'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté')
    ], string='Adhésion', required=True, default='pending')

    # Mail Sending for Adhesion
    def action_validate_adhesion(self):
        """Validate the adhesion and send a confirmation email."""
        if self.adhesion == 'pending':
            self.adhesion = 'validated'
            self.send_adhesion_confirmation_mail()
        else:
            raise ValidationError(_("L'adhésion est déjà validée ou rejetée."))

    def send_adhesion_confirmation_mail(self):
        """Send confirmation email for validated adhesion."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_adhesion_confirmation').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour la confirmation d'adhésion est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def action_reject_adhesion(self):
        """Reject the adhesion and send a rejection email."""
        if self.adhesion == 'pending':
            self.adhesion = 'rejected'
            self.send_adhesion_rejection_mail()
        else:
            raise ValidationError(_("L'adhésion est déjà validée ou rejetée."))

    def send_adhesion_rejection_mail(self):
        """Send rejection email for rejected adhesion."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_adhesion_rejection').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour le rejet d'adhésion est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

# Sale Order Model Inherit
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

    # Mail Sending for Credit Order Validation
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

# Sale Order Mail Model Inherit - Modified for multiple order types
class SaleOrderMail(models.Model):
    _inherit = 'sale.order'

    def send_order_confirmation_mail(self):
        """Send confirmation email for simple order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partenaire introuvable pour la commande donnée.'}

        subject = 'Confirmation de votre commande'
        commitment_date = datetime.now() + timedelta(days=7)
        commitment_date_str = commitment_date.strftime('%Y-%m-%d')

        create_account_section = ""
        if not partner.password:
            # create_account_link = f"http://localhost:5173/create-compte?mail={partner.email}"
            create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
            # create_account_link = f"https://ccbme.sn/mail={partner.email}?create-compte"
            create_account_section = f'''
                <tr>
                    <td align="center" style="min-width: 590px; padding-top: 20px;">
                        <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre commande :</span><br/>
                        <a href="{create_account_link}" style="font-size: 16px; font-weight: bold;">Créer un compte</a>
                    </td>
                </tr>
            '''

        body_html = f'''
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
                        <tbody>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle">
                                                <span style="font-size: 10px;">Votre commande</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {self.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td colspan="2" style="text-align:center;">
                                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Détails du destinataire
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {partner.name}<br/>
                                                {partner.phone}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Adresse
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {partner.city}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Date de livraison estimée
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                Entre le {commitment_date_str} et {(commitment_date + timedelta(days=3)).strftime('%d-%b-%Y')}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Méthode de paiement
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                Paiement à la livraison
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="1" cellpadding="5" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;">
                                        <tr>
                                            <th>Produit</th>
                                            <th>Quantité</th>
                                            <th>Prix unitaire</th>
                                            <th>Total</th>
                                        </tr>
                                        {"".join([f"<tr><td>{line.product_id.name}</td><td>{line.product_uom_qty}</td><td>{line.price_unit}</td><td>{line.price_total}</td></tr>" for line in self.order_line])}
                                        <tr>
                                            <td colspan="3" style="text-align:right; font-weight:bold;">Total du panier :</td>
                                            <td style="font-weight:bold;">{self.amount_total}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            {create_account_section} 
                        </tbody>
                    </table>
                </td>
            </tr>
            <tr>
                <td align="center" style="min-width: 590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
                        <tr>
                            <td style="text-align: center; font-size: 13px;">
                                Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''

        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{partner.email}, {additional_email}'

        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }

        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def send_preorder_confirmation_mail(self):
        """Send confirmation email for pre-order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partenaire introuvable pour la commande donnée.'}

        subject = 'Confirmation de votre précommande'
        commitment_date_start = datetime.now() + timedelta(days=30)
        commitment_date_end = datetime.now() + timedelta(days=60)
        commitment_date_start_str = commitment_date_start.strftime('%Y-%m-%d')
        commitment_date_end_str = commitment_date_end.strftime('%Y-%m-%d')

        create_account_section = ""
        if not partner.password:
            # create_account_link = f"http://localhost:5173/create-compte?mail={partner.email}"
            create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
            # create_account_link = f"https://ccbme.sn/mail={partner.email}?create-compte"
            create_account_section = f'''
                <tr>
                    <td align="center" style="min-width: 590px; padding-top: 20px;">
                        <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre précommande :</span><br/>
                        <a href="{create_account_link}" style="font-size: 16px; font-weight: bold;">Créer un compte</a>
                    </td>
                </tr>
            '''

        payment_info = ""
        if self.first_payment_amount or self.second_payment_amount or self.third_payment_amount:
            payment_info += "<h3>Informations de paiement</h3>"
            payment_info += "<table border='1' cellpadding='5' cellspacing='0' width='590' style='min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;'>"
            payment_info += "<tr><th>Montant</th><th>Date d'échéance</th><th>État</th></tr>"
            if self.first_payment_amount:
                first_payment_date = self.first_payment_date.isoformat() if self.first_payment_date else "Non définie"
                first_payment_state = "Payé" if self.first_payment_state == 'paid' else "Non payé"
                payment_info += f"<tr><td>{self.first_payment_amount}</td><td>{first_payment_date}</td><td>{first_payment_state}</td></tr>"
            if self.second_payment_amount:
                second_payment_date = self.second_payment_date.isoformat() if self.second_payment_date else "Non définie"
                second_payment_state = "Payé" if self.second_payment_state == 'paid' else "Non payé"
                payment_info += f"<tr><td>{self.second_payment_amount}</td><td>{second_payment_date}</td><td>{second_payment_state}</td></tr>"
            if self.third_payment_amount:
                third_payment_date = self.third_payment_date.isoformat() if self.third_payment_date else "Non définie"
                third_payment_state = "Payé" if self.third_payment_state == 'paid' else "Non payé"
                payment_info += f"<tr><td>{self.third_payment_amount}</td><td>{third_payment_date}</td><td>{third_payment_state}</td></tr>"
            payment_info += "</table>"

        total_amount = self.amount_total
        remaining_amount = self.amount_residual

        body_html = f'''
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
                        <tbody>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle">
                                                <span style="font-size: 10px;">Votre précommande</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {self.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td colspan="2" style="text-align:center;">
                                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Détails du destinataire
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {partner.name}<br/>
                                                {partner.phone}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Adresse
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {partner.city}
                                            </td>
                                        </tr>
                                        <br />
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Date de livraison estimée
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                Entre le {commitment_date_start_str} et {commitment_date_end_str}
                                            </td>
                                        </tr>
                                        <br />
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Méthode de paiement
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                Paiement en ligne
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <br />
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="1" cellpadding="5" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;">
                                        <tr>
                                            <th>Produit</th>
                                            <th>Quantité</th>
                                            <th>Prix unitaire</th>
                                            <th>Total</th>
                                        </tr>
                                        {"".join([f"<tr><td>{line.product_id.name}</td><td>{line.product_uom_qty}</td><td>{line.price_unit}</td><td>{line.price_total}</td></tr>" for line in self.order_line])}
                                        <tr>
                                            <td colspan="3" style="text-align:right; font-weight:bold;">Total du panier :</td>
                                            <td style="font-weight:bold;">{total_amount}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            {create_account_section} 
                            <br />
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    {payment_info}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
            <tr>
                <td align="center" style="min-width: 590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
                        <tr>
                            <td style="text-align: center; font-size: 13px;">
                                Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''

        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{partner.email}, {additional_email}'

        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }

        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

# Add Credit Order Validation State and Validation Actions

    def action_validate_credit_order(self):
        """Validate the credit order and send a confirmation email."""
        if self.validation_state == 'pending':
            self.validation_state = 'validated'
            self.send_credit_order_confirmation_mail()
        else:
            raise ValidationError(_("La commande est déjà validée ou rejetée."))

    def send_credit_order_confirmation_mail(self):
        """Send confirmation email for validated credit order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_credit_order_confirmation').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour la confirmation de la commande à crédit est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    def action_reject_credit_order(self):
        """Reject the credit order and send a rejection email."""
        if self.validation_state == 'pending':
            self.validation_state = 'rejected'
            self.send_credit_order_rejection_mail()
        else:
            raise ValidationError(_("La commande est déjà validée ou rejetée."))

    def send_credit_order_rejection_mail(self):
        """Send rejection email for rejected credit order."""
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        template_id = self.env.ref('your_module_name.email_template_credit_order_rejection').id
        if not template_id:
            raise UserError(_("Le modèle d'email pour le rejet de la commande à crédit est manquant."))

        try:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            return {'status': 'success', 'message': 'Email envoyé avec succès.'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

