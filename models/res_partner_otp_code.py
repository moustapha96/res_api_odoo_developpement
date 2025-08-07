from odoo import models, fields, api
from datetime import datetime, timedelta
import random

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    otp_verified = fields.Boolean(string='OTP vérification', default=False)
    otp_code_ids = fields.One2many('otp.code', 'partner_id', string="Codes OTP")



    # ajoute pour voir le code
    def get_otp(self):
        for partner in self:
            code_existant = self.env['otp.code'].search([('partner_id', '=', partner.id)], limit=1)
            if code_existant:
                return code_existant.code
            
            if partner.phone:
                # otp_code = ''.join(random.choices('0123456789', k=4))  # Génération d'un OTP aléatoire
                # expiration = datetime.now() + timedelta(minutes=30)
                otp_code  = self._generate_otp(partner)

                # self.env['otp.code'].create({
                #     'partner_id': partner.id,
                #     'code': otp_code,
                #     'expiration': expiration,
                # })

                # Envoi du SMS avec le code OTP
                return otp_code

    def send_otp(self):
        for partner in self:
 
            if partner.phone:
                otp_code = self._generate_otp(partner)

                message = (
                    f"Bonjour ,\n"
                    f"Votre code de vérification est {otp_code}\n"
                    f"Merci de ne pas répondre à ce message.\n"
                    f"Equipe de CCBM Shop"
                )
              

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
                                                            <span style="font-size: 10px;">Vérification de votre compte</span><br/>
                                                            
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
                                                                Cher {partner.name},<br/><br/>
                                                                Voici votre code de vérification OTP pour vérifier votre compte :<br/>
                                                                <div style="margin: 16px 0px; text-align: center; font-size: 24px; font-weight: bold; background: #f3f3f3; padding: 10px; border-radius: 5px;">
                                                                    {otp_code}
                                                                </div>
                                                                Ce code est valable pour une durée limitée. Ne le partagez avec personne.<br/><br/>
                                                                Vous pouvez aussi cliquer sur le bouton ci-dessous pour accéder directement à la page de vérification et entrer votre code :
                                                                <div style="margin: 16px 0px; text-align: center;">
                                                                    <a style="background-color: #875A7B; padding: 10px 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size:14px;" 
                                                                        href="http://ccbme.sn/verification-code?email={partner.email}">
                                                                        Vérifier mon compte
                                                                    </a>
                                                                </div>
                                                                
                                                                Ce code est valable pour une durée limitée. Ne le partagez avec personne.<br/><br/>
                                                                Merci,<br/>
                                                                <strong>{partner.company_id.name}</strong>
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
                                                        {partner.company_id.name}
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td valign="middle" align="left" style="opacity: 0.7;">
                                                        {partner.company_id.phone}
                                                            | <a style="text-decoration:none; color: #454748;" href="mailto:{partner.company_id.email}">{partner.company_id.email}</a>
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
                                            Généré par <a target="_blank" href="https://www.ccbmshop.sn" style="color: #875A7B;">CCBM Shop</a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    '''

                # Envoi du SMS avec le code OTP
                self.send_sms(partner.phone, message)

                self.send_email(partner.email, 'Code de vérification', body_html)

                return otp_code

    def verify_otp(self, otp_code):
        """ Vérifie si l'OTP est correct et encore valide """
        otp_record = self.env['otp.code'].search([
            ('partner_id', '=', self.id),
            ('code', '=', otp_code),
            ('expiration', '>', fields.Datetime.now())  # Vérification que l'OTP n'est pas expiré
        ], limit=1)

        if otp_record:
            self.write({'otp_verified': True})
            otp_record.unlink()  # Suppression de l'OTP après validation
            return True
        return False

    @api.model
    def send_sms(self, recipient, message):
        """ Envoie un SMS via le modèle `send.sms` """
        # result = self.env['send.sms'].sudo().send_sms(recipient, message)
        result = self.env['send.sms'].create({
                'recipient': recipient,
                'message': message,
            }).send_sms()

        return result
    
    @api.model
    def send_email(self, recipient, subject, body):
        """ Envoie un email via le modèle `send.email` """
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
      
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        # email_to = f'{recipient},{additional_email}'
        email_to = f'{recipient}'
        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body,
            'state': 'outgoing',
        }
        mail_mail = self.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return True
        except Exception as e:
            return True

    def _generate_otp(self, partner):
        otp_code = ''.join(random.choices('0123456789', k=4))
        expiration = datetime.now() + timedelta(minutes=30)
        self.env['otp.code'].create({
            'partner_id': partner.id,
            'code': otp_code,
            'expiration': expiration,
        })
        return otp_code

    