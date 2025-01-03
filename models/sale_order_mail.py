from odoo import models, fields, api

from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64

_logger = logging.getLogger(__name__)

class SaleOrderMail(models.Model):
    _inherit = 'sale.order'

    
    def send_order_confirmation_mail(self):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        # Récupérer le partenaire associé à la commande
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        # Construire le sujet et les dates de livraison
        subject = 'Confirmation de votre commande'
        commitment_date = datetime.now() + timedelta(days=7)
        commitment_date_str = commitment_date.strftime('%Y-%m-%d')

        # Vérifier si le partenaire a déjà un mot de passe
        create_account_section = ""
        if not partner.password:
            # Générer le lien pour créer un compte
            # create_account_link = f"https://ccbme.sn/mail={partner.email}?create-compte"
            # create_account_link = f"http://localhost:5173/create-compte?mail={partner.email}"
            create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
            create_account_section = f'''
                <tr>
                    <td align="center" style="min-width: 590px; padding-top: 20px;">
                        <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre commande :</span><br/>
                        <a href="{create_account_link}" style="font-size: 16px; font-weight: bold;">Créer un compte</a>
                    </td>
                </tr>
            '''
        
        # Construire le contenu de l'e-mail
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
                            {create_account_section} <!-- Section ajoutée pour le lien de création de compte -->
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

        # Définir les valeurs du message e-mail
        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }

        # Envoi de l'e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}


    def send_preorder_confirmation_mail(self):
    # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer le partenaire associé à la commande
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        # Construire le sujet de l'e-mail
        subject = 'Confirmation de votre précommande'

        # Définir les dates de livraison
        commitment_date_start = datetime.now() + timedelta(days=30)
        commitment_date_end = datetime.now() + timedelta(days=60)
        commitment_date_start_str = commitment_date_start.strftime('%Y-%m-%d')
        commitment_date_end_str = commitment_date_end.strftime('%Y-%m-%d')

        # Vérifier si le partenaire a déjà un mot de passe
        create_account_section = ""
        if not partner.password:
            # Générer le lien pour créer un compte
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

        # Générer les informations de paiement
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

        # Construire le contenu de l'e-mail
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
                            {create_account_section} <!-- Section ajoutée pour le lien de création de compte -->
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

        # Définir les valeurs du message e-mail
        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }

        # Construire le message e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}
     

    def send_credit_order_confirmation_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Demande de commande à crédit en cours'
        
        create_account_section = ""
        if not partner.password:
            create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
            create_account_section = self._generate_create_account_section(create_account_link)
        
        body_html = self._generate_email_body_html(partner, 'request', create_account_section)

        self.send_mail(mail_server, partner, subject, body_html)

    def _generate_payment_info_html(self, payments):
        payment_rows = "".join([
            f"""
            <tr>
                <td>{payment[0]}</td>
                <td>{payment[1]:.2f}</td>
                <td>{payment[2]}</td>
                <td>{payment[3].strftime('%d/%m/%Y')}</td>
            </tr>
            """ for payment in payments
        ])

        return f"""
        <h3>Informations de paiement</h3>
        <p>Veuillez noter que le paiement initial de 50% validera complètement votre commande à crédit.</p>
        <table border='1' cellpadding='5' cellspacing='0' width='590' style='min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;'>
            <tr>
                <th>Échéance</th>
                <th>Montant</th>
                <th>Pourcentage</th>
                <th>Date d'échéance</th>
            </tr>
            {payment_rows}
        </table>
        """

    def _generate_create_account_section(self, create_account_link):
        return f"""
        <tr>
            <td align="center" style="min-width: 590px; padding-top: 20px;">
                <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre commande à crédit :</span><br/>
                <a href="{create_account_link}" style="font-size: 16px; font-weight: bold;">Créer un compte</a>
            </td>
        </tr>
        """

    def _generate_email_body_html(self, partner, email_type, additional_content=""):
        email_content = {
            'validation': {
                'title': 'Validation de votre précommande à crédit',
                'content': f"""
                    <p>Félicitations {partner.name},</p>
                    <p>Votre commande à crédit numéro {self.name} a été validée.</p>
                    <p><strong>Important :</strong> Le paiement initial de 50% validera complètement votre commande à crédit.</p>
                    <p>Détails de la commande :</p>
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
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre service des Ressources Humaines.</p>
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
                    <p>Cette étape marque une avancée importante dans le processus de validation de votre commande.</p>
                    <p>Nous vous tiendrons informé des prochaines étapes.</p>
                """
            },
            'rh_validation': {
                'title': 'Validation RH de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre service des Ressources Humaines.</p>
                    <p>Cette étape marque une avancée importante dans le processus de validation de votre commande.</p>
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
        """

    def send_mail(self, mail_server, partner, subject, body_html):
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        # email_to = f'{partner.email}, {additional_email}'
        email_to = f'{partner.email}'

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


    # mail apres payment precommande
    def send_payment_status_mail(self):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer le partenaire associé à la commande
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        # Construire le contenu de l'e-mail
        subject = 'Mise à jour de l\'état de votre paiement'

        commitment_date_start = datetime.now() + timedelta(days=30)
        commitment_date_end = datetime.now() + timedelta(days=60)
        commitment_date_start_str = commitment_date_start.strftime('%Y-%m-%d')
        commitment_date_end_str = commitment_date_end.strftime('%Y-%m-%d')

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
                            <br />
                            <br />
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    {payment_info}
                                </td>
                            </tr>
                            <br />
                            <br />
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Prix total
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {total_amount}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Somme restante à payer
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {remaining_amount}
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
                                Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''

        email_from = mail_server.smtp_user
        # email_to = partner.email
        # additional_email = 'bara.mboup@ccbm.sn'
        additional_email = 'shop@ccbm.sn'
        email_to = f'{partner.email}, {additional_email}'

        # Définir les valeurs du message e-mail
        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }
        # Construire le message e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}


    def send_credit_order_to_rh_for_confirmation(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        # Send email to HR
        parent = self.partner_id.parent_id
        rh_user = request.env['res.partner'].sudo().search([('role', '=', 'main_user'), ('parent_id', '=', parent.id)], limit=1)
        
        if rh_user:
            hr_subject = f'Nouvelle commande à crédit à valider - {self.name}'
            hr_body_html = f'''
            <p>Bonjour,</p>
            <p>Une nouvelle commande à crédit nécessite votre validation :</p>
            <ul>
                <li>Numéro de commande : {self.name}</li>
                <li>Client : {partner.name}</li>
                <li>Montant total : {self.amount_total}</li>
            </ul>
            <p>Veuillez vous connecter au système pour examiner et valider cette commande.</p>
            '''
            self.send_mail(mail_server, rh_user, hr_subject, hr_body_html)

        return {'status': 'success', 'message': 'Emails sent successfully'}

    
    # mail apres payment creditorder
    def send_payment_status_mail_creditorder(self):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer le partenaire associé à la commande
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        # Construire le contenu de l'e-mail
        subject = 'Mise à jour de l\'état de votre commande à crédit'

        commitment_date_start = datetime.now() + timedelta(days=1)
        commitment_date_end = datetime.now() + timedelta(days=3)
        commitment_date_start_str = commitment_date_start.strftime('%Y-%m-%d')
        commitment_date_end_str = commitment_date_end.strftime('%Y-%m-%d')

        payment_info = ""
        if self.first_payment_amount or self.second_payment_amount or self.third_payment_amount or self.fourth_payment_amount:
            payment_info += "<h3>Échéancier de paiement</h3>"
            payment_info += "<table border='1' cellpadding='5' cellspacing='0' width='590' style='min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;'>"
            payment_info += "<tr><th>Échéance</th><th>Montant</th><th>Date d'échéance</th><th>État</th></tr>"
            
            payments = [
                ('1ère', self.first_payment_amount, self.first_payment_date, self.first_payment_state),
                ('2ème', self.second_payment_amount, self.second_payment_date, self.second_payment_state),
                ('3ème', self.third_payment_amount, self.third_payment_date, self.third_payment_state),
                ('4ème', self.fourth_payment_amount, self.fourth_payment_date, self.fourth_payment_state)
            ]
            
            for echance, amount, date, state in payments:
                if amount:
                    payment_date = date.strftime('%Y-%m-%d') if date else "Non définie"
                    payment_state = "Payé" if state == True else "Non payé"
                    payment_info += f"<tr><td>{echance}</td><td>{amount}</td><td>{payment_date}</td><td>{payment_state}</td></tr>"
            
            payment_info += "</table>"

        total_amount = self.amount_total
        remaining_amount = self.amount_residual

        fully_paid_message = ""
        if remaining_amount == 0:
            fully_paid_message = "<p style='font-size: 16px; font-weight: bold; color: green;'>Votre commande à crédit est totalement payée.</p>"

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
                                                <span style="font-size: 10px;">Votre commande à crédit</span><br/>
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
                                                    Détails du client
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
                                                    Type de commande
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                Commande à crédit
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <br />
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
                            <br />
                            <br />
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    {payment_info}
                                </td>
                            </tr>
                            <br />
                            <br />
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                        {fully_paid_message}
                                    </td>
                                </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Prix total
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {total_amount}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 50%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Somme restante à payer
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {remaining_amount}
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
        # email_to = f'{partner.email}, {additional_email}'
        email_to = f'{partner.email}'

        # Définir les valeurs du message e-mail
        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }
        # Construire le message e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}    

    @api.model
    def action_confirm(self):
        res = super(SaleOrderMail, self).action_confirm()
        if self.type_sale == 'preorder':
            self.send_preorder_confirmation_mail()
        elif self.type_sale == 'order':
            self.send_order_confirmation_mail()
       
        return res


    @api.model
    def action_register_payment(self, payment_amount):
        res = super(SaleOrderMail, self).action_register_payment(payment_amount)
        self.send_payment_status_mail()
        return res

    @api.depends('amount_paid', 'amount_total')
    def compute_amount_residual_tracked(self):
        _logger.info("Mail envoyé pour la commande %s", self.name)
        for order in self:
            if order.type_sale == 'creditorder':
                _logger.info("Mail envoyé pour la commande %s", order.name)
                order.send_payment_status_mail_creditorder()
            
