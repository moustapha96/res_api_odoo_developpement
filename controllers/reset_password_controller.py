# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

from odoo import http, models, api, fields , tools, SUPERUSER_ID, _, Command
from odoo.http import request
import werkzeug
import json
import logging
import random
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import time

from functools import wraps

_logger = logging.getLogger(__name__)


def _jsonable(o):
    try: json.dumps(o)
    except TypeError: return False
    else: return True

def check_identity(fn):
    """ Wrapped method should be an *action method* (called from a button
    type=object), and requires extra security to be executed. This decorator
    checks if the identity (password) has been checked in the last 10mn, and
    pops up an identity check wizard if not.

    Prevents access outside of interactive contexts (aka with a request)
    """
    @wraps(fn)
    def wrapped(self):
        if not request:
            raise UserError(_("This method can only be accessed over HTTP"))

        if request.session.get('identity-check-last', 0) > time.time() - 10 * 60:
            # update identity-check-last like github?
            return fn(self)

        w = self.sudo().env['res.users.identitycheck'].create({
            'request': json.dumps([
                { # strip non-jsonable keys (e.g. mapped to recordsets like binary_field_real_user)
                    k: v for k, v in self.env.context.items()
                    if _jsonable(v)
                },
                self._name,
                self.ids,
                fn.__name__
            ])
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.users.identitycheck',
            'res_id': w.id,
            'name': _("Security Control"),
            'target': 'new',
            'views': [(False, 'form')],
        }
    wrapped.__has_check_identity = True
    return wrapped


class ChangePasswordWizard(models.TransientModel):
    _name = "change.password.wizard"
    _description = "Change Password Wizard"

    def _default_user_ids(self):
        user_ids = self._context.get('active_model') == 'res.users' and self._context.get('active_ids') or []
        return [
            Command.create({'user_id': user.id, 'user_login': user.login})
            for user in self.env['res.users'].browse(user_ids)
        ]

    user_ids = fields.One2many('change.password.user', 'wizard_id', string='Users', default=_default_user_ids)

    def change_password_button(self):
        self.ensure_one()
        self.user_ids.change_password_button()
        if self.env.user in self.user_ids.user_id:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return {'type': 'ir.actions.act_window_close'}

class ChangePasswordUser(models.TransientModel):
    _name = 'change.password.user'
    _description = 'User, Change Password Wizard'

    wizard_id = fields.Many2one('change.password.wizard', string='Wizard', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    user_login = fields.Char(string='User Login', readonly=True)
    new_passwd = fields.Char(string='New Password', default='')

    def change_password_button(self):
        for line in self:
            if not line.new_passwd:
                raise UserError(_("Before clicking on 'Change Password', you have to write a new password."))
            line.user_id._change_password(line.new_passwd)
        # don't keep temporary passwords in the database longer than necessary
        self.write({'new_passwd': False})

class ChangePasswordOwn(models.TransientModel):
    _name = "change.password.own"
    _description = "User, change own password wizard"
    _transient_max_hours = 0.1

    new_password = fields.Char(string="New Password")
    confirm_password = fields.Char(string="New Password (Confirmation)")

    @api.constrains('new_password', 'confirm_password')
    def _check_password_confirmation(self):
        if self.confirm_password != self.new_password:
            raise ValidationError(_("The new password and its confirmation must be identical."))

    @check_identity
    def change_password(self):
        self.env.user._change_password(self.new_password)
        self.unlink()
        # reload to avoid a session expired error
        # would be great to update the session id in-place, but it seems dicey
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    

class ResetPasswordREST(http.Controller):

    def generate_token(self, email):

        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d%H%M%S")
        email_letters = list(email)
        random.shuffle(email_letters)
        shuffled_email = ''.join(email_letters)
        combined_str = f"{date_str}{shuffled_email}"
        token = hashlib.sha256(combined_str.encode()).hexdigest()
        token = token[:16]
        return token

    @http.route('/api/new-password', methods=['POST'], type='http', auth='none', cors='*', csrf=False)
    def reset_password(self, **kwargs):
        data = json.loads(request.httprequest.data)
        email = data.get('email')
        password = data.get('password')
        token = data.get('token')

        _logger.info(f"Received data: email={email}, password={password}, token={token}")

        if not token or not password:
            _logger.error("Missing token or password")
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': 'Missing token or password'})
            )

        try:
            user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
            if not user or user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            partner = request.env['res.partner'].sudo().search([('signup_token', '=', token),('email', '=', email)], limit=1)
            _logger.info(f"Partner: {partner}")
            if partner  and partner.signup_token == token  and partner.email == email and partner.signup_expiration >= datetime.datetime.now():
                partner.write({
                    'signup_type': None,
                    'signup_token': None,
                    'signup_expiration': None,
                    'password': password
                })

                _logger.info(f"Password reset for email: {email}")
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({'status': 'success', 'message': 'Le mot de passe a été réinitialisé avec succès'})
                )
            else:
                _logger.error(f"Token not found for email: {email}")
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({'status': 'error', 'message': 'Token non trouvé'})
                )
            

        except Exception as e:
            _logger.error(f'Erreur lors de la réinitialisation du mot de passe: {str(e)}')
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': str(e)})
            )

        

    @http.route('/api/reset-password/<email>', methods=['GET'], type='http', auth='none', cors='*', csrf=False)
    def reset_password_request(self,email, **kwargs):

        if not email:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': f'email non valide '})
            )

        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)


        partner = request.env['res.partner'].sudo().search([ ('email', '=', email) , ( 'role','=','main_user' ) ], limit=1)
        company = partner.company_id

        if partner:
            # Générer un token de réinitialisation de mot de passe
            token = self.generate_token(email)
            # Construire le contenu de l'e-mail
            subject = 'Réinitialiser votre mot de passe'
            reset_url = f'https://ccbme.sn/new-password?mail={partner.email}&token={token}'
            # reset_url = f'https://localhost:5173/new-password?mail={partner.email}&token={token}'
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
                                                    <span style="font-size: 10px;">Réinitialisation de mot de passe</span><br/>
                                                    <span style="font-size: 20px; font-weight: bold;">
                                                        {partner.name}
                                                    </span>
                                                </td>
                                                <td valign="middle" align="right">
                                                    <img style="padding: 0px; margin: 0px; height: auto; width: 80px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
                                                        Vous avez demandé une réinitialisation de votre mot de passe.<br/>
                                                        Pour réinitialiser votre mot de passe, cliquez sur le lien suivant :
                                                        <div style="margin: 16px 0px 16px 0px;">
                                                            <a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="{reset_url}">
                                                                Réinitialiser le mot de passe
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
                                                {company.name}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td valign="middle" align="left" style="opacity: 0.7;">
                                                {company.phone}
                                                    | <a style="text-decoration:none; color: #2D7DBA;" href="mailto:{company.email}">{company.email}</a>
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
                                    Généré par <a target="_blank" href="https://ccbme.sn" style="color: #2D7DBA;">CCBM Shop</a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            '''

            mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
            email_from = mail_server.smtp_user
            additional_email = 'shop@ccbm.sn'
            email_to = f'{email}, {additional_email}'

            email_values = {
                'email_from': email_from,
                'email_to': email_to,
                'subject': subject,
                'body_html': body_html,
                'state': 'outgoing',
            }
            mail_mail = request.env['mail.mail'].sudo().create(email_values)

            try:
                mail_mail.send()
                # Enregistrer le token
                partner.write({
                    'signup_type' : 'reset',
                    'signup_token': token,
                    'signup_expiration': datetime.datetime.now() + datetime.timedelta(days=1),
                })

                return werkzeug.wrappers.Response(
                        status=200,
                        content_type='application/json; charset=utf-8',
                        headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                        response=json.dumps({'status': 'success', 'message': f'Un lien de réinitialisation du mot de passe a été envoyé à votre adresse e-mail'})
                    )

            except Exception as e:
                _logger.error(f'Error sending email: {str(e)}')
                return werkzeug.wrappers.Response(
                        status=200,
                        content_type='application/json; charset=utf-8',
                        headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                        response=json.dumps({'status': 'error', 'message': str(e)})
                    )
        else:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': 'Utilisateur ou compte non existant'})
            )


    @http.route('/api/rh/reset-password/<email>', methods=['GET'], type='http', auth='none', cors='*', csrf=False)
    def reset_password_request_rh(self,email, **kwargs):
        if not email:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': f'email non valide '})
            )

        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)


        partner = request.env['res.partner'].sudo().search([ ('email', '=', email) ], limit=1)
        company = partner.parent_id

        if partner:
            # Générer un token de réinitialisation de mot de passe
            token = self.generate_token(email)
            # Construire le contenu de l'e-mail
            subject = 'Réinitialiser votre mot de passe'
            # reset_url = f'https://africatransit.sn/new-password?mail={partner.email}&token={token}'
            reset_url = f'http://localhost:3000/new-password?mail={partner.email}&token={token}'
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
                                                    <span style="font-size: 10px;">Réinitialisation de mot de passe</span><br/>
                                                    <span style="font-size: 20px; font-weight: bold;">
                                                        {partner.name}
                                                    </span>
                                                </td>
                                                <td valign="middle" align="right">
                                                    <img style="padding: 0px; margin: 0px; height: auto; width: 80px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
                                                        Vous avez demandé une réinitialisation de votre mot de passe.<br/>
                                                        Pour réinitialiser votre mot de passe, cliquez sur le lien suivant :
                                                        <div style="margin: 16px 0px 16px 0px;">
                                                            <a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="{reset_url}">
                                                                Réinitialiser le mot de passe
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
                                                {company.name}
                                                </td>
                                            </tr>
                                            <tr>
                                                <td valign="middle" align="left" style="opacity: 0.7;">
                                                {company.phone}
                                                    | <a style="text-decoration:none; color: #2D7DBA;" href="mailto:{company.email}">{company.email}</a>
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
                                    Généré par <a target="_blank" href="https://africatransit.sn/" style="color: #2D7DBA;">CCBM Shop GRH</a>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            '''

            mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
            email_from = mail_server.smtp_user
            additional_email = 'shop@ccbm.sn'
            email_to = f'{email}, {additional_email}'

            email_values = {
                'email_from': email_from,
                'email_to': email_to,
                'subject': subject,
                'body_html': body_html,
                'state': 'outgoing',
            }
            mail_mail = request.env['mail.mail'].sudo().create(email_values)

            try:
                mail_mail.send()
                # Enregistrer le token
                partner.write({
                    'signup_type' : 'reset',
                    'signup_token': token,
                    'signup_expiration': datetime.datetime.now() + datetime.timedelta(days=1),
                })

                return werkzeug.wrappers.Response(
                        status=200,
                        content_type='application/json; charset=utf-8',
                        headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                        response=json.dumps({'status': 'success', 'message': f'Un lien de réinitialisation du mot de passe a été envoyé à votre adresse e-mail'})
                    )

            except Exception as e:
                _logger.error(f'Error sending email: {str(e)}')
                return werkzeug.wrappers.Response(
                        status=200,
                        content_type='application/json; charset=utf-8',
                        headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                        response=json.dumps({'status': 'error', 'message': str(e)})
                    )
        else:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': 'Adresse e-mail non valide'})
            )