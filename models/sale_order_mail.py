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
        # Construire le contenu de l'e-mail
        subject = 'Confirmation de votre commande'

        commitment_date = datetime.now() + timedelta(days=7)
        commitment_date_str = commitment_date.strftime('%Y-%m-%d')


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
                                                Entre le {commitment_date_str} et {(commitment_date + timedelta(days=3)).strftime('%d-%b-%Y')}
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
                                            <td style="font-weight:bold;">{self.amount_total}</td>
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

    

    def send_preorder_confirmation_mail(self):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer le partenaire associé à la commande
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        # Construire le contenu de l'e-mail
        subject = 'Confirmation de votre précommande'

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
        


    @api.model
    def action_confirm(self):
        res = super(SaleOrderMail, self).action_confirm()
        if self.type_sale == 'preorder':
            self.send_preorder_confirmation_mail()
        else:
            self.send_order_confirmation_mail()
        return res
   


    @api.model
    def action_register_payment(self, payment_amount):
        res = super(SaleOrderMail, self).action_register_payment(payment_amount)
        self.send_payment_status_mail()
        return res