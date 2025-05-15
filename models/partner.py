from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import logging
from datetime import datetime, timedelta
import base64
_logger = logging.getLogger(__name__)
class Partner(models.Model):
    _inherit = 'res.partner'

    password = fields.Char(string='Mot de passe de connexion sur la partie web',widget='password', required=False)
    is_verified = fields.Boolean(string='Etat verification compte mail', default=False)
    avatar = fields.Char(string='Photo profil Client', required=False)
    role = fields.Selection([
        ('main_user', 'Utilisateur Principal'),
        ('secondary_user', 'Utilisateur Secondaire')
    ], string='Rôle', default='secondary_user')
    adhesion = fields.Selection([
        ('pending', 'En cours de validation'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté')
    ], string='Adhésion', default='pending')
    adhesion_submit = fields.Boolean(string="Etat demande d'adhésion", default=False)

    entreprise_code = fields.Char(string='Code entreprise', required=False)

   
    @api.model_create_multi
    def create(self, vals_list):
        """ Méthode pour générer un code unique basé sur le nom, la date de création et le rang de l'entreprise """

        for vals in vals_list:
            if vals.get('is_company', None):
                code_date_creation = datetime.now().strftime('%d%m%Y')
                code_number = self.search_count([('is_company', '=', True)]) + 1
                code_name = str(vals.get('name')[0:4]).upper()
                vals['entreprise_code'] = f"{code_name}{code_date_creation}{code_number}"

                return super(Partner, self).create(vals)
            else:
                return super(Partner, self).create(vals)

    @api.model
    def action_confirm_demande_adhesion(self, state):
        # find partner with entreprise_code
        if state == 'pending':
            self.adhesion_submit = True
            self.send_adhesion_request_mail()
            self.send_demande_to_rh()
        elif state == 'accepted':
            self.adhesion_submit = False
            self.send_adhesion_confirmation_mail()
        elif state == 'rejected':
            self.adhesion_submit = False
            self.send_adhesion_rejection_mail()
        
        return True


    def send_adhesion_request_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        subject = f'Nouvelle demande d\'adhésion - {self.name}'
        body_html_client = f'''
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
                                                <span style="font-size: 10px;">Votre demande d'adhésion</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    En cours de traitement
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
                                                <p>Bonjour {self.name},</p>
                                                <p>Nous avons bien reçu votre demande d'adhésion à {self.parent_id.name}.</p>
                                                <p>Votre demande est actuellement en cours de validation par le service RH de la société.</p>
                                               
                                                <p>Cordialement,</p>
                                                <p>L'équipe CCBM Shop</p>
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

        body_html_hr = f'''
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
                                                <span style="font-size: 10px;">Nouvelle demande d'adhésion</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    À valider
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
                                                <p>Une nouvelle demande d'adhésion a été soumise et nécessite votre validation :</p>
                                                <ul>
                                                    <li>Nom : {self.name}</li>
                                                    <li>Email : {self.email}</li>
                                                    
                                                </ul>
                                                <p>Veuillez examiner cette demande .</p>
                                                <p>Cordialement,</p>
                                                <p>Le système CCBM SHOP</p>
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

        self.send_mail(mail_server, subject, body_html_client)

    def send_demande_to_rh(self):

        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        parent = self.parent_id
        # find all partner where role = "main_user " and parent_id.id  = parent.id
        rh_user = request.env['res.partner'].sudo().search([('role', '=', 'main_user'), ('parent_id', '=', parent.id) ] , limit=1)

        _logger.info(f"rh users {rh_user} ,  {rh_user.email}")
        subject = "Nouvelle demande d'adhésion"

        body_html_hr = f'''
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
                                                <span style="font-size: 10px;">Nouvelle demande d'adhésion</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    À valider
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
                                                <p>Une nouvelle demande d'adhésion a été soumise et nécessite votre validation :</p>
                                                <ul>
                                                    <li>Nom : {self.name}</li>
                                                    <li>Email : {self.email}</li>
                                                    <li>Société : {self.company_id.name}</li>
                                                </ul>
                                                <p>Veuillez examiner cette demande et prendre les mesures appropriées.</p>
                                                <p>Cordialement,</p>
                                                <p>Le système CCBM SHOP</p>
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

        additional_email = 'shop@ccbm.sn'
        email_to_client = f'{rh_user.email}, {additional_email}'
        email_values_client = {
            'email_from':  mail_server.smtp_user,
            'email_to': email_to_client,
            'subject': subject,
            'body_html': body_html_hr,
            'state': 'outgoing',
        }
        mail_mail_client = self.env['mail.mail'].sudo().create(email_values_client)
        
        try:
            mail_mail_client.send()
            _logger.info(f'Email sent successfully to rh: {self.email}')
        except Exception as e:
            _logger.error(f'Error sending email to rh: {str(e)}')

    def send_adhesion_confirmation_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        subject = f'Confirmation d\'adhésion - {self.name}'
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
                                                <span style="font-size: 10px;">Votre demande d'adhésion</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    Validée
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
                                                <p>Félicitations {self.name},</p>
                                                <p>Nous avons le plaisir de vous informer que votre demande d'adhésion à {self.parent_id.name} a été validée.</p>
                                               
                                               
                                                <p>Nous sommes ravis de vous compter parmi nous et nous vous souhaitons la bienvenue chez {self.parent_id.name} !</p>
                                                <p>Cordialement,</p>
                                                <p>L'équipe CCBM Shop</p>
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

        self.send_mail(mail_server, subject, body_html)

    def send_adhesion_rejection_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))

        subject = f'Réponse à votre demande d\'adhésion - {self.name}'
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
                                                <span style="font-size: 10px;">Votre demande d'adhésion</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    Réponse
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
                                                <p>Cher(e) {self.name},</p>
                                                <p>Nous avons examiné attentivement votre demande d'adhésion à {self.parent_id.name}.</p>
                                                <p>Après une évaluation approfondie, nous regrettons de vous informer que votre candidature n'a pas été retenue à ce stade.</p>
                                                <p>Cordialement,</p>
                                                <p>L'équipe CCBM Shop</p>
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

        self.send_mail(mail_server, subject, body_html)

    def send_mail(self,   mail_server, subject, body_html_client, body_html_hr=None):
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        
        # Envoyer l'e-mail au client
        email_to_client = f'{self.email}, {additional_email}'
        email_values_client = {
            'email_from': email_from,
            'email_to': email_to_client,
            'subject': subject,
            'body_html': body_html_client,
            'state': 'outgoing',
        }
        mail_mail_client = self.env['mail.mail'].sudo().create(email_values_client)
        
        try:
            mail_mail_client.send()
            _logger.info(f'Email sent successfully to client: {self.email}')
        except Exception as e:
            _logger.error(f'Error sending email to client: {str(e)}')
        
    def send_mail_create_account(self, partner, password):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))
        
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        
        subject = 'Votre compte CCBM SHOP'
        body_html_client = f'''
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
            <tr>
                <td align="center" style="min-width: 590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                        <tr>
                            <td align="center" style="min-width: 590px;">
                                <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                    <tr>
                                        <td>
                                            <p>Cher(e) {partner.name},</p>
                                            <p>Votre compte a bien créé un compte sur CCBM SHOP.</p>
                                            <p>Voici vos identifiants de connexion:</p>
                                            <p>Identifiant: {partner.email}</p>
                                            <p>Mot de passe: {password}</p>
                                            <p>Cordialement,</p>
                                            <p>L'équipe CCBM Shop</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
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


        email_to_client = f'{partner.email}, {additional_email}'
        email_values_client = {
            'email_from': email_from,
            'email_to': email_to_client,
            'subject': subject,
            'body_html': body_html_client,
            'state': 'outgoing',
        }
        mail_mail_client = self.env['mail.mail'].sudo().create(email_values_client)
        
        try:
            mail_mail_client.send()
            _logger.info(f'Email sent successfully to client: {self.email}')
        except Exception as e:
            _logger.error(f'Error sending email to client: {str(e)}')
        pass 
