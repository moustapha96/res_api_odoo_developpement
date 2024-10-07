# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)


class userREST(http.Controller):

    def set_verification_status(self, email, is_verified):
        # Stocker la valeur de isVerified dans ir.config_parameter
        request.env['ir.config_parameter'].sudo().set_param(f'user_verification_{email}', is_verified)

    def get_verification_status(self, email):
        # Récupérer la valeur de isVerified depuis ir.config_parameter
        return request.env['ir.config_parameter'].sudo().get_param(f'user_verification_{email}')

    def set_user_avatar(self, email, avatar):
        # Stocker la valeur de isVerified dans ir.config_parameter
        request.env['ir.config_parameter'].sudo().set_param(f'user_avatar_{email}', avatar)

    def get_user_avatar(self, email):
        # Récupérer la valeur de isVerified depuis ir.config_parameter
        return request.env['ir.config_parameter'].sudo().get_param(f'user_avatar_{email}')

    def send_verification_mail(self, email):
        # Récupérer ou créer une instance de IrMailServer
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)

        # Récupérer l'utilisateur associé à l'adresse e-mail
        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            return {'status': 'error', 'message': 'User not found for the given email'}
        company = partner.company_id

        # Construire le contenu de l'e-mail
        subject = 'Vérifiez votre compte'
        url = f"http://localhost:5173/login?mail={partner.email}&isVerified=1&token={partner.id}"
        # url = f"https://ccbme.sn/login?mail={partner.email}&isVerified=1&token={partner.id}"

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
                                                    Votre compte a été créé avec succès !<br/>
                                                    Votre identifiant est <strong>{partner.email}</strong><br/>
                                                    Pour accéder à votre compte, vous pouvez utiliser le lien suivant :
                                                    <div style="margin: 16px 0px 16px 0px;">
                                                        <a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="{url}">
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
                                               {company.name}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td valign="middle" align="left" style="opacity: 0.7;">
                                               {company.phone}
                                                | <a style="text-decoration:none; color: #454748;" href="mailto:{company.email}">{company.email}</a>
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

        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{email}, {additional_email}'

        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
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
            # mail_server.send_email(message)
            mail_mail.send()
            return {'status': 'succes', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}


    @http.route('/api/users/<id>', methods=['GET'], type='http', auth='none', cors="*")
    def api_users_GET(self, id , **kw):
        if id:
            user = request.env['res.users'].sudo().search([('id','=',id)])
            if user:
                user_data = {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'login': user.login,
                    'partner_id': user.partner_id.id or None,
                    'partner_name': user.partner_id.name or None,
                    'partner_street': user.partner_id.street or None,
                    'partner_street2': user.partner_id.street2 or None,
                    'partner_city': user.partner_id.city or None,
                    'partner_state_id': user.partner_id.state_id.id or None,
                    'partner_state_name': user.partner_id.state_id.name or None,
                    'partner_zip': user.partner_id.zip or None,
                    'partner_country_id': user.partner_id.country_id.id or None,
                    'partner_country_name': user.partner_id.country_id.name or None,
                    'partner_vat': user.partner_id.vat or None,
                    'partner_email': user.partner_id.email or None,
                    'partner_phone': user.partner_id.phone or None,
                    'company_id': user.company_id.id or None,
                    'company_name': user.company_id.name or None,
                    'company_street': user.company_id.street or None,
                    'company_street2': user.company_id.street2 or None,
                    'company_city': user.company_id.city or None,
                    'company_state_id': user.company_id.state_id.id or None,
                    'company_state_name': user.company_id.state_id.name or None,
                    'company_zip': user.company_id.zip or None,
                    'company_country_id': user.company_id.country_id.id or None,
                    'company_country_name': user.company_id.country_id.name or None,
                    'company_vat': user.company_id.vat or None,
                    'company_email': user.company_id.email or None,
                    'company_phone': user.company_id.phone or None,
                    'is_verified' : self.get_verification_status(user.email) or None,
                    'avatar': self.get_user_avatar(user.email) or None,
                    'image_1920': user.partner_id.image_1920 or None
                }

                resp = werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps(user_data)
                )
                return resp
            return  werkzeug.wrappers.Response(
                status=404,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Utilisateur non trouvée")
            )
        return  werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("user_id est obligatoire")
        )


    @http.route('/api/users/<id>/compte', methods=['GET'],  type='http', auth='none', cors="*")
    def api_users_compte(self, id):
        partner = request.env['res.partner'].sudo().search( [ ('id', '=' , id)] , limit=1)
        order_obj = request.env['sale.order']
        if partner:
           
            # Compter les commandes de type "order"
            order_count = order_obj.sudo().search_count([('partner_id.id', '=', partner.id), ('state', 'not in', ['cancel', 'draft']), ('type_sale', '=', 'order')])

            # Compter les commandes de type "preorder"
            preorder_count = order_obj.sudo().search_count([('partner_id.id', '=', partner.id), ('state', 'not in', ['cancel', 'draft']), ('type_sale', '=', 'preorder')])

            # Compter les commandes livrées
            delivered_count = order_obj.sudo().search_count([('partner_id.id', '=', partner.id), ('state', '=', 'delivered')])

            # Compter les commandes en cours
            progress_count = order_obj.sudo().search_count([('partner_id.id', '=', partner.id), ('state', 'in', ['sent', 'to_delivered']), ('type_sale', 'in', ['order', 'preorder'])])
           
            return http.Response(json.dumps({
                'user_name': partner.name,
                'order_count': order_count,
                'preorder_count': preorder_count,
                'delivered_count': delivered_count,
                'progress_count': progress_count,
            }), content_type='application/json')
        else:
            return http.Response(json.dumps({
                'message': 'Utilisateur introuvable'
            }), content_type='application/json')
        

    @http.route('/api/users/<int:id>/update', methods=['PUT'], type='http', auth='none', cors='*', csrf=False)
    def api_users_POST(self, id, **kw):
        data = json.loads(request.httprequest.data)
        name = data.get('name')
        city = data.get('city')
        phone = data.get('phone')

        if data:
            country = request.env['res.country'].sudo().search([ ('id' , '=' , 204 ) ] , limit = 1 )
            partner_phone = request.env['res.partner'].sudo().search([('phone', '=', phone), ('id', '!=', id)], limit=1)
            partner = request.env['res.partner'].sudo().search([ ('id', '=', id)], limit=1)

            if partner and partner_phone.phone != phone:
                partner.write({
                    'name': name,
                    'city': city,
                    'phone': phone,
                    'country_id': country.id or None,
                })

                resp = werkzeug.wrappers.Response(
                    status=200,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({
                        'id': partner.id,
                        'name': partner.name,
                        'email': partner.email,
                        'partner_id': partner.id,
                        'company_id': partner.company_id.id,
                        'company_name': partner.company_id.name,
                        'partner_city': partner.city,
                        'partner_phone': partner.phone,
                        'country_id': partner.country_id.id or None,
                        'country_name': partner.country_id.name or None,
                        'country_code': partner.country_id.code,
                        'country_phone_code': partner.country_id.phone_code,
                        'avatar': partner.avatar or None,
                        'is_verified' : partner.is_verified,
                    })
                )
                return resp
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'message': "Un compte avec ce numéro téléphone existe déjà"})
            )
        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({'message': 'Données invalides'})
        )


    @http.route('/api/users/verified/<email>', methods=['GET'], type='http', auth='none', cors="*", csrf=False)
    def api_users_verified(self, email):
        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': 'Utilisateur non trouvé pour l\'e-mail donné'})
            )

        if partner.is_verified == True:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'success', 'message': 'Utilisateur déjà vérifié'})
            )

        if partner.is_verified == False:
            partner.write({'is_verified': True})
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'success', 'message': f'Utilisateur verifié avec succès '})
            )

        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps({'status': 'error', 'message': 'Utilisateur non trouvé pour l\'e-mail donné'})
        )
    

    @http.route('/api/users/avatar/<id>', methods=['PUT'], type='http', auth='none', cors="*", csrf=False)
    def api_users_avatar(self, id ):
        data = json.loads(request.httprequest.data)
        avatar_url = data.get('avatar')

        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({'status': 'error', 'message': 'Utilisateur non trouvé pour l\'e-mail donné'})
            )

        if avatar_url and partner:
            partner.write({
               'avatar': avatar_url
            })
            user_data = {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'company_id': partner.company_id.id,
                'partner_id':partner.id,
                'company_id': partner.company_id.id,
                'company_name': partner.company_id.name,
                'partner_city':partner.city,
                'partner_phone':partner.phone,
                'country_id':partner.country_id.id,
                'country_name':partner.country_id.name,
                'country_code':partner.country_id.code,
                'country_phone_code':partner.country_id.phone_code,
                'is_verified' : partner.is_verified,
                'avatar': partner.avatar
            }
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(user_data)
            )


    @http.route('/api/new_compte', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_new_compte_post(self, **kw):
        data = json.loads(request.httprequest.data)
        if not data:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Données invalides")
            )

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        city = data.get('city')
        phone = data.get('phone')

        company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
        country = request.env['res.country'].sudo().search([('id', '=', 204)], limit=1)
        partner_email = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)

        if partner_email:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Utilisateur avec cet adresse mail existe déjà")
            )

        if not partner_email :
            user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
            if not user or user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            partner = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email,
                'customer_rank': 1,
                'company_id': company.id,
                'city': city,
                'phone': phone,
                'is_company': False,
                'active': True,
                'type': 'contact',
                'company_name': company.name,
                'country_id': country.id or None,
                'password': password,
                'is_verified': False
            })
            if partner:
                self.send_verification_mail(partner.email)
                return werkzeug.wrappers.Response(
                    status=201,
                    content_type='application/json; charset=utf-8',
                    headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                    response=json.dumps({
                        'id': partner.id,
                        'name': partner.name,
                        'email': partner.email,
                        'partner_id':partner.id,
                        'company_id': partner.company_id.id,
                        'company_name': partner.company_id.name,
                        'partner_city': partner.city,
                        'partner_phone': partner.phone,
                        'country_id': partner.country_id.id or None,
                        'country_name': partner.country_id.name or None,
                        'country_code': partner.country_id.code,
                        'country_phone_code': partner.country_id.phone_code,
                        'is_verified': partner.is_verified,
                        'avatar': partner.avatar or None,
                        'image_1920': partner.image_1920 or None
                    })
                    )

        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Compte client non créer, veuillez reessayer")
        )

    # reccuperer un partner a travers son id
    @http.route('/api/partnerByEmail/<email>', methods=['GET'], type='http', auth='none', cors="*")
    def api_partner_get_by_email(self, email):
        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if partner:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({
                    'id': partner.id,
                    'name': partner.name,
                    'email': partner.email,
                    'partner_id':partner.id,
                    'company_id': partner.company_id.id,
                    'company_name': partner.company_id.name,
                    'partner_city': partner.city,
                    'partner_phone': partner.phone,
                    'country_id': partner.country_id.id or None,
                    'country_name': partner.country_id.name or None,
                    'country_code': partner.country_id.code,
                    'country_phone_code': partner.country_id.phone_code,
                    'is_verified': partner.is_verified,
                    'avatar': partner.avatar or None,
                    'image_1920': partner.image_1920 or None,
                    'password': partner.password
                })
            )

        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Compte client non trouvé, veuillez reessayer")
        )
        
    # create password and update info for partner
    @http.route('/api/partner-create/<email>/update', methods=['POST'], type='http', auth='none', cors="*",csrf=False)
    def api_partner_create_update(self, email, **kw):
        data = json.loads(request.httprequest.data)
        telephone = data.get('telephone')
        password = data.get('password')
        city = data.get('adresse')
        name = data.get('name')

        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Compte client non è, veuillez reessayer")
            )
        if partner:
            partner.write({
                'name': name,
                'city': city,
                'phone': telephone,
                'password': password,
                'is_verified': False
            })
            self.send_verification_mail(partner.email)

            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Compte client creer avec succes , veuillez consulter votre email pour la verification")
            )

        return werkzeug.wrappers.Response(
            status=400,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps("Compte client non créé, veuillez reessayer")
        )
    