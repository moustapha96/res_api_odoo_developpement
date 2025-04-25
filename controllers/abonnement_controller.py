# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime

_logger = logging.getLogger(__name__)


class AbonnementControllerREST(http.Controller):

    @http.route('/api/abonnement/<email>/desactiver', methods=['GET'], type='http', auth='none')
    def desactiver_abonnement(self, email, **kwargs):

        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)

        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            return request.not_found()
        partner.write({'subscribed': False})

        return request.make_response(json.dumps({'status': 'success', 'message': 'Abonnement desactivé'}), headers={'Content-Type': 'application/json'})
    
    @http.route('/api/abonnement/<email>/activer', methods=['GET'], type='http', auth='none')
    def activer_abonnement(self, email, **kwargs):

        user = request.env['res.users'].sudo().search([('id', '=', request.env.uid)], limit=1)
        if not user or user._is_public():
            return request.not_found()

        partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if not partner:
            return request.not_found()
        partner.write({'subscribed': True})

        return request.make_response(json.dumps({'status': 'success', 'message': 'Abonnement activé'}), headers={'Content-Type': 'application/json'})