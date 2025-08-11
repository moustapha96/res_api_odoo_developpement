from odoo import models, fields, api
from odoo.http import request
import logging
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    @api.model
    def send_credit_order_validation_mail(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Validation de votre commande à crédit'
        today = datetime.now().date()
        payments = self._generate_payments(today)
        _logger.info("PAYMENTS TYPES: %s", [type(p) for p in payments])
        payment_info = self.generate_payment_schedule_html(payments)
        body_html = self._generate_email_body_html(partner, 'validation', payment_info)
        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('validation')


    @api.model
    def handle_state_change(self, vals):
        """
        Cette méthode vérifie les changements d'état RH et Admin
        et envoie les notifications appropriées.
        """
        if 'validation_rh_state' in vals:
            new_rh_state = vals.get('validation_rh_state')
            if new_rh_state == 'validated':
                self.send_credit_order_rh_validation()
                self.send_credit_order_to_admin_for_validation()
            elif new_rh_state == 'rejected':
                self.send_credit_order_rh_rejected()

        if 'validation_admin_state' in vals:
            new_admin_state = vals.get('validation_admin_state')
            if new_admin_state == 'validated':
                self.send_credit_order_admin_validation()
            elif new_admin_state == 'rejected':
                self.send_credit_order_admin_rejected()

        return True
    # def create(self , vals):
        # res = super(SaleCreditOrderMail, self).create(vals)
        # res.send_credit_order_creation_notification_to_hr()
        # res.send_credit_order_validation_mail()
        # return res
    

    def write(self, vals):
        """
        Redéfinition de la méthode `write` pour gérer les notifications
        lors de changements d'état.
        """
        # Appeler d'abord la méthode parent pour sauvegarder les changements
        result = super(SaleCreditOrderMail, self).write(vals)
        
        # Gérer les notifications après la sauvegarde
        self.handle_state_change(vals)
        
        if 'credit_month_rate' in vals or 'creditorder_month_count' in vals:
            for order in self:
                try: 
                    order.send_credit_order_validation_mail()
                except Exception as e:
                    _logger.error(f'Error sending validation mail for order {order.name}: {str(e)}')
        return result
    
    def _generate_payments(self, today):
        """
        Génère les informations de paiement en incluant explicitement l'acompte comme première échéance
        """
        payments = []
        payment_lines = self.env['sale.order.credit.payment'].search([('order_id', '=', self.id)])

        for line in payment_lines:
            label = "Premier Paiement (Acompte)" if line.sequence == 1 else f"ÉCHEANCE {line.sequence}"
            payments.append((label, line.amount, f"{line.rate:.1f}%", datetime.fromisoformat(line.due_date).date() , line.state))
        return payments
        
    def generate_payment_schedule_html(self, payments): 
        """
        Génère le HTML pour afficher l'échéancier de paiement dans un email.
        """
        payment_rows = "\n".join([
            f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">Échéance {idx}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{payment[4]}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{payment[1]} {self.currency_id.name}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{payment[3]}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{'Payé' if payment[4] == False  else 'Non Payé'}</td>
            </tr>
            """
            for idx, payment in enumerate(payments, start=1)
        ])

        return f"""
        <h3 style="color: #333; margin-top: 20px;">Échéancier de Paiement</h3>
        <table border='1' cellpadding='5' cellspacing='0' width='100%' style='min-width: 100%; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse; margin-top: 15px;'>
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Échéance</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Date d'échéance</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Montant dû</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Taux (%)</th>
                    <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Statut</th>
                   
                </tr>
            </thead>
            <tbody>
                {payment_rows}
            </tbody>
        </table>
        """
    
    def send_credit_order_validation_mail(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Validation de votre commande à crédit'
        payments = self._generate_payments(datetime.now().date())
        payment_schedule_html = self.generate_payment_schedule_html(payments)

        body_html = f"""
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family: Verdana, Arial, sans-serif; color: #454748; width: 100%; border-collapse: separate;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse: separate;">
                        <tr>
                            <td align="center" style="min-width: 590px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse: separate;">
                                    <tr>
                                        <td valign="middle">
                                            <span style="font-size: 10px;">Validation de votre commande à crédit</span><br/>
                                            <span style="font-size: 20px; font-weight: bold;">{self.name}</span>
                                        </td>
                                        <td valign="middle" align="right">
                                            <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colspan="2" style="text-align: center;">
                                            <hr width="100%" style="background-color: rgb(204, 204, 204); border: medium none; clear: both; display: block; font-size: 0px; min-height: 1px; line-height: 0; margin: 16px 0px 16px 0px;"/>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="min-width: 590px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse: separate;">
                                    <tr>
                                        <td>
                                            <p>Félicitations {partner.name},</p>
                                            <p>Votre commande à crédit numéro {self.name} a été créée avec succès.</p>
                                            <p>Détails des échéances :</p>
                                            {payment_schedule_html}
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                       
                        <!-- Footer CCBM -->
                            <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
                                        <td colspan="2" style="padding: 12px; text-align: center;">
                                            <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                                            <p> <a href="https://ccbmshop.sn" style="color: #875A7B;">www.ccbmshop.sn</a></p>
                                        </td>
                                    </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

        self.send_sms_notification('validation')
        return self.send_mail(mail_server,partner, subject, body_html)

    def _generate_payment_info_html(self, payments):
        """
        Génère le HTML pour les informations de paiement avec mise en forme améliorée
        et mise en évidence de l'acompte
        """
        if not payments:
            return "<p>Aucune information de paiement disponible.</p>"
        
        rows = ""
        for payment in payments:
            label, amount, status,rate, due_date = payment[:5]

            # Formatage de la date
            if isinstance(due_date, (datetime, date)):
                date_str = due_date.strftime('%d/%m/%Y')
            else:
                date_str = str(due_date)

            # Formatage du montant
            amount_fmt = f"{amount:,.0f}".replace(',', ' ')

            status_str = "Payé" if status else "Non Payé"

            # Mise en évidence de l'acompte
            bg_color = "#e8f4fd" if "Acompte" in label else ""

            rows += f"""
            <tr style="background-color: {bg_color}">
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: {'bold' if 'Acompte' in label else 'normal'}">
                    {label}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">
                    {amount_fmt} {self.currency_id.name}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    {status_str}
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                    {date_str} 
                </td>
            </tr>
            """
        
        return f"""
        <div style="margin-top: 20px;">
            <h3 style="color: #333; border-bottom: 2px solid #875A7B; padding-bottom: 5px;">
                Échéancier de Paiement
            </h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Échéance</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Montant</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Pourcentage</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Date</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <div style="margin-top: 15px; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                <p style="margin: 5px 0;">
                    <strong>Total commande:</strong> {self.amount_total:,.0f} {self.currency_id.name}
                </p>
                <p style="margin: 5px 0;">
                    <strong>Nombre d'échéances:</strong> {len(payments)}
                </p>
               
            </div>
        </div>
        """

    def send_payment_status_mail_creditorder(self):
        """
        Envoie un email de mise à jour du statut de paiement
        """
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Mise à jour de l\'état de votre commande à crédit'
        today = datetime.now().date()
        payments = self._generate_payments(today)
        payment_info = self._generate_payment_info_html(payments)
        
        # Calculs pour le statut de paiement
        total_amount = self.amount_total
        remaining_amount = self.amount_residual
        paid_amount = total_amount - remaining_amount
        paid_percentage = (paid_amount / total_amount) * 100 if total_amount > 0 else 0

        # Dates de livraison estimées
        commitment_date_start = datetime.now() + timedelta(days=1)
        commitment_date_end = datetime.now() + timedelta(days=3)
        commitment_date_start_str = commitment_date_start.strftime('%d/%m/%Y')
        commitment_date_end_str = commitment_date_end.strftime('%d/%m/%Y')

        # Message si totalement payé
        fully_paid_message = ""
        if remaining_amount == 0:
            fully_paid_message = "<p style='font-size: 16px; font-weight: bold; color: green; text-align: center; margin: 20px 0;'>✅ Votre commande à crédit est totalement payée.</p>"

        # Informations sur les produits commandés
        order_lines_info = ""
        for line in self.order_line:
            order_lines_info += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{line.product_id.name}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{int(line.product_uom_qty)}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{line.price_unit:,.0f} {self.currency_id.name}</td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{line.price_total:,.0f} {self.currency_id.name}</td>
            </tr>
            """

        additional_content = f"""
        <tr>
            <td align="center" style="min-width: 590px;">
                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 15px 8px; border-collapse:separate;">
                    <tr>
                        <td colspan="2">
                            <h3 style="color: #333; margin-bottom: 15px;">Détails de la commande</h3>
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 5px 0;">
                            <span style="font-size: 14px; font-weight: bold;">Client :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 5px 0;">
                            {partner.name}<br/>
                            {partner.phone or 'Non renseigné'}
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 5px 0;">
                            <span style="font-size: 14px; font-weight: bold;">Adresse :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 5px 0;">
                            {partner.city or 'Non renseignée'}
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 5px 0;">
                            <span style="font-size: 14px; font-weight: bold;">Date de livraison estimée :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 5px 0;">
                            Entre le {commitment_date_start_str} et {commitment_date_end_str}
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 5px 0;">
                            <span style="font-size: 14px; font-weight: bold;">Type de commande :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 5px 0;">
                            Commande à crédit
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td align="center" style="min-width: 590px; padding-top: 20px;">
                <h3 style="color: #333; margin-bottom: 15px;">Produits commandés</h3>
                <table border="1" cellpadding="5" cellspacing="0" width="590" style="min-width: 590px; background-color: white; border-collapse:collapse;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; border: 1px solid #ddd;">Produit</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Quantité</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Prix unitaire</th>
                            <th style="padding: 10px; border: 1px solid #ddd;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {order_lines_info}
                        <tr style="background-color: #f8f9fa; font-weight: bold;">
                            <td colspan="3" style="text-align:right; padding: 10px; border: 1px solid #ddd;">Total du panier :</td>
                            <td style="text-align:right; padding: 10px; border: 1px solid #ddd;">{total_amount:,.0f} {self.currency_id.name}</td>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
        <tr>
            <td align="center" style="min-width: 590px; padding-top: 20px;">
                {payment_info}
            </td>
        </tr>
        {f'<tr><td align="center" style="min-width: 590px; padding-top: 20px;">{fully_paid_message}</td></tr>' if fully_paid_message else ''}
        <tr>
            <td align="center" style="min-width: 590px; padding-top: 20px;">
                <h3 style="color: #333; margin-bottom: 15px;">Résumé</h3>
                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #f8f9fa; padding: 15px; border-collapse:separate; border-radius: 5px;">
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold;">Prix total :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold;">{total_amount:,.0f} {self.currency_id.name}</span>
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold; color: #28a745;">Montant payé :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold; color: #28a745;">{paid_amount:,.0f} {self.currency_id.name}</span>
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold; color: #dc3545;">Somme restante à payer :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold; color: #dc3545;">{remaining_amount:,.0f} {self.currency_id.name}</span>
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold;">Pourcentage payé :</span>
                        </td>
                        <td valign="middle" align="right" style="width: 50%; padding: 8px 0;">
                            <span style="font-size: 15px; font-weight: bold;">{paid_percentage:.1f}%</span>
                        </td>
                    </tr>
                </table>
                 <!-- Footer CCBM -->
                            <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
                                        <td colspan="2" style="padding: 12px; text-align: center;">
                                            <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                                            <p> <a href="https://ccbmshop.sn" style="color: #875A7B;">www.ccbmshop.sn</a></p>
                                        </td>
                                    </tr>
            </td>
        </tr>
        """

        body_html = self._generate_email_body_html(partner, 'payment_status', additional_content)
        return self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_rh_rejected(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)

        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Rejet de votre commande à crédit par le service RH'
        body_html = self._generate_email_body_html(partner, 'rh_rejection')

        if partner.email:
            self.send_mail(mail_server, partner, subject, body_html)
        else:
            _logger.error(f'Partner email not found for partner: {partner.name}')

        if partner.phone:
            self.send_sms_notification('rh_rejection')
        else:
            _logger.error(f'Partner phone not found for partner: {partner.name}')

    def send_credit_order_rh_validation(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Validation RH de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'rh_validation')

        if partner.email:
            self.send_mail(mail_server, partner, subject, body_html)
        else:
            _logger.error(f'Partner email not found for partner: {partner.name}')

        if partner.phone:
            self.send_sms_notification('rh_validation')
        else:
            _logger.error(f'Partner phone not found for partner: {partner.name}')

    def send_credit_order_to_admin_for_validation(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        admin_user = self.env['res.users'].sudo().search(
            [('groups_id', '=', self.env.ref('base.group_system').id)], limit=1
        )

        if not admin_user:
            _logger.error('No admin user found to send the confirmation email')
            return {'status': 'error', 'message': 'No admin user found'}

        subject = f'Confirmation requise pour la commande à crédit - {self.name}'
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
                                                <span style="font-size: 10px;">Commande à crédit</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {self.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
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
                                            <td>
                                                <p>Bonjour {self.company_id.name},</p>
                                                <p>Le service RH a confirmé la commande à crédit suivante :</p>
                                                <ul>
                                                    <li>Numéro de commande : {self.name}</li>
                                                    <li>Client : {self.partner_id.name}</li>
                                                    <li>Montant total : {self.amount_total} {self.currency_id.name}</li>
                                                </ul>
                                                <p>Votre confirmation est maintenant requise pour finaliser cette commande.</p>
                                                <p>Veuillez vous connecter au système pour examiner et valider cette commande.</p>
                                                <p>Cordialement,<br/>Le système automatique</p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
            
           <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
                            <td colspan="2" style="padding: 12px; text-align: center;">
                                <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                                <p> <a href="https://ccbmshop.sn" style="color: #875A7B;">www.ccbmshop.sn</a></p>
                            </td>
                        </tr>
        </table>
        '''
        if admin_user.partner_id.email:
            return self.send_mail(mail_server, admin_user.partner_id, subject, body_html)
        else:
            _logger.error(f'Admin email not found for admin: {admin_user.name}')
            return {'status': 'error', 'message': 'Admin email not found'}

    def send_credit_order_admin_validation(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)

        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Validation administrative de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'admin_validation')

        if partner.email:
            self.send_mail(mail_server, partner, subject, body_html)
        else:
            _logger.error(f'Partner email not found for partner: {partner.name}')

        if partner.phone:
            self.send_sms_notification('admin_validation')
        else:
            _logger.error(f'Partner phone not found for partner: {partner.name}')

    def send_credit_order_admin_rejected(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)

        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Rejet de votre commande à crédit par l\'administration'
        body_html = self._generate_email_body_html(partner, 'admin_rejection')

        if partner.email:
            self.send_mail(mail_server, partner, subject, body_html)
        else:
            _logger.error(f'Partner email not found for partner: {partner.name}')

        if partner.phone:
            self.send_sms_notification('admin_rejection')
        else:
            _logger.error(f'Partner phone not found for partner: {partner.name}')

    def send_mail(self, mail_server, partner, subject, body_html):
        if not mail_server:
            _logger.error('Mail server not configured')
            return {'status': 'error', 'message': 'Mail server not configured'}

        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = None

        if hasattr(partner, 'email') and partner.email:
            email_to = f'{partner.email}, {additional_email}'
        else:
            _logger.error(f'Partner email not found for partner: {partner.name}')
            return {'status': 'error', 'message': 'Partner email not found'}

        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }
        mail_mail = self.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}


    def send_sms_notification(self, notification_type):
        message_templates = {
            'validation': f"Bonjour {self.partner_id.name},\nVotre commande à crédit numéro {self.name} a été créée avec succès.",
            'rejection': f"Bonjour {self.partner_id.name},\nNous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.",
            'rh_rejection': f"Bonjour {self.partner_id.name},\nNous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par votre service des Ressources Humaines.",
            'admin_rejection': f"Bonjour {self.partner_id.name},\nNous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre administration.",
            'admin_validation': f"Bonjour {self.partner_id.name},\nNous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre administration.",
            'rh_validation': f"Bonjour {self.partner_id.name},\nNous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par votre service des Ressources Humaines.",
            'request': f"Bonjour {self.partner_id.name},\nNous avons bien reçu votre demande de commande à crédit numéro {self.name}. Elle est actuellement en cours de validation par nos services.",
            'creation': f"Bonjour {self.partner_id.name},\nVotre commande à crédit numéro {self.name} a été créée avec succès. Elle est actuellement en attente de validation par votre service des ressources humaines.",
            'hr_notification': f"Bonjour,\nUne nouvelle demande de validation de commande à crédit numéro {self.name} nécessite votre validation."
        }

        message = message_templates.get(notification_type, "")
        if message:
            recipient = self.partner_id.phone
            if recipient:
                sms_record = self.env['send.sms'].create({
                    'recipient': recipient,
                    'message': message,
                }).send_sms()
                _logger.info(f'SMS sent: {sms_record}')
            else:
                _logger.error(f'Partner phone not found for partner: {self.partner_id.name}')

    def _generate_email_body_html(self, partner, email_type, additional_content=""):
        email_content = {
            'validation': {
                'title': 'Validation de votre commande à crédit',
                'content': f"""
                    <p>Félicitations {partner.name},</p>
                    <p>Votre commande à crédit numéro {self.name} a été créée avec succès.</p>
                    <p>Détails des échéances :</p>
                """
            },
            'rejection': {
                'title': 'Rejet de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.</p>
                    <p>Si vous avez des questions concernant cette décision, n'hésitez pas à nous contacter pour plus d'informations.</p>
                """
            },
            'rh_rejection': {
                'title': 'Rejet de votre commande à crédit par le service RH',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par votre service des Ressources Humaines.</p>
                    <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
                """
            },
            'admin_rejection': {
                'title': 'Rejet de votre commande à crédit par l\'administration',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre administration.</p>
                    <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
                """
            },
            'admin_validation': {
                'title': 'Validation administrative de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre administration.</p>
                    <p>Nous vous invitons à vous connecter dès maintenant à la plateforme afin d’effectuer le paiement de {self.credit_month_rate}% du montant de la commande.</p>
                    <p>Nous vous tiendrons informé des prochaines étapes.</p>
                """
            },
            'rh_validation': {
                'title': 'Validation RH de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par votre service des Ressources Humaines.</p>
                    <p>Vous pouvez à présent attendre la validation finale de CCBM Shop avant de procéder au paiement.</p>
                    <p>Nous vous tiendrons informé des prochaines étapes.</p>
                """
            },
            'request': {
                'title': 'Votre demande de commande à crédit',
                'content': f"""
                    <p>Bonjour {partner.name},</p>
                    <p>Nous avons bien reçu votre demande de commande à crédit numéro {self.name}.</p>
                    <p>Elle est actuellement en cours de validation par nos services.</p>
                    <p>Nous vous tiendrons informé de l'avancement de votre demande.</p>
                """
            },
            'rh_confirmation': {
                'title': 'Confirmation requise pour la commande à crédit',
                'content': f"""
                    <p>Bonjour,</p>
                    <p>Une nouvelle commande à crédit nécessite votre confirmation :</p>
                    <ul>
                        <li>Numéro de commande : {self.name}</li>
                        <li>Client : {self.partner_id.name}</li>
                        <li>Montant total : {self.amount_total} {self.currency_id.name}</li>
                        <li>Pourcentage d'acompte : {self.credit_month_rate}% </li>
                        <li> Nombre d'écheances : {self.creditorder_month_count} Paiement(s) </li>
                    </ul>
                    <p>Veuillez examiner cette commande et prendre les mesures appropriées.</p>
                    <p>Cordialement,<br/>Le système automatique</p>
                """
            },
            'payment_status': {
                'title': 'Mise à jour de l\'état de votre commande à crédit',
                'content': f"""
                    <p>Bonjour {partner.name},</p>
                    <p>Voici la mise à jour de l'état de votre commande à crédit numéro {self.name}.</p>
                """
            }
        }

        return f"""
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
                                                <span style="font-size: 10px;">{email_content[email_type]['title']}</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {self.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
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
                                            <td>
                                                {email_content[email_type]['content']}
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            {additional_content}
                        </tbody>
                    </table>
                </td>
            </tr>
            <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
                            <td colspan="2" style="padding: 12px; text-align: center;">
                                <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                                <p> <a href="https://ccbmshop.sn" style="color: #875A7B;">www.ccbmshop.sn</a></p>
                            </td>
                        </tr>
        </table>
        """

    def get_sale_order_credit_payment(self):
        """
        Récupère les lignes de paiement de crédit pour cette commande
        """
        payments = self.env['sale.order.credit.payment'].search([('order_id', '=', self.id)])
        data = []
        for payment in payments:
            data.append({
                'sequence': payment.sequence,
                'due_date': payment.due_date.isoformat() if hasattr(payment.due_date, 'isoformat') else payment.due_date,
                'amount': payment.amount,
                'rate': payment.rate,
                'state': payment.state,
            })
        return data



    def send_credit_order_creation_notification_to_hr(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return {'status': 'error', 'message': 'Mail server not configured'}

        parent = self.partner_id.parent_id
        rh_user = request.env['res.partner'].sudo().search([('role', '=', 'main_user'), ('parent_id', '=', parent.id)], limit=1)
        if not rh_user:
            return False
        
        subject = 'Nouvelle commande à valider'

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
                                                <span style="font-size: 10px;">Commande à crédit</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {self.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
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
                                            <td>
                                                <p>Bonjour,</p>
                                                <p>Une nouvelle demande de commande à crédit a été créée et nécessite votre validation :</p>
                                                <ul>
                                                    <li>Numéro de commande : {self.name}</li>
                                                    <li>Client : {self.partner_id.name}</li>
                                                    <li>Montant total : {self.amount_total} {self.currency_id.name}</li>
                                                </ul>
                                                <p>Veuillez examiner cette demande et prendre les mesures appropriées.</p>
                                                <p>Cordialement,<br/>Le système automatique</p>
                                            </td>
                                        </tr>
                                    </table>
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
                                Généré par <a target="_blank" href="https://www.ccbmshop.sn" style="color: #875A7B;">CCBM SHOP</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''

        self.send_mail(mail_server, rh_user, subject, body_html)
        self.send_sms_notification('hr_notification')
