# from odoo import models, fields, api
# from datetime import datetime
# import logging

# _logger = logging.getLogger(__name__)


# class SaleCreditOrderMail(models.Model):
#     _inherit = 'sale.order'

#     def send_payment_reminder(self):
#         """
#         Parcourt les paiements échus et envoie les notifications (e-mail + SMS).
#         """
#         today = datetime.now().date()
#         overdue_payments = self._get_overdue_payments(today)

#         for payment in overdue_payments:
#             self._notify_overdue_payment(payment)

#     def _get_overdue_payments(self, today):
#         """
#         Récupère les lignes de paiements échus pour la commande.
#         :param today: date actuelle
#         :return: liste des paiements échus sous forme de dictionnaires
#         """
#         overdue = []
#         payments = self._generate_payments(today)

#         for payment in payments:
#             label, amount, state, rate, due_date = payment
#             if not state and due_date < today and amount > 0:
#                 _logger.info(f"[ÉCHU] {label} | Montant: {amount} | Date: {due_date}")
#                 overdue.append({
#                     'label': label,
#                     'amount': amount,
#                     'due_date': due_date,
#                 })
#         return overdue

#     def _notify_overdue_payment(self, payment):
#         """
#         Envoie une notification (e-mail + SMS) pour un paiement échu donné.
#         """
#         partner = self.partner_id
#         if not partner:
#             _logger.warning(f"[ERREUR] Aucun partenaire trouvé pour la commande {self.name}")
#             return

#         subject = f'🔔 Rappel : Paiement en retard - {payment["label"]}'
      
#         body_html = f"""
#             <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f4; padding: 20px;">
#              <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td valign="middle">
#                                                 <span style="font-size: 10px;">Commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                 <tr>
#                     <td align="center">
#                         <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; padding: 30px; border-radius: 6px;">
#                             <tr>
#                                 <td align="center" style="font-size: 22px; font-weight: bold; padding-bottom: 20px; color: #dc3545;">
#                                     ⚠️ Rappel de paiement échu
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 16px; color: #333333; padding-bottom: 10px;">
#                                     Bonjour {partner.name},
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 15px;">
#                                     Nous vous informons que le paiement de <strong>{payment['amount']} {self.currency_id.name}</strong>,
#                                     prévu le <strong>{payment['due_date']}</strong>, est <span style="color: red; font-weight: bold;">en retard</span>.
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 20px;">
#                                     Voici les détails de la commande concernée :
#                                     <ul style="margin-top: 10px; margin-bottom: 10px; padding-left: 20px; color: #444;">
#                                         <li><strong>Référence :</strong> {self.name}</li>
#                                         <li><strong>Date de commande :</strong> {self.date_order.strftime('%d/%m/%Y')}</li>
#                                         <li><strong>Montant total :</strong> {self.amount_total:,.0f} {self.currency_id.name}</li>
#                                     </ul>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 15px;">
#                                     Merci de bien vouloir régulariser votre situation dans les plus brefs délais afin d’éviter toute interruption ou pénalité éventuelle.
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="padding-bottom: 30px;">
#                                     <a href="https://www.ccbmshop.sn/login" style="display: inline-block; background-color: #007bff; color: #ffffff; text-decoration: none; padding: 12px 25px; font-size: 15px; border-radius: 5px;">
#                                         Connectez vous maintenant
#                                     </a>
#                                 </td>
#                             </tr>
                           
#                         </table>
#                     </td>
#                 </tr>

#                 <!-- Footer CCBM -->
#                  <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                             <td colspan="2" style="padding: 12px; text-align: center;">
#                                 <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                                 <p> <a href="https://ccbmshop.sn" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                             </td>
#                         </tr>
#             </table>
#             """


#         mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#         self.send_mail(mail_server, partner, subject, body_html)

#         if partner.phone:
#             sms_msg = (
#                 f"Bonjour {partner.name}, votre paiement de {payment['amount']} {self.currency_id.name} "
#                 f"(commande {self.name}, échéance {payment['due_date']}) est en retard. "
#                 f"Merci de régulariser au plus vite.\n{self.company_id.name}"
#             )

#             self.env['send.sms'].create({
#                 'recipient': partner.phone,
#                 'message': sms_msg,
#             }).send_sms()
#         else:
#             _logger.warning(f"[SMS NON ENVOYÉ] Numéro manquant pour {partner.name}")

#     def _generate_payments(self, today):
#         """
#         Génère une liste des échéances de paiement à partir de la méthode `get_sale_order_credit_payment`.
#         :param today: date du jour
#         :return: liste de tuples (label, montant, état, taux, date d'échéance)
#         """
#         payments = []
#         payment_lines = self.get_sale_order_credit_payment()

#         for line in sorted(payment_lines, key=lambda x: x['sequence']):
#             due_date = line['due_date']
#             if isinstance(due_date, str):
#                 due_date = datetime.fromisoformat(due_date).date()

#             label = "Premier Paiement (Acompte)" if line['sequence'] == 1 else f"Échéance {line['sequence']}"
#             payments.append((
#                 label,
#                 line['amount'],
#                 line['state'],
#                 f"{line['rate']:.1f}%",
#                 due_date
#             ))

#         return payments


#     def send_mail(self, mail_server, partner, subject, body_html):
        
#         if not mail_server:
#             _logger.error('Mail server not configured')
#             return {'status': 'error', 'message': 'Mail server not configured'}

#         email_from = mail_server.smtp_user
#         additional_email = 'shop@ccbm.sn'
#         email_to = None

#         if hasattr(partner, 'email') and partner.email:
#             email_to = f'{partner.email}, {additional_email}'
#         else:
#             _logger.error(f'Partner email not found for partner: {partner.name}')
#             return {'status': 'error', 'message': 'Partner email not found'}

#         email_values = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'subject': subject,
#             'body_html': body_html,
#             'state': 'outgoing',
#         }
#         # return True
#         mail_mail = self.env['mail.mail'].sudo().create(email_values)
#         try:
#             mail_mail.send()
#             return {'status': 'success', 'message': 'Mail envoyé avec succès'}
#         except Exception as e:
#             _logger.error(f'Error sending email: {str(e)}')
#             return {'status': 'error', 'message': str(e)}

   

#     def check_overdue_payments_cron(self):
#         """
#         Méthode appelée par la tâche cron pour vérifier les paiements échus.
#         """
#         _logger.info("[CRON] Démarrage du cron de notifications pour commandes à crédit")

#         orders = self.search([('type_sale', '=', 'creditorder')])
#         _logger.info(f"[CRON] Commandes à traiter : {len(orders)}")

#         for order in orders:
#             if order.state == "draft" or order.state == "cancel" :
#                 _logger.info(f"[CRON] Traitement de la commande {order.name} pour {order.partner_id.name} annulée ou en brouliion ")

#             if order.state == "to_delivered" or order.state == "delivered" or order.state == "sale" :
#                 _logger.info(f"[CRON] Traitement de la commande {order.name} pour {order.partner_id.name}")
#                 order.send_payment_reminder()
            


#     def check_and_send_overdue_payments(self):
#         """
#         Vérifie et envoie les notifications de paiements échus pour toutes les commandes.
#         """
#         for order in self.search([]):
#             order.send_payment_reminder()

from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    def send_payment_reminder(self):
        """
        Parcourt les paiements échus et envoie les notifications (e-mail + SMS).
        Ne traite que les paiements réellement échus (non payés, date passée, montant > 0).
        """
        today = datetime.now().date()
        overdue_payments = self._get_overdue_payments(today)

        if not overdue_payments:
            _logger.debug(f"[AUCUN PAIEMENT ÉCHU] Commande {self.name} - Aucun paiement échu à notifier")
            return

        _logger.info(f"[NOTIFICATION] Commande {self.name} - {len(overdue_payments)} paiement(s) échu(s) à notifier")
        for payment in overdue_payments:
            self._notify_overdue_payment(payment)

    def _get_overdue_payments(self, today):
        """
        Récupère les lignes de paiements échus pour la commande.
        :param today: date actuelle
        :return: liste des paiements échus sous forme de dictionnaires
        """
        overdue = []
        payments = self._generate_payments(today)

        for payment in payments:
            label, amount, state, rate, due_date = payment
            
            # Vérifier que le paiement est échu : non payé (not state), date passée, montant > 0
            if not state and due_date < today and amount > 0:
                _logger.info(f"[ÉCHU] {label} | Montant: {amount} | Date: {due_date} | État: Non payé")
                overdue.append({
                    'label': label,
                    'amount': amount,
                    'due_date': due_date,
                })
            else:
                if state:
                    _logger.debug(f"[IGNORÉ] {label} | État: Payé")
                elif due_date >= today:
                    _logger.debug(f"[IGNORÉ] {label} | Date: {due_date} (pas encore échu)")
                elif amount <= 0:
                    _logger.debug(f"[IGNORÉ] {label} | Montant: {amount} (montant nul ou négatif)")
        return overdue

    def _notify_overdue_payment(self, payment):
        """
        Envoie une notification (e-mail + SMS) pour un paiement échu donné.
        """
        # Vérification supplémentaire : s'assurer que le paiement est toujours échu
        today = datetime.now().date()
        due_date = payment.get('due_date')
        
        # Convertir due_date en date si c'est une string
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()
        
        # Ne pas envoyer si l'échéance n'est pas encore passée
        if due_date >= today:
            _logger.info(f"[IGNORÉ] Paiement {payment.get('label')} pas encore échu (échéance: {due_date})")
            return
        
        # Vérifier que le montant est supérieur à 0
        if payment.get('amount', 0) <= 0:
            _logger.info(f"[IGNORÉ] Paiement {payment.get('label')} avec montant nul ou négatif")
            return
        
        partner = self.partner_id
        if not partner:
            _logger.warning(f"[ERREUR] Aucun partenaire trouvé pour la commande {self.name}")
            return

        # Formater la date d'échéance pour l'affichage
        due_date_str = due_date.strftime('%d/%m/%Y') if hasattr(due_date, 'strftime') else str(due_date)

        subject = f'🔔 Rappel : Paiement en retard - {payment["label"]}'
      
        body_html = f"""
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f4; padding: 20px;">
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
                    <td align="center">
                        <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; padding: 30px; border-radius: 6px;">
                            <tr>
                                <td align="center" style="font-size: 22px; font-weight: bold; padding-bottom: 20px; color: #dc3545;">
                                    ⚠️ Rappel de paiement échu
                                </td>
                            </tr>
                            <tr>
                                <td style="font-size: 16px; color: #333333; padding-bottom: 10px;">
                                    Bonjour {partner.name},
                                </td>
                            </tr>
                            <tr>
                                <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 15px;">
                                    Nous vous informons que le paiement de <strong>{payment['amount']} {self.currency_id.name}</strong>,
                                    prévu le <strong>{due_date_str}</strong>, est <span style="color: red; font-weight: bold;">en retard</span>.
                                </td>
                            </tr>
                            <tr>
                                <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 20px;">
                                    Voici les détails de la commande concernée :
                                    <ul style="margin-top: 10px; margin-bottom: 10px; padding-left: 20px; color: #444;">
                                        <li><strong>Référence :</strong> {self.name}</li>
                                        <li><strong>Date de commande :</strong> {self.date_order.strftime('%d/%m/%Y')}</li>
                                        <li><strong>Montant total :</strong> {self.amount_total:,.0f} {self.currency_id.name}</li>
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 15px;">
                                    Merci de bien vouloir régulariser votre situation dans les plus brefs délais afin d’éviter toute interruption ou pénalité éventuelle.
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="padding-bottom: 30px;">
                                    <a href="https://www.ccbmshop.sn/login" style="display: inline-block; background-color: #007bff; color: #ffffff; text-decoration: none; padding: 12px 25px; font-size: 15px; border-radius: 5px;">
                                        Connectez vous maintenant
                                    </a>
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
            """


        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        mail_result = self.send_mail(mail_server, partner, subject, body_html)
        
        if mail_result.get('status') == 'success':
            _logger.info(f"[MAIL ENVOYÉ] Commande {self.name} - Paiement {payment['label']} échu notifié à {partner.email}")
        else:
            _logger.error(f"[MAIL ÉCHOUÉ] Commande {self.name} - Erreur: {mail_result.get('message', 'Unknown error')}")

        if partner.phone:
            sms_msg = (
                f"Bonjour {partner.name}, votre paiement de {payment['amount']} {self.currency_id.name} "
                f"(commande {self.name}, échéance {due_date_str}) est en retard. "
                f"Merci de régulariser au plus vite.\n{self.company_id.name}"
            )

            try:
                self.env['send.sms'].create({
                    'recipient': partner.phone,
                    'message': sms_msg,
                }).send_sms()
                _logger.info(f"[SMS ENVOYÉ] Commande {self.name} - Paiement {payment['label']} échu notifié au {partner.phone}")
            except Exception as e:
                _logger.error(f"[SMS ÉCHOUÉ] Commande {self.name} - Erreur: {str(e)}")
        else:
            _logger.warning(f"[SMS NON ENVOYÉ] Numéro manquant pour {partner.name} (commande {self.name})")

    def _generate_payments(self, today):
        """
        Génère une liste des échéances de paiement à partir de la méthode `get_sale_order_credit_payment`.
        :param today: date du jour
        :return: liste de tuples (label, montant, état, taux, date d'échéance)
        """
        payments = []
        payment_lines = self.get_sale_order_credit_payment()

        for line in sorted(payment_lines, key=lambda x: x['sequence']):
            due_date = line['due_date']
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date).date()

            label = "Premier Paiement (Acompte)" if line['sequence'] == 1 else f"Échéance {line['sequence']}"
            payments.append((
                label,
                line['amount'],
                line['state'],
                f"{line['rate']:.1f}%",
                due_date
            ))

        return payments


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
        # return True
        mail_mail = self.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

   

    def check_overdue_payments_cron(self):
        """
        Méthode appelée par la tâche cron pour vérifier les paiements échus.
        Ne traite que les commandes valides (confirmées, livrées ou en cours de livraison).
        """
        _logger.info("[CRON] Démarrage du cron de notifications pour commandes à crédit")

        orders = self.search([('type_sale', '=', 'creditorder')])
        _logger.info(f"[CRON] Commandes trouvées : {len(orders)}")

        processed_count = 0
        skipped_count = 0
        
        for order in orders:
            # Ignorer les commandes en brouillon ou annulées
            if order.state == "draft" or order.state == "cancel":
                _logger.debug(f"[CRON] Commande {order.name} ignorée (état: {order.state})")
                skipped_count += 1
                continue

            # Traiter uniquement les commandes confirmées, livrées ou en cours de livraison
            if order.state in ("to_delivered", "delivered", "sale"):
                _logger.info(f"[CRON] Traitement de la commande {order.name} pour {order.partner_id.name} (état: {order.state})")
                order.send_payment_reminder()
                processed_count += 1
            else:
                _logger.debug(f"[CRON] Commande {order.name} ignorée (état non traité: {order.state})")
                skipped_count += 1
        
        _logger.info(f"[CRON] Terminé - Traitées: {processed_count}, Ignorées: {skipped_count}")
            


    def check_and_send_overdue_payments(self):
        """
        Vérifie et envoie les notifications de paiements échus pour toutes les commandes.
        Ne traite que les commandes à crédit valides avec des paiements réellement échus.
        """
        orders = self.search([('type_sale', '=', 'creditorder')])
        _logger.info(f"[MANUEL] Vérification de {len(orders)} commande(s) à crédit")
        
        for order in orders:
            # Ignorer les commandes en brouillon ou annulées
            if order.state in ("draft", "cancel"):
                continue
            
            # Traiter uniquement les commandes valides
            if order.state in ("to_delivered", "delivered", "sale"):
                order.send_payment_reminder()
