
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)

from .auth import ControllerREST  # Importez la classe correctement


class PartnerREST(http.Controller):


    @http.route('/api/partner/compte/<int:partner_id>', methods=['GET'], type='http', auth='none', cors='*', csrf=False)
    def api_get_partner(self, partner_id, **kwargs):
        try:
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
            if not partner:
                return error_response(404, 'partner_not_found', 'Partner not found')
            
            auth_controller = ControllerREST()
            user_partner = auth_controller._get_user_partner(partner.email)
            
            if not user_partner:
                return error_response(404, 'user_partner_not_found', 'User partner not found')
            
            uid = auth_controller._authenticate_odoo_user()
            tokens = auth_controller._generate_and_save_tokens(uid)
            user_data = auth_controller._get_user_data(user_partner, uid)
            company_data = auth_controller._get_company_data(user_partner)
            parent_data = auth_controller._get_parent_data(user_partner)
            
            return auth_controller._create_successful_response(uid, tokens, user_data, company_data, parent_data)
        
        except Exception as e:
            _logger.error(f"Error in api_get_partner: {str(e)}")
            return error_response(500, 'internal_server_error', str(e))

        
        












    # @http.route('/api/auth/login', methods=['POST'], type='http', auth='none', cors='*', csrf=False)
    # def api_auth_login_post(self, **kw):

    #     try:
    #         jdata = json.loads(request.httprequest.data)
    #         username, password = self._validate_credentials(jdata)
            
    #         self._authenticate_admin()
    #         user_partner = self._get_user_partner(username)
            
    #         if not user_partner:
    #             return error_resp(400, "Email ou mot de passe incorrecte!")
            
    #         if not user_partner.is_verified:
    #             return error_resp(400, "Email non verifié!")
            
    #         is_true_partner = self._verify_partner_password(user_partner, password)
            
    #         if not is_true_partner:
    #             return error_resp(401, "Email ou mot de passe incorrecte")
            
    #         uid = self._authenticate_odoo_user()
            
    #         if not uid:
    #             return error_response(401, 'odoo_user_authentication_failed', "Odoo User authentication failed!")
            
    #         tokens = self._generate_and_save_tokens(uid)
    #         user_data = self._get_user_data(user_partner, uid)
    #         company_data = self._get_company_data(user_partner)
    #         parent_data = self._get_parent_data(user_partner)
            
    #         return self._create_successful_response(uid, tokens, user_data, company_data, parent_data)
        
    #     except Exception as e:
    #         _logger.error(f"Error in api_auth_gettokens: {str(e)}")
    #         return error_response(500, 'internal_server_error', str(e))