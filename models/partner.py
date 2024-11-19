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
    # la fonction pour generer le code
    # @api.model
    # def create(self, vals):
    #     vals['entreprise_code'] = self.get_entreprise_code()
    #     return super(Partner, self).create(vals)
    
    # def get_entreprise_code(self):
    #     current_date = datetime.now()
    #     current_year = current_date.year
    #     current_month = current_date.month
    #     current_day = current_date.day
    #     current_time = current_date.strftime('%H%M%S')
        
    #     current_date_str = f"{current_year}{current_month:02d}{current_day:02d}"
        
    #     name_prefix = self.name[:4] if self.name else 'N/A'
        
    #     company_count = self.env['res.partner'].search_count([('is_company', '=', True)])
        
    #     return f"{name_prefix} {current_date_str}{current_time}{company_count}"

    @api.model
    def action_confirm_demande_adhesion(self):
        if self.adhesion == 'pending':
            self.adhesion_submit = True
            self.send_adhesion_request_mail()
        elif self.adhesion == 'accepted':
            self.adhesion_submit = False
            self.send_adhesion_confirmation_mail()
        elif self.adhesion == 'rejected':
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
                                                <p>Bonjour {self.name},</p>
                                                <p>Nous avons bien reçu votre demande d'adhésion à {self.company_id.name}.</p>
                                                <p>Votre demande est actuellement en cours de validation par le service RH de la société.</p>
                                                <p>Nous vous tiendrons informé de l'avancement de votre demande dans les plus brefs délais.</p>
                                                <p>Merci pour votre patience et votre intérêt pour {self.company_id.name}.</p>
                                                <p>Cordialement,</p>
                                                <p>L'équipe RH</p>
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

        self.send_mail(mail_server, subject, body_html_client, body_html_hr)

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
                                                <p>Félicitations {self.name},</p>
                                                <p>Nous avons le plaisir de vous informer que votre demande d'adhésion à {self.company_id.name} a été validée.</p>
                                                <p>Vous êtes maintenant officiellement membre de notre société. Voici ce que cela signifie pour vous :</p>
                                                <ul>
                                                    <li>Accès à tous les avantages réservés aux employés</li>
                                                    <li>Participation aux événements de l'entreprise</li>
                                                    <li>Accès à notre plateforme interne</li>
                                                </ul>
                                                <p>Notre équipe RH vous contactera prochainement pour finaliser votre intégration.</p>
                                                <p>Nous sommes ravis de vous compter parmi nous et nous vous souhaitons la bienvenue chez {self.company_id.name} !</p>
                                                <p>Cordialement,</p>
                                                <p>L'équipe RH de {self.company_id.name}</p>
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
                                                <p>Cher(e) {self.name},</p>
                                                <p>Nous avons examiné attentivement votre demande d'adhésion à {self.company_id.name}.</p>
                                                <p>Après une évaluation approfondie, nous regrettons de vous informer que votre candidature n'a pas été retenue à ce stade.</p>
                                                <p>Cette décision ne remet pas en cause vos qualités personnelles et professionnelles. Nous vous encourageons à continuer à développer vos compétences et à postuler à nouveau dans le futur si une opportunité correspondant à votre profil se présente.</p>
                                                <p>Nous vous remercions sincèrement de l'intérêt que vous avez porté à notre société et vous souhaitons le meilleur dans vos projets professionnels.</p>
                                                <p>Cordialement,</p>
                                                <p>L'équipe RH de {self.company_id.name}</p>
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

    def send_mail(self, mail_server, subject, body_html_client, body_html_hr=None):
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        
        # Envoyer l'e-mail au client
        # email_to_client = f'{self.email}, {additional_email}'
        email_to_client = f'{self.email}'
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
        
        # Envoyer l'e-mail au RH si body_html_hr est fourni
        if body_html_hr and self.email:
            # email_to_hr = f'{self.hr_email}, {additional_email}'
            email_to_hr = f'{self.email}'
            email_values_hr = {
                'email_from': email_from,
                'email_to': email_to_hr,
                'subject': subject,
                'body_html': body_html_hr,
                'state': 'outgoing',
            }
            mail_mail_hr = self.env['mail.mail'].sudo().create(email_values_hr)
            
            try:
                mail_mail_hr.send()
                _logger.info(f'Email sent successfully to HR: {self.email}')
            except Exception as e:
                _logger.error(f'Error sending email to HR: {str(e)}')

