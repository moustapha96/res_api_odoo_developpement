from odoo import models, fields, api
from odoo.http import request
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    @api.model
    def send_credit_order_validation_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Validation de votre commande à crédit'
        
        today = datetime.now().date()
        premier_paiement = today + timedelta(days=3)
        dexieme_paiement = today + timedelta(days=30)
        troisieme_paiement = today + timedelta(days=60)
        quatrieme_paiement = today + timedelta(days=90)
        
        total_amount = self.amount_total
        payments = [
            ('Paiement initial', total_amount * 0.5, '50%', premier_paiement),
            ('Deuxième paiement', total_amount * 0.15, '15%', dexieme_paiement),
            ('Troisième paiement', total_amount * 0.15, '15%', troisieme_paiement),
            ('Quatrième paiement', total_amount * 0.20, '20%', quatrieme_paiement)
        ]

        payment_info = self._generate_payment_info_html(payments)
        body_html = self._generate_email_body_html(partner, 'validation', payment_info)

        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('validation')

    def send_credit_order_rejection_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Rejet de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'rejection')

        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('rejection')

    def send_credit_order_rh_rejected(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Rejet de votre commande à crédit par le service RH'
        body_html = self._generate_email_body_html(partner, 'rh_rejection')

        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('rh_rejection')

    def send_credit_order_admin_rejected(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Rejet de votre commande à crédit par l\'administration'
        body_html = self._generate_email_body_html(partner, 'admin_rejection')

        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('admin_rejection')

    def send_credit_order_admin_validation(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Validation administrative de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'admin_validation')

        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('admin_validation')

    def send_credit_order_rh_validation(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Validation RH de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'rh_validation')

        self.send_mail(mail_server, partner, subject, body_html)
        self.send_sms_notification('rh_validation')

    def send_credit_order_request_mail(self):
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
        self.send_sms_notification('request')

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
        <p>Veuillez noter que le paiement initial de 50%  apres validation par votre RH et de notre service validera complètement votre commande à crédit.</p>
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
                'title': 'Validation de votre commande à crédit',
                'content': f"""
                    <p>Félicitations {partner.name},</p>
                    <p>Votre commande à crédit numéro {self.name} a été créée avec succès.</p>
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
                    <p>Nous vous invitons à vous connecter dès maintenant à la plateforme afin d’effectuer le paiement de 50% du montant de la commande.</p>
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

    def send_credit_order_creation_notification_to_client(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return {'status': 'error', 'message': 'Mail server not configured'}

        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        subject = 'Votre commande à crédit a été créée'

        create_account_section = ""
        if not partner.password:
            create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
            create_account_section = f'''
                <tr>
                    <td align="center" style="min-width: 590px; padding-top: 20px;">
                        <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre commande à crédit :</span><br/>
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
                                            <td>
                                                <p>Cher/Chère {partner.name},</p>
                                                <p>Nous vous informons que votre commande à crédit ({self.name}) a été créée avec succès.</p>
                                                <p>Votre demande est actuellement en attente de validation par votre service des ressources humaines. Nous vous tiendrons informé de l'avancement de votre demande.</p>
                                                <p>Merci pour votre confiance.</p>
                                                <p>Cordialement,<br/>L'équipe {self.company_id.name}</p>
                                            </td>
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

        self.send_mail(mail_server, partner.email, subject, body_html)
        self.send_sms_notification('creation')

    def send_credit_order_creation_notification_to_hr(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return {'status': 'error', 'message': 'Mail server not configured'}

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
                                Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''

        self.send_mail(mail_server, self.company_id.email, subject, body_html)
        self.send_sms_notification('hr_notification')


    def send_credit_order_to_admin_for_validation(self):
        # Envoie un mail à l'administrateur pour lui informer qu'une commande à crédit a été confirmée et nécessite sa validation
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
                                                <p>Bonjour Administrateur,</p>
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
        return self.send_mail(mail_server, admin_user.partner_id, subject, body_html)
       

    def send_mail(self, mail_server, partner, subject, body_html):
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{partner.email}, {additional_email}'
        # email_to = f'{partner.email}'

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
            'request': f"Bonjour {self.partner_id.name},\nNous avons bien reçu votre demande de commande à crédit numéro {self.name} .Elle est actuellement en cours de validation par nos services.",
            'creation': f"Bonjour {self.partner_id.name},\nVotre commande à crédit numéro {self.name} a été créée avec succès. Elle est actuellement en attente de validation par votre service des ressources humaines.",
            'hr_notification': f"Bonjour,\nUne nouvelle demande de validation de commande à crédit numéro {self.name} nécessite votre validation."
        }

        message = message_templates.get(notification_type, "")
        if message:
            recipient = self.partner_id.phone
            self.env['send.sms'].create({
                'recipient': recipient,
                'message': message,
            }).send_sms()

    # @api.onchange('validation_rh_state', 'validation_admin_state')
    # def onchange_validation(self):
    #     if self.validation_rh_state == 'validated':
    #         self.send_credit_order_rh_validation()
    #     elif self.validation_rh_state == 'rejected':
    #         self.send_credit_order_rh_rejected()

    #     if self.validation_admin_state == 'validated':
    #         self.send_credit_order_admin_validation()
    #     elif self.validation_admin_state == 'rejected':
    #         self.send_credit_order_admin_rejected()

    # # envoi du mail de validation de la commande à crédit par le RH
    # @api.model
    # def send_credit_order_rh_validation(self):
    #     self.send_sms_notification('rh_validation')

    # def write(self, vals):
    #     result = super(SaleCreditOrderMail, self).write(vals)
    #     if 'validation_rh_state' in vals:
    #         if vals['validation_rh_state'] == 'validated':
    #             self.send_credit_order_rh_validation()
    #             self.send_credit_order_to_admin_for_validation()
    #         elif vals['validation_rh_state'] == 'rejected':
    #             self.send_credit_order_rh_rejected()
        
    #     if 'validation_admin_state' in vals:
    #         if vals['validation_admin_state'] == 'validated':
    #             self.send_credit_order_admin_validation()
    #         elif vals['validation_admin_state'] == 'rejected':
    #             self.send_credit_order_admin_rejected()
    #     return result
     
    @api.model
    def action_validation_rh_state(self):
        _logger.debug('action_validation_rh_state()...')
        if self.validation_rh_state == 'validated':
            self.send_credit_order_rh_validation()
        elif self.validation_rh_state == 'rejected':
            self.send_credit_order_rh_rejected()
        return True


    @api.model
    def handle_state_change(self, vals):
        """
        Cette méthode vérifie les changements d'état RH et Admin
        et envoie les notifications appropriées.
        """
        
        # Vérifie les changements d'état RH
        if 'validation_rh_state' in vals:
            new_rh_state = vals.get('validation_rh_state')
            if new_rh_state == 'validated':
                # self.send_sms_notification('rh_validation')
                self.send_credit_order_rh_validation()
              
                self.send_credit_order_to_admin_for_validation()
            elif new_rh_state == 'rejected':
                self.send_credit_order_rh_rejected()
                # self.send_sms_notification('rh_rejected')
               

        # Vérifie les changements d'état Admin
        if 'validation_admin_state' in vals:
            new_admin_state = vals.get('validation_admin_state')
            if new_admin_state == 'validated':
                self.send_credit_order_admin_validation()
                # self.send_sms_notification('admin_validation')
            elif new_admin_state == 'rejected':
                # self.send_sms_notification('admin_rejected')
                self.send_credit_order_admin_rejected()
            

        return True
    

    def write(self, vals):
        """
        Redéfinition de la méthode `write` pour gérer les notifications
        lors de changements d'état.
        """
        notifications = self.handle_state_change(vals)
        result = super(SaleCreditOrderMail, self).write(vals)
        return result

    
