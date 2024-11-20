# -*- coding: utf-8 -*-
from .main import *
import sys
import time
from passlib.context import CryptContext

_logger = logging.getLogger(__name__)


# List of REST resources in current file:
#   (url prefix)            (method)     (action)
# /api/auth/get_tokens        GET     - Login in Odoo and get access tokens
# /api/auth/refresh_token     POST    - Refresh access token
# /api/auth/delete_tokens     POST    - Delete access tokens from token store


# List of IN/OUT data (json data and HTTP-headers) for each REST resource:

# /api/auth/get_tokens  GET  - Login in Odoo and get access tokens
# IN data:
#   JSON:
#       {
#           "username": "XXXX",     # Odoo username
#           "password": "XXXX",     # Odoo user password
#           "access_lifetime": XXX, # (optional) access token lifetime (seconds)
#           "refresh_lifetime": XXX # (optional) refresh token lifetime (seconds)
#       }
# OUT data:
OUT__auth_gettokens__SUCCESS_CODE = 200             # editable
#   Possible ERROR CODES:
#       400 'empty_username_or_password'
#       401 'odoo_user_authentication_failed'
#   JSON:
#       {
#           "uid":                  XXX,
#           "user_context":         {....},
#           "company_id":           XXX,
#           "access_token":         "XXXXXXXXXXXXXXXXX",
#           "expires_in":           XXX,
#           "refresh_token":        "XXXXXXXXXXXXXXXXX",
#           "refresh_expires_in":   XXX
#       }

# /api/auth/refresh_token  POST  - Refresh access token
# IN data:
#   JSON:
#       {
#           "refresh_token": "XXXXXXXXXXXXXXXXX",
#           "access_lifetime": XXX  # (optional) access token lifetime (seconds)
#       }
# OUT data:
OUT__auth_refreshtoken__SUCCESS_CODE = 200          # editable
#   Possible ERROR CODES:
#       400 'no_refresh_token'
#       401 'invalid_token'
#   JSON:
#       {
#           "access_token": "XXXXXXXXXXXXXXXXX",
#           "expires_in":   XXX
#       }

# /api/auth/delete_tokens  POST  - Delete access tokens from token store
# IN data:
#   JSON:
#       {"refresh_token": "XXXXXXXXXXXXXXXXX"}
# OUT data:
OUT__auth_deletetokens__SUCCESS_CODE = 200          # editable
#   Possible ERROR CODES:
#       400 'no_refresh_token'


# HTTP controller of REST resources:

class ControllerREST(http.Controller):

    def set_verification_status(self, email, is_verified):
        # Stocker la valeur de isVerified dans ir.config_parameter
        request.env['ir.config_parameter'].sudo().set_param(f'user_verification_{email}', is_verified)

    def get_verification_status(self, email):
        # Récupérer la valeur de isVerified depuis ir.config_parameter
        return request.env['ir.config_parameter'].sudo().get_param(f'user_verification_{email}')

    def get_user_avatar(self, email):
        # Récupérer la valeur de isVerified depuis ir.config_parameter
        return request.env['ir.config_parameter'].sudo().get_param(f'user_avatar_{email}')


    def set_user_avatar(self, email, avatar):
        # Stocker la valeur de isVerified dans ir.config_parameter
        request.env['ir.config_parameter'].sudo().set_param(f'user_avatar_{email}', avatar)
    def define_token_expires_in(self, token_type, jdata):
        token_lifetime = jdata.get('%s_lifetime' % token_type)
        try:
            token_lifetime = float(token_lifetime)
        except:
            pass
        if isinstance(token_lifetime, (int, float)):
            expires_in = token_lifetime
        else:
            try:
                expires_in = float(request.env['ir.config_parameter'].sudo()
                    .get_param('rest_api.%s_token_expires_in' % token_type))
            except:
                expires_in = None
        return int(round(expires_in or (sys.maxsize - time.time())))


    def _get_parent_data(self, user_partner ):
        _logger.info(f" user parent {user_partner.parent_id} , {user_partner.parent_id.name},{user_partner.parent_id.phone}")
        
        if user_partner.parent_id:
            return {
                'id': user_partner.parent_id.id,
                'name': user_partner.parent_id.name,
                'email': user_partner.parent_id.email,
                'phone': user_partner.parent_id.phone,
                'entreprise_code': user_partner.parent_id.entreprise_code or None,
                'info': 'Parent'
            }
        else:
           return {}
        
        
    def _get_company_data(self, user_partner ):
        _logger.info(f" user parent {user_partner.parent_id} , {user_partner.parent_id.name},{user_partner.parent_id.phone}")
        
        return {
                'id': user_partner.company_id.id,
                'name': user_partner.company_id.name,
                'email': user_partner.company_id.email,
                'phone': user_partner.company_id.phone,
                'entreprise_code': user_partner.company_id.entreprise_code or None,
                'info': "Entreprise"
            }    
            


    @http.route('/api/auth/refresh_token', methods=['POST'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    def api_auth_refreshtoken(self, **kw):
        # Get request parameters from url
        args = request.httprequest.args.to_dict()
        # Get request parameters from body
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        
        # Get and check refresh token
        refresh_token = jdata.get('refresh_token')
        if not refresh_token:
            error_descrip = "No refresh token was provided in request!"
            error = 'no_refresh_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        # Validate refresh token
        refresh_token_data = token_store.fetch_by_refresh_token(request.env, refresh_token)
        if not refresh_token_data:
            return error_response_401__invalid_token()
        
        old_access_token = refresh_token_data['access_token']
        new_access_token = generate_token()
        expires_in = self.define_token_expires_in('access', jdata)
        uid = refresh_token_data['user_id']
        
        # Update access (and refresh) token in store
        token_store.update_access_token(
            request.env,
            old_access_token = old_access_token,
            new_access_token = new_access_token,
            expires_in = expires_in,
            refresh_token = refresh_token,
            user_id = uid)
        
        # Successful response:
        resp = werkzeug.wrappers.Response(
            status = OUT__auth_refreshtoken__SUCCESS_CODE,
            content_type = 'application/json; charset=utf-8',
            headers = [ ('Cache-Control', 'no-store'),
                        ('Pragma', 'no-cache')  ],
            response = json.dumps({
                'access_token': new_access_token,
                'expires_in':   expires_in,
            }),
        )
        # Remove cookie session
        resp.set_cookie = lambda *args, **kwargs: None
        return resp
    
    # Delete access tokens from token store:
    @http.route('/api/auth/delete_tokens', methods=['POST'], type='http', auth='none', cors=rest_cors_value, csrf=False)
    def api_auth_deletetokens(self, **kw):
        # Get request parameters from url
        args = request.httprequest.args.to_dict()
        # Get request parameters from body
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        
        # Get and check refresh token
        refresh_token = jdata.get('refresh_token')
        if not refresh_token:
            error_descrip = "No refresh token was provided in request!"
            error = 'no_refresh_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        token_store.delete_all_tokens_by_refresh_token(request.env, refresh_token)
        
        # Successful response:
        return successful_response(
            OUT__auth_deletetokens__SUCCESS_CODE,
            {}
        )


    def hash_password(self, password):
        """
        Fonction pour hacher un mot de passe en utilisant le contexte de hachage par défaut d'Odoo.
        """
        # Créez un contexte de hachage similaire à celui d'Odoo
        pwd_context = CryptContext(schemes=["pbkdf2_sha512", "md5_crypt"], deprecated="md5_crypt")
        # Hache le mot de passe
        hashed_password = pwd_context.hash(password)
        return hashed_password
    

    def check_password(self, password, hashed_password):
        """
        Fonction pour verifier le mot de passe haché.
        """
        # Créez un contexte de hachage similaire à celui d'Odoo
        pwd_context = CryptContext(schemes=["pbkdf2_sha512", "md5_crypt"], deprecated="md5_crypt")
        # Hache le mot de passe
        return pwd_context.verify(password, hashed_password)

    def is_hashed_password(self, password):
        """
        Vérifie si le mot de passe est déjà haché.
        """
        if not password:
            return False
        # Contexte de hachage d'Odoo pour gérer les mots de passe
        pwd_context = CryptContext(schemes=["pbkdf2_sha512", "md5_crypt"], deprecated="md5_crypt")
        
        # Retourne True si le mot de passe est déjà haché, False sinon
        return pwd_context.identify(password) is not None
    

    def _get_db_name(self):
        return request.session.db

    def _create_successful_response(self, uid, tokens, user_data , company_data, parent_data):
        response_data = {
            'uid': uid,
            'user_context': request.session.context if uid else {},
            'company_id': request.env.user.company_id.id if uid else 'null',
            'user_info': user_data,
            'is_verified': user_data['is_verified'],
            'company': company_data,
            'parent': parent_data, 
            **tokens
        }

        resp = werkzeug.wrappers.Response(
            status=OUT__auth_gettokens__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(response_data),
        )
        resp.set_cookie = lambda *args, **kwargs: None
        return resp
    
    def _get_user_data(self, user_partner, uid):
        return {
            'id': user_partner.id,
            'uid': uid,
            'name': user_partner.name,
            'email': user_partner.email,
            'partner_id': user_partner.id,
            # 'company_name': user_partner.company_id.name  or None,
            # 'company_id': user_partner.company_id.id or None,
            'partner_city': user_partner.city,
            'partner_phone': user_partner.phone,
            'country_id': user_partner.country_id.id,
            'country_name': user_partner.country_id.name,
            'country_code': user_partner.country_id.code,
            'country_phone_code': user_partner.country_id.phone_code,
            'is_verified': user_partner.is_verified,
            'avatar': user_partner.avatar,
            'role': user_partner.role,
            'adhesion': user_partner.adhesion,
            'adhesion_submit' : user_partner.adhesion_submit,
            'parent_id': user_partner.parent_id.id
        }
    
    def _generate_and_save_tokens(self, uid):
        access_token = generate_token()
        refresh_token = generate_token()
        expires_in = 3600  
        refresh_expires_in = max(7200, expires_in)

        token_store.save_all_tokens(
            request.env,
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
            user_id=uid
        )

        return {
            'access_token': access_token,
            'expires_in': expires_in,
            'refresh_token': refresh_token,
            'refresh_expires_in': refresh_expires_in,
        }
    

    def _authenticate_odoo_user(self):
        email_admin = 'dev-odoo-16'
        password_admin = 'password'

        # email_admin = 'ccbmtech@ccbm.sn'
        # password_admin = 'ccbmE@987'
        try:
            request.session.authenticate(self._get_db_name(), email_admin, password_admin)
        except Exception as e:
            _logger.error(f"Odoo authentication failed: {str(e)}")
        return request.session.uid
    
    def _verify_partner_password(self, user_partner, password):
        if self.is_hashed_password(user_partner.password):
            return self.check_password(password, user_partner.password)
        elif user_partner.password == password:
            hash_password = self.hash_password(password)
            user_partner.write({'password': hash_password})
            return True
        return False
    
    def _get_user_partner(self, username):
        return request.env['res.partner'].sudo().search([('email', '=', username)], limit=1)
    
    def _authenticate_admin(self):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

    def _validate_credentials(self, jdata):
        username = jdata.get('username')
        password = jdata.get('password')
        if not username or not password:
            raise ValueError("Empty value of 'username' or 'password'!")
        return username, password
    
    def _get_request_data(self):
        args = request.httprequest.args.to_dict()
        try:
            body = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            body = {}
        jdata = args.copy()
        jdata.update(body)
        return jdata
    
    @http.route('/api/auth/get_tokens', methods=['GET', 'POST'], type='http', auth='none', cors="*", csrf=False)
    def api_auth_gettokens(self, **kw):
        try:
            jdata = self._get_request_data()
            username, password = self._validate_credentials(jdata)
            
            self._authenticate_admin()
            user_partner = self._get_user_partner(username)
            
            if not user_partner:
                return error_resp(400, "Email ou mot de passe incorrecte!")
            
            if not user_partner.is_verified:
                return error_resp(400, "Email non verifié!")
            
            is_true_partner = self._verify_partner_password(user_partner, password)
            
            if not is_true_partner:
                return error_resp(401, "Email ou mot de passe incorrecte")
            
            uid = self._authenticate_odoo_user()
            
            if not uid:
                return error_response(401, 'odoo_user_authentication_failed', "Odoo User authentication failed!")
            
            tokens = self._generate_and_save_tokens(uid)
            user_data = self._get_user_data(user_partner, uid)
            company_data = self._get_company_data(user_partner)
            parent_data = self._get_parent_data(user_partner)
            
            return self._create_successful_response(uid, tokens, user_data, company_data ,parent_data)
        
        except Exception as e:
            _logger.error(f"Error in api_auth_gettokens: {str(e)}")
            return error_response(500, 'internal_server_error', str(e))
        

    @http.route('/api/auth/login', methods=['POST'], type='http', auth='none', cors='*', csrf=False)
    def api_auth_login_post(self, **kw):

        try:
            jdata = json.loads(request.httprequest.data)
            username, password = self._validate_credentials(jdata)
            
            self._authenticate_admin()
            user_partner = self._get_user_partner(username)
            
            if not user_partner:
                return error_resp(400, "Email ou mot de passe incorrecte!")
            
            if not user_partner.is_verified:
                return error_resp(400, "Email non verifié!")
            
            is_true_partner = self._verify_partner_password(user_partner, password)
            
            if not is_true_partner:
                return error_resp(401, "Email ou mot de passe incorrecte")
            
            uid = self._authenticate_odoo_user()
            
            if not uid:
                return error_response(401, 'odoo_user_authentication_failed', "Odoo User authentication failed!")
            
            tokens = self._generate_and_save_tokens(uid)
            user_data = self._get_user_data(user_partner, uid)
            company_data = self._get_company_data(user_partner)
            parent_data = self._get_parent_data(user_partner)
            
            return self._create_successful_response(uid, tokens, user_data, company_data, parent_data)
        
        except Exception as e:
            _logger.error(f"Error in api_auth_gettokens: {str(e)}")
            return error_response(500, 'internal_server_error', str(e))