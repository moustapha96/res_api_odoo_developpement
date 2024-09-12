# -*- coding: utf-8 -*-
from .main import *

import json
from odoo.http import request
import requests
_logger = logging.getLogger(__name__)


class ContactController(http.Controller):


    @http.route('/api/sendContact', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def send_welcome_mail(self, **kw):
        data = json.loads(request.httprequest.data)
        email = data.get('email')
        nom = data.get('nom')
        sujet = data.get('sujet')
        message = data.get('message')

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
                                                <span style="font-size: 10px;">Nouveau message de contact</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {sujet}
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
                                                    Détails de l'expéditeur
                                                </span>
                                            </td>
                                            <td valign="middle" align="right" style="width: 50%;">
                                                {nom}<br/>
                                                {email}
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle" style="width: 100%;">
                                                <span style="font-size: 15px; font-weight: bold;">
                                                    Message
                                                </span>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" style="width: 100%;">
                                                {message}
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
                        </tbody>
                    </table>
                </td>
            </tr>
        </table>
        '''

        # Récupérer ou créer une instance de IrMailServer 
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)        
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{email}, {additional_email}'


        # Définir les valeurs du message e-mail
        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': sujet,
            'body_html': body_html,
            'state': 'outgoing',
        }
        # Construire le message e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            _logger.info('Email envoyé avec succès')
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Mail envoyé avec succès"))
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
          
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps( {'message': str(e)} ))
    