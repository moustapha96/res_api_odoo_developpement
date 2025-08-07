from odoo import models, fields, api

from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class ResUsersVerif(models.Model):
    _inherit = 'res.users'

    def send_verification_mail(self, email):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer l'utilisateur associé à l'adresse e-mail
        user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
        if not user:
            return {'status': 'error', 'message': 'User not found for the given email'}

        # Construire le contenu de l'e-mail
        subject = 'Vérifiez votre compte'

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
                                                <span style="font-size: 10px;">Votre compte</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {user.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 80px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
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
                                            <td valign="top" style="font-size: 13px;">
                                                <div>
                                                    Cher {user.name},<br/><br/>
                                                    Votre compte a été créé avec succès !<br/>
                                                    Votre identifiant est <strong>{user.email}</strong><br/>
                                                    Pour accéder à votre compte, vous pouvez utiliser le lien suivant :
                                                    <div style="margin: 16px 0px 16px 0px;">
                                                        <a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="https://ccbmshop.sn/login?mail={user.email}&isVerified=1&token={user.id}">
                                                            Aller à Mon compte
                                                        </a>
                                                    </div>
                                                    Merci,<br/>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="text-align:center;">
                                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle" align="left">
                                               {user.company_id.name}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" align="left" style="opacity: 0.7;">
                                               {user.company_id.phone}
                                                | <a style="text-decoration:none; color: #454748;" href="mailto:{user.company_id.email}">{user.company_id.email}</a>
                                                |
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

        email_from = mail_server.smtp_user
        # email_to = email
        additional_email = 'shop@ccbm.sn'
        email_to = f'{email}, {additional_email}'

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
    def create(self, vals):
        user = super(ResUsersVerif, self).create(vals)
        experts_emails = [user.email]
        user.send_verification_mail(experts_emails)
        return user
