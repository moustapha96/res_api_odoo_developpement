
from .main import *

from odoo import http, models, fields
from odoo.http import request
import json
import logging
import werkzeug
import logging
_logger = logging.getLogger(__name__)



class CRMUpdateController(http.Controller):



    @http.route('/api/create_or_update_crm', type='http', auth='none', methods=['POST'], cors="*", csrf=False)
    def create_or_update_crm(self, **post):
        try:
            # Vérification de l'utilisateur
            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            # Récupération des données
            crm_data = json.loads(request.httprequest.data or "{}")
            if not crm_data:
                return json.dumps({"status": "error", "message": "Les données sont vides ou invalides."})
            
    
            # Vérifiez les champs requis
            if not all(key in crm_data for key in ['total', 'type', 'date', 'location', 'produits']):
                return json.dumps({"status": "error", "message": "Certains champs obligatoires sont manquants dans les données CRM."})

            total = crm_data.get('total')
            type = crm_data.get('type')
            date = crm_data.get('date')
            location = crm_data.get('location')
            localisation = crm_data.get('localisation')
            produits = crm_data.get('produits')

            # Traitement des données
            if not crm_data:
                return json.dumps({"status": "error", "message": "Aucune donnée CRM reçue"})

            CRM = request.env['crm.lead'].sudo()
            Partner = request.env['res.partner'].sudo()
            LeadLine = request.env['crm.lead.line'].sudo()

            # Recherche d'un CRM existant
            existing_crm = CRM.search([
                '|',
                ('email_from', '=', crm_data.get('email')),
                ('email_from', '=', crm_data.get('guest_id'))
            ], limit=1)

            # Recherche d'un partenaire existant
            partner = None
            if crm_data.get('email') != "Guest":
                partner = Partner.search([('email', '=', crm_data.get('email'))], limit=1)

            lieu = f"Localisation : {location} - {localisation}\n"
            les_produits = ""
            for produit in produits:
                les_produits += "nom : "+ produit['nom'] + ",quantité :"+ str(produit['quantité']) + ",prix : "+ str(produit['prix']) + "\n"

              

            if existing_crm:
                # Enregistrer la ligne de panier
                LeadLine.create({
                    'lead_id': existing_crm.id,
                    'products': les_produits,
                    'date': fields.Datetime.now(),
                    'amount': total,
                    'type': type,
                })
                if crm_data.get('email') != "Guest":
                    crm_with_email_guest_id = CRM.search([('email_from', '=', crm_data.get('guest_id'))], limit=1)
                    if crm_with_email_guest_id:
                        crm_with_email_guest_id.write({
                            'name': f"Opportunité pour {crm_data.get('name')}",
                            'partner_id': partner.id if partner else None,
                            'email_from': crm_data.get('email'),
                            'phone': crm_data.get('phone'),
                            'expected_revenue':  total,
                            'date_maj': fields.Datetime.now(),
                            "description": existing_crm.description + "\t " + lieu 
                        })
                    else:
                        existing_crm.write({
                            'expected_revenue':  total,
                            'date_maj': fields.Datetime.now(),
                            "description": existing_crm.description + "\t " + lieu 
                        })
                message = "Tous les produits ont été ajoutés au CRM existant."
                crm_id = existing_crm.id
            else:
                # Si le CRM n'existe pas, création avec tous les produits
                new_crm = CRM.create({
                    'name': f"Opportunité pour {crm_data.get('name')}",
                    'partner_id': partner.id if partner else None,
                    'email_from': crm_data.get('email') if partner else crm_data.get('guest_id'),
                    'phone': crm_data.get('phone'),
                    'type': 'opportunity',
                    'expected_revenue': total,
                    'date_maj': fields.Datetime.now(),
                    "description": lieu 
                })
                LeadLine.create({
                    'lead_id': new_crm.id,
                    'products': les_produits,
                    'date': fields.Datetime.now(),
                    'amount': total,
                    'type': type,
                })
            
                message = "Nouveau CRM créé avec succès."
                crm_id = new_crm.id

            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({"status": "success", "message": message, "crm_id": crm_id})
            )
        except Exception as e:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                response=json.dumps({"status": "error", "message": str(e)})
            )
        

