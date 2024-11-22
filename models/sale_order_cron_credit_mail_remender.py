# from odoo import models, fields, api
# from datetime import datetime, timedelta

# class SaleOrderCronCreditMailRemender(models.Model):
#     _inherit = 'sale.order'

#     @api.model
#     def send_overdue_payment_reminders(self):
#         """
#         Envoie des rappels par e-mail pour les commandes à crédit avec des paiements en retard
#         entre `seven_days_before_now` et `today`.
#         """

#         today = fields.Date.today()
#         seven_days_before_now = today - timedelta(days=7)
#         overdue_orders = self.search([
#             ('type_sale', '=', 'creditorder'),
#             ('state', '=', 'sale'),
#             '|', '|', '|',
#             '&',
#             ('first_payment_date', '<', today),
#             ('first_payment_date', '>=', seven_days_before_now),
#             '&',
#             ('second_payment_date', '<', today),
#             ('second_payment_date', '>=', seven_days_before_now),
#             '&',
#             ('third_payment_date', '<', today),
#             ('third_payment_date', '>=', seven_days_before_now),
#             '&',
#             ('fourth_payment_date', '<', today),
#             ('fourth_payment_date', '>=', seven_days_before_now),
#         ])

#         for order in overdue_orders:
#             overdue_payments = self._get_overdue_payments(order, today)
#             if overdue_payments:
#                 self._send_overdue_payment_reminder_email(order, overdue_payments)

#     def _get_overdue_payments(self, order, today):
#         overdue_payments = []
#         payment_fields = [
#             ('first_payment_date', 'first_payment_state', 'first_payment_amount', 'Premier paiement'),
#             ('second_payment_date', 'second_payment_state', 'second_payment_amount', 'Deuxième paiement'),
#             ('third_payment_date', 'third_payment_state', 'third_payment_amount', 'Troisième paiement'),
#             ('fourth_payment_date', 'fourth_payment_state', 'fourth_payment_amount', 'Quatrième paiement'),
#         ]

#         for date_field, state_field, amount_field, payment_name in payment_fields:
#             payment_date = getattr(order, date_field)
#             payment_state = getattr(order, state_field)
#             payment_amount = getattr(order, amount_field)

#             # if payment_date and payment_date < today and not payment_state:
#             overdue_payments.append((payment_name, payment_amount, payment_date))

#         return overdue_payments

#     def _send_overdue_payment_reminder_email(self, order, overdue_payments):
#         mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#         if not mail_server:
#             return {'status': 'error', 'message': 'Mail server not configured'}

#         partner = order.partner_id
#         subject = f'Rappel de paiement en retard - Commande {order.name}'

#         overdue_payments_html = ''.join([
#             f'<tr><td>{payment[0]}</td><td>{payment[1]} {order.currency_id.name}</td><td>{payment[2].strftime("%d/%m/%Y")}</td></tr>'
#             for payment in overdue_payments
#         ])

#         body_html = f'''
#         <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
#             <tr>
#                 <td align="center">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
#                         <tbody>
#                             <!-- Header -->
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td valign="middle">
#                                                 <span style="font-size: 10px;">Rappel de paiement</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {order.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
#                                             </td>
#                                         </tr>
#                                         <tr>
#                                             <td colspan="2" style="text-align:center;">
#                                                 <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <!-- Content -->
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td>
#                                                 <p>Cher/Chère {partner.name},</p>
#                                                 <p>Nous vous rappelons que certains paiements pour votre commande à crédit {order.name} sont en retard.</p>
#                                                 <p>Voici les détails des paiements en retard :</p>
#                                                 <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
#                                                     <tr>
#                                                         <th>Échéance</th>
#                                                         <th>Montant</th>
#                                                         <th>Date d'échéance</th>
#                                                     </tr>
#                                                     {overdue_payments_html}
#                                                 </table>
#                                                 <p>Nous vous prions de bien vouloir effectuer le paiement dès que possible pour régulariser votre situation.</p>
#                                                 <p>Si vous avez déjà effectué le paiement, veuillez ignorer ce message.</p>
#                                                 <p>Pour toute question, n'hésitez pas à nous contacter.</p>
#                                                 <p>Cordialement,<br/>L'équipe {order.company_id.name}</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <!-- Footer -->
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td style="text-align: center; font-size: 13px;">
#                                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         self._send_mail(mail_server, partner, subject, body_html)

#     def _send_mail(self, mail_server, partner, subject, body_html):
#         email_from = mail_server.smtp_user
#         email_to = partner.email

#         email_values = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'subject': subject,
#             'body_html': body_html,
#             'state': 'outgoing',
#         }

#         mail_mail = self.env['mail.mail'].sudo().create(email_values)
#         try:
#             mail_mail.send()
#             return {'status': 'success', 'message': 'Mail envoyé avec succès'}
#         except Exception as e:
#             return {'status': 'error', 'message': str(e)}

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class SaleOrderCronCreditMailReminder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def send_overdue_payment_reminders(self):
        """
        Envoie des rappels par e-mail pour les commandes à crédit avec des paiements prévus
        entre aujourd'hui et 7 jours avant la date d'échéance.
        """
        today = fields.Date.today()
        reminder_date_limit = today - timedelta(days=7)

        # Recherche des commandes à crédit avec des paiements attendus dans 7 jours
        overdue_orders = self.search([
            ('type_sale', '=', 'creditorder'),
            ('state', '=', 'sale'),
            '|', '|', '|',
            '&', ('first_payment_date', '>=', reminder_date_limit), ('first_payment_date', '<=', today),
            '&', ('second_payment_date', '>=', reminder_date_limit), ('second_payment_date', '<=', today),
            '&', ('third_payment_date', '>=', reminder_date_limit), ('third_payment_date', '<=', today),
            '&', ('fourth_payment_date', '>=', reminder_date_limit), ('fourth_payment_date', '<=', today),
        ])

        _logger.info(f"Commandes trouvées pour rappels (paiements attendus le {today}): {len(overdue_orders)}")

        for order in overdue_orders:
            overdue_payments = self._get_overdue_payments(order, today)
            if overdue_payments:
                self._send_overdue_payment_reminder_email(order, overdue_payments)

    def _get_overdue_payments(self, order, today):
        """
        Récupère les paiements en retard pour une commande donnée.
        """
        overdue_payments = []
        payment_fields = [
            ('first_payment_date', 'first_payment_state', 'first_payment_amount', 'Premier paiement'),
            ('second_payment_date', 'second_payment_state', 'second_payment_amount', 'Deuxième paiement'),
            ('third_payment_date', 'third_payment_state', 'third_payment_amount', 'Troisième paiement'),
            ('fourth_payment_date', 'fourth_payment_state', 'fourth_payment_amount', 'Quatrième paiement'),
        ]

        for date_field, state_field, amount_field, payment_name in payment_fields:
            payment_date = getattr(order, date_field)
            payment_state = getattr(order, state_field)
            payment_amount = getattr(order, amount_field)

            if payment_date and payment_date <= today and payment_date >= today - timedelta(days=7) and not payment_state:
                overdue_payments.append((payment_name, payment_amount, payment_date))

        return overdue_payments

    def _send_overdue_payment_reminder_email(self, order, overdue_payments):
        """
        Envoie un e-mail de rappel pour les paiements en retard.
        """
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            _logger.error('Mail server not configured')
            return {'status': 'error', 'message': 'Mail server not configured'}

        partner = order.partner_id
        subject = f'Rappel de paiement en retard - Commande {order.name}'

        overdue_payments_html = ''.join([
            f'<tr><td>{payment[0]}</td><td>{payment[1]} {order.currency_id.name}</td><td>{payment[2].strftime("%d/%m/%Y")}</td></tr>'
            for payment in overdue_payments
        ])

        body_html = self._generate_email_body(order, partner, overdue_payments_html)

        self._send_mail(mail_server, partner, subject, body_html)

    def _generate_email_body(self, order, partner, overdue_payments_html):
        """
        Génère le corps de l'e-mail de rappel.
        """
        return f'''
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
                        <tbody>
                            <!-- Header -->
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle">
                                                <span style="font-size: 10px;">Rappel de paiement</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {order.name}
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
                            <!-- Content -->
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td>
                                                <p>Cher/Chère {partner.name},</p>
                                                <p>Nous vous rappelons que certains paiements pour votre commande à crédit {order.name} sont en retard.</p>
                                                <p>Voici les détails des paiements en retard :</p>
                                                <table border="1" cellpadding="5" cellspacing="0" style="width: 100%;">
                                                    <tr>
                                                        <th>Échéance</th>
                                                        <th>Montant</th>
                                                        <th>Date d'échéance</th>
                                                    </tr>
                                                    {overdue_payments_html}
                                                </table>
                                                <p>Nous vous prions de bien vouloir effectuer le paiement dès que possible pour régulariser votre situation.</p>
                                                <p>Si vous avez déjà effectué le paiement, veuillez ignorer ce message.</p>
                                                <p>Pour toute question, n'hésitez pas à nous contacter.</p>
                                                <p>Cordialement,<br/>L'équipe {order.company_id.name}</p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <!-- Footer -->
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
                        </tbody>
                    </table>
                </td>
            </tr>
        </table>
        '''

    def _send_mail(self, mail_server, partner, subject, body_html):
        """
        Envoie un e-mail via le serveur de messagerie configuré.
        """
        email_from = mail_server.smtp_user
        email_to = partner.email

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
            _logger.info(f'Mail envoyé avec succès à {email_to}')
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Erreur lors de l\'envoi du mail à {email_to}: {str(e)}')
            return {'status': 'error', 'message': str(e)}
