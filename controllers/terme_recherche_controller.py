# my_module/controllers/controllers.py
from odoo import http
from odoo.http import request


from .main import *
import pdb
import datetime
import logging
import json
import werkzeug



class TermeRechercheController(http.Controller):

    FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/termes_recherche.json")
    @http.route('/api/termeRecherche', methods=['POST'], type='http', cors="*", auth='none', csrf=False)
    def add_terme_recherche(self, **kw):
        
        data = json.loads(request.httprequest.data)
        search_terms = data.get('terme')
        source= data.get('source')
    
        if not source or not search_terms:
            return http.Response('Missing required fields', status=200)
        
        directory = os.path.dirname(self.FILE_PATH)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Charger les données existantes
        if os.path.exists(self.FILE_PATH):
            with open(self.FILE_PATH, "r", encoding="utf-8") as f:
                try:
                    terms_data = json.load(f)
                except json.JSONDecodeError:
                    terms_data = {}
        else:
            terms_data = {}

        if source not in terms_data:
            terms_data[source] = {}

        if search_terms in terms_data[source]:
            terms_data[source][search_terms] += 1
        else:
            terms_data[source][search_terms] = 1

        with open(self.FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(terms_data, f, ensure_ascii=False, indent=4)
        
        resp = werkzeug.wrappers.Response(
                status=201,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps("Terme de recherche enregister")
            )
        return resp
       
