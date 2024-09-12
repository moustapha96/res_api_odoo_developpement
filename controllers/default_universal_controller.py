# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    
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
                                                    Cher {user.name},<br/><br/>
                                                    Votre compte a été créé avec succès !<br/>
                                                    Votre identifiant est <strong>{user.email}</strong><br/>
                                                    Pour accéder à votre compte, vous pouvez utiliser le lien suivant :
                                                    <div style="margin: 16px 0px 16px 0px;">
                                                        <a style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;" href="https://ccbme.sn/login?mail={user.email}&isVerified=1&token={user.id}">
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
                                Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM Shop</a>
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
    
    def define_schema_params(self, request, model_name, method):
        schema = pre_schema = default_vals = None
        cr, uid = request.cr, request.session.uid
        Model = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        ResModel = request.env(cr, uid)[model_name]
        if Model.rest_api__used:
            model_available = True
            if method == 'read_all':
                if Model.rest_api__read_all__schema:
                    schema = literal_eval(Model.rest_api__read_all__schema)
                    pre_schema = True
                else:
                    if 'name' in ResModel._fields.keys():
                        schema = ('id', 'name',)
                    else:
                        schema = ('id',)
                    pre_schema = False
            elif method == 'read_one':
                if Model.rest_api__read_one__schema:
                    schema = literal_eval(Model.rest_api__read_one__schema)
                    pre_schema = True
                else:
                    schema = tuple(ResModel._fields.keys())
                    pre_schema = False
            elif method == 'create_one':
                if Model.rest_api__create_one__schema:
                    schema = literal_eval(Model.rest_api__create_one__schema)
                    pre_schema = True
                else:
                    schema = ('id',)
                    pre_schema = False
                default_vals = literal_eval(Model.rest_api__create_one__defaults or '{}')
        else:
            model_available = False
        return model_available, schema, pre_schema, default_vals
    
    # Read all (with optional filters, offset, limit, order, exclude_fields, include_fields):
    @http.route('/api/<string:model_name>', methods=['GET'], type='http', auth='none', cors=rest_cors_value)
    # @check_permissions
    def api__model_name__GET(self, model_name, **kw):
        model_available, schema, pre_schema, _ = self.define_schema_params(request, model_name, 'read_all')
        if not model_available:
            return error_response_501__model_not_available()
        _logger.debug('schema == %s; pre_schema == %s' % (schema, pre_schema))
        return wrap__resource__read_all(
            modelname = model_name,
            default_domain = [],
            success_code = 200,
            OUT_fields = schema,
            pre_schema = pre_schema,
        )
    
    # Read one (with optional exclude_fields, include_fields):
    @http.route('/api/<string:model_name>/<id>', methods=['GET'], type='http', auth='none', cors=rest_cors_value)
    @check_permissions
    def api__model_name__id_GET(self, model_name, id, **kw):
        model_available, schema, pre_schema, _ = self.define_schema_params(request, model_name, 'read_one')
        if not model_available:
            return error_response_501__model_not_available()
        _logger.debug('schema == %s; pre_schema == %s' % (schema, pre_schema))
        return wrap__resource__read_one(
            modelname = model_name,
            id = id,
            success_code = 200,
            OUT_fields = schema,
            pre_schema = pre_schema,
        )
    
    # Create one:
    @http.route('/api/<string:model_name>', methods=['POST'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    @check_permissions
    def api__model_name__POST(self, model_name, **kw):
        model_available, schema, _, default_vals = self.define_schema_params(request, model_name, 'create_one')
        if not model_available:
            return error_response_501__model_not_available()
        _logger.debug('schema == %s; default_vals == %s' % (schema, default_vals))
        return wrap__resource__create_one(
            modelname = model_name,
            default_vals = default_vals,
            success_code = 200,
            OUT_fields = schema,
        )
    
    # Update one:
    @http.route('/api/<string:model_name>/<id>', methods=['PUT'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    @check_permissions
    def api__model_name__id_PUT(self, model_name, id, **kw):
        return wrap__resource__update_one(
            modelname = model_name,
            id = id,
            success_code = 200,
        )

    # Delete one:
    @http.route('/api/<string:model_name>/<id>', methods=['DELETE'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    @check_permissions
    def api__model_name__id_DELETE(self, model_name, id, **kw):
        return wrap__resource__delete_one(
            modelname = model_name,
            id = id,
            success_code = 200,
        )

    # Call method (with optional parameters):
    @http.route('/api/<string:model_name>/<id>/<method>', methods=['PUT'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    @check_permissions
    def api__model_name__id__method_PUT(self, model_name, id, method, **kw):
        return wrap__resource__call_method(
            modelname = model_name,
            id = id,
            method = method,
            success_code = 200,
        )


    # Reccuperer la liste des stats
    @http.route('/api/state', methods=['GET'], type='http', auth='none', cors='*' )
    def api_state_get(self, **kw):
        countrys = request.env['res.country.state'].sudo().search([])
        country_data = []
        if countrys:
            for p in countrys:
                country_data.append({
                'id': p.id,
                'state_name': p.name,
                'state_id': p.id,
                'country_id': p.country_id.id,
                'phone': p.country_id.phone_code,
                'code' : p.code,
                'country_name': p.country_id.name
            })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(country_data)
            )
            return resp
        return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Erreur lors de la reccuperation des pays"))

    @http.route('/api/country', methods=['GET'], type='http', auth='none', cors='*' )
    def api_country_get(self, **kw):
        countrys = request.env['res.country'].sudo().search([])
        country_data = []
        if countrys:
            for p in countrys:
                country_data.append({
                'id': p.id,
                'phone': p.phone_code,
                'code' : p.code,
                'name': p.name
            })

            resp = werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(country_data)
            )
            return resp
        return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Erreur lors de la reccuperation des pays"))


