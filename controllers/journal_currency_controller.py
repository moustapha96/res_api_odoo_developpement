# -*- coding: utf-8 -*-
from .main import *
import pdb
import datetime
import logging
import json
_logger = logging.getLogger(__name__)


class JournalCurrencyREST(http.Controller):
    @http.route('/api/journals', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_get_journals(self):
        try:
            # Récupérer tous les journaux comptables
            journals = request.env['account.journal'].sudo().search([])
            # Convertir les journaux en dictionnaires
            journals_dict = []
            for journal in journals:
                journal_dict = {
                    'id': journal.id,
                    'name': journal.name,
                    'code': journal.code,
                    'type': journal.type,
                    'company_id': journal.company_id.id,
                    'company_name': journal.company_id.name,
                    'currency': journal.currency_id.id or None
                    # Ajoutez d'autres champs ici selon vos besoins
                }
                journals_dict.append(journal_dict)

            # Retourner la liste des journaux en JSON
            return request.make_response(
                json.dumps(journals_dict),
                headers={'Content-Type': 'application/json'}
            )

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )

    @http.route('/api/methode_payment', methods=['GET'], type='http', cors="*", auth='none', csrf=False)
    def api_get_journals(self):
        try:
            # Récupérer tous les journaux comptables
            methodes = request.env['account.payment.method.line'].sudo().search([])
            # Convertir les journaux en dictionnaires
            methodes_dict = []
            for meth in methodes:
                methode_dict = {
                    'id': meth.id,
                    'method_payment_name': meth.name,
                    'journal_id': meth.journal_id.id,
                    'journal_name': meth.journal_id.name,
                    'journal_code': meth.journal_id.code,
                    'jpurnal_type': meth.journal_id.type,
                    'journal_company_id': meth.journal_id.company_id.id,
                    'journal_company_name': meth.journal_id.company_id.name,
                    'journal_currency': meth.journal_id.currency_id.id or None,
                    'payment_method_id': meth.payment_method_id.id,
                    'payment_method_name': meth.payment_method_id.name,
                    'payment_account_id': meth.payment_account_id.id,
                    'sequence': meth.sequence,
                    # Ajoutez d'autres champs ici selon vos besoins
                }
                methodes_dict.append(methode_dict)

            # Retourner la liste des journaux en JSON
            return request.make_response(
                json.dumps(methodes_dict),
                headers={'Content-Type': 'application/json'}
            )

        except ValueError as e:
            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers={'Content-Type': 'application/json'}
            )
