# -*- coding: utf-8 -*-
from .main import *

import json
from odoo.http import request
import requests
_logger = logging.getLogger(__name__)


class MailerRest(http.Controller):

    @http.route('/api/sendMail', methods=['POST'], type='json', auth='none', cors="*", csrf=False)
    def send_mail(self, **kw):
        # Récupérer les paramètres de la requête
        data = json.loads(request.httprequest.data)

        email_from = data.get('email_from')
        email_to = data.get('email_to')
        subject = data.get('subject')
        body = data.get('body')

        if not email_from or not email_to or not subject or not body:
            return {'status': 'error', 'message': 'Missing required parameters'}

        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Construire le message e-mail
        message = mail_server.build_email(email_from, [email_to], subject, body)

        try:
            # Envoyer l'e-mail
            mail_server.send_email(message)
            return {'status': 'success', 'message': 'Email sent successfully'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        

    @http.route('/api/sendMailUser', methods=['POST'], type='json', auth='none', cors="*", csrf=False)
    def send_mail_user(self, **kw):
        # Récupérer les paramètres de la requête
        data = json.loads(request.httprequest.data)

        email_from = data.get('email_from')
        email_to = data.get('email_to')
        subject = data.get('subject')
        body = data.get('body')

        if not email_from or not email_to or not subject or not body:
            return {'status': 'error', 'message': 'Missing required parameters'}

        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return True
            mail_server = request.env['ir.mail_server'].sudo().create({
                'name': 'Gmail',
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_user': 'moustaphakhouma964@gmail.com',
                'smtp_pass': 'moustaphakhouma1996',
                'smtp_encryption': 'starttls',
            })

        # Récupérer le partenaire associé à l'adresse e-mail
        partner = request.env['res.partner'].sudo().search([('id', '=', 70)], limit=1)
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given email'}

        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        # Créer un enregistrement temporaire de crm.lead
        lead = request.env['crm.lead'].sudo().create({
            'name': subject,
            'partner_id': partner.id,
            'email_from': email_from,
            'company_id': partner.company_id.id,
            'user_id':  request.env.user.id,
        })

        # Récupérer le template d'e-mail
        mail_template = request.env['mail.template'].sudo().search([('id', '=', 15)], limit=1)
        if not mail_template:
            return {'status': 'error', 'message': 'Mail template not found'}

        # Générer le contenu de l'e-mail en utilisant le template
        email_values = mail_template.generate_email([lead.id], fields=['email_from', 'email_to', 'subject', 'body_html'])

        # Créer et envoyer l'e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values[lead.id])
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Email sent successfully'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/welcome_mail/<email>', methods=['GET'], type='json', auth='none', cors="*", csrf=False)
    def send_welcome_mail(self, email , **kw):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer l'utilisateur associé à l'adresse e-mail
        user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
        if not user:
            return {'status': 'error', 'message': 'User not found for the given email'}

        # Récupérer le template d'e-mail
        mail_template = request.env['mail.template'].sudo().search([('id', '=', 33)], limit=1)
        if not mail_template:
            return {'status': 'error', 'message': 'Mail template not found'}

        # Générer le contenu de l'e-mail en utilisant le template
        email_values = mail_template.generate_email([user.id], fields=['email_from', 'email_to', 'subject', 'body_html'])

        # Créer et envoyer l'e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values[user.id])
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Email sent successfully'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/sendResetPasswordMail/<email>', methods=['GET'], type='http', auth='none', cors="*", csrf=False)
    def send_reset_password_mail(self,email, **kw):


        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return True
            mail_server = request.env['ir.mail_server'].sudo().create({
                'name': 'Gmail',
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_user': 'moustaphakhouma964@gmail.com',
                'smtp_pass': 'moustaphakhouma1996',
                'smtp_encryption': 'starttls',
            })

        # Récupérer l'utilisateur associé à l'adresse e-mail
        user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
        if not user:
            return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps("Utilisateur non trouvé pour l'e-mail donné")
                )

        # Vérifier si l'utilisateur existe et n'est pas supprimé
        if not user.exists():
            return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps("L'utilisateur n'existe pas ou a été supprimé")
                )

        # Récupérer le template d'e-mail
        mail_template = request.env['mail.template'].sudo().search([('id', '=', 1)], limit=1)
        if not mail_template:
            return werkzeug.wrappers.Response(
                        status=400,
                        content_type='application/json; charset=utf-8',
                        headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                        response=json.dumps("Modèle de courrier électronique non trouvé")
                    )

        email_values = mail_template.generate_email([user.id], fields=['email_from', 'email_to', 'subject', 'body_html'])

        # Créer et envoyer l'e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values[user.id])
        try:
            mail_mail.send()

            return werkzeug.wrappers.Response(
                            status=200,
                            content_type='application/json; charset=utf-8',
                            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                            response=json.dumps("E-mail envoyé avec succès")
                        )
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return werkzeug.wrappers.Response(
                            status=400,
                            content_type='application/json; charset=utf-8',
                            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                            response=json.dumps(f'Error sending email: {str(e)}')
                        )


    @http.route('/api/sendPortalInvitationMail/<email>', methods=['GET'], type='json', auth='none', cors="*", csrf=False)
    def send_portal_invitation_mail(self, email , **kw):

        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return True
            mail_server = request.env['ir.mail_server'].sudo().create({
                'name': 'Gmail',
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_user': 'moustaphakhouma964@gmail.com',
                'smtp_pass': 'moustaphakhouma1996',
                'smtp_encryption': 'starttls',
            })

        # Récupérer l'utilisateur associé à l'adresse e-mail
        user = request.env['res.users'].sudo().search([('id', '=', 9)], limit=1)
        if not user:
            return {'status': 'error', 'message': 'User not found for the given email'}

        # Vérifier si l'utilisateur existe et n'est pas supprimé
        if not user.exists():
            return {'status': 'error', 'message': 'User does not exist or has been deleted'}

        # Récupérer le template d'e-mail
        mail_template = request.env['mail.template'].sudo().search([('id', '=', 2)], limit=1)
        if not mail_template:
            return {'status': 'error', 'message': 'Mail template not found'}

        # Générer le contenu de l'e-mail en utilisant le template
        email_values = mail_template.generate_email([user.id], fields=['email_from', 'email_to', 'subject', 'body_html'])

        # Créer et envoyer l'e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values[user.id])
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Email sent successfully'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/mail_contact', methods=['POST'], type='json', auth='none', cors="*", csrf=False)
    def send_welcome_mail(self, **kw):
        data = json.loads(request.httprequest.data)

        email = data.get('email')
        nom = data.get('nom')
        sujet = data.get('sujet')
        message = data.get('message')
        
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer l'utilisateur associé à l'adresse e-mail
        user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
        if not user:
            return {'status': 'error', 'message': 'User not found for the given email'}

        # Récupérer le template d'e-mail
        mail_template = request.env['mail.template'].sudo().search([('id', '=', 33)], limit=1)
        if not mail_template:
            return {'status': 'error', 'message': 'Mail template not found'}

        # Générer le contenu de l'e-mail en utilisant le template
        email_values = mail_template.generate_email([user.id], fields=['email_from', 'email_to', 'subject', 'body_html'])

        # Créer et envoyer l'e-mail
        mail_mail = request.env['mail.mail'].sudo().create(email_values[user.id])
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Email sent successfully'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/verify_account/<email>', methods=['GET'], type='http', auth='none', cors="*", csrf=False)
    def send_verification_mail(self, email, **kw):
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
                                Généré par <a target="_blank" href="https://www.ccbmshop.sn" style="color: #875A7B;">CCBM Shop</a>
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
     
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return True
            mail_server = request.env['ir.mail_server'].sudo().create({
                'name': 'My Mail Server',
                'smtp_host': 'smtp.gmail.com',  # Utilisez le serveur SMTP correct
                'smtp_port': 587,
                'smtp_user': 'moustaphakhouma964@gmail.com',
                'smtp_pass': 'moustaphakhouma1996',
                'smtp_encryption': 'starttls',
            })

        
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
            # mail_server.send_email(message)
            mail_mail.send()
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Email de verification envoyé avec succés")
            )
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': str(e)})
            )