from odoo import models, fields, api
from odoo.http import request
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AccountPaymentPreorder(models.Model):
    _inherit = 'account.payment'

    # mail après paiement précommande
    def send_payment_status_mail(self):
        order = self.sale_id
        if order:
            # Récupérer ou créer une instance de IrMailServer
            mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

            # Récupérer le partenaire associé à la commande
            partner = order.partner_id
            if not partner:
                return {'status': 'error', 'message': 'Partner not found for the given order'}

            # Construire le contenu de l'e-mail
            subject = 'Mise à jour de l\'état de votre paiement'

            commitment_date_start = datetime.now() + timedelta(days=30)
            commitment_date_end = datetime.now() + timedelta(days=60)
            commitment_date_start_str = commitment_date_start.strftime('%Y-%m-%d')
            commitment_date_end_str = commitment_date_end.strftime('%Y-%m-%d')

            payment_info = ""
            if order.first_payment_amount or order.second_payment_amount or order.third_payment_amount:
                payment_info += "<h3>Informations de paiement</h3>"
                payment_info += "<table border='1' cellpadding='5' cellspacing='0' width='590' style='min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;'>"
                payment_info += "<tr><th>Montant</th><th>Date d'échéance</th><th>État</th></tr>"
                if order.first_payment_amount:
                    first_payment_date = order.first_payment_date.isoformat() if order.first_payment_date else "Non définie"
                    first_payment_state = "Payé" if order.first_payment_state == True else "Non payé"
                    payment_info += f"<tr><td>{order.first_payment_amount}</td><td>{first_payment_date}</td><td>{first_payment_state}</td></tr>"
                if order.second_payment_amount:
                    second_payment_date = order.second_payment_date.isoformat() if order.second_payment_date else "Non définie"
                    second_payment_state = "Payé" if order.second_payment_state == True else "Non payé"
                    payment_info += f"<tr><td>{order.second_payment_amount}</td><td>{second_payment_date}</td><td>{second_payment_state}</td></tr>"
                if order.third_payment_amount:
                    third_payment_date = order.third_payment_date.isoformat() if order.third_payment_date else "Non définie"
                    third_payment_state = "Payé" if order.third_payment_state == True else "Non payé"
                    payment_info += f"<tr><td>{order.third_payment_amount}</td><td>{third_payment_date}</td><td>{third_payment_state}</td></tr>"
                payment_info += "</table>"

            total_amount = order.amount_total
            remaining_amount = order.amount_residual

            order_lines = order.order_line.filtered(lambda line: not line.is_downpayment)

            # Message indiquant que la précommande est totalement payée
            fully_paid_message = ""
            if remaining_amount == 0:
                fully_paid_message = "<p style='font-size: 16px; font-weight: bold; color: green;'>Votre précommande est totalement payée.</p>"

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
                                                        {order.name}
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
                                            {"".join([f"<tr><td>{line.product_id.name}</td><td>{line.product_uom_qty}</td><td>{line.price_unit}</td><td>{line.price_total}</td></tr>" for line in order_lines])}
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
                                <br />
                                <br />
                                <tr>
                                    <td align="center" style="min-width: 590px;">
                                        {fully_paid_message}
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

            email_from = mail_server.smtp_user
            # email_to = partner.email
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
        else:
            return {'status': 'error', 'message': 'User not found for the given email'}



    # @api.model
    def action_post(self):
        res = super(AccountPaymentPreorder, self).action_post()
        if self.sale_id.type_sale == 'preorder':
            self.send_payment_status_mail()
        elif self.sale_id.type_sale == 'creditorder':
            self.sale_id.send_payment_status_mail_creditorder()
        return res
