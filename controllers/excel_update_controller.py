
from .main import *

from odoo import http, models, fields
from odoo.http import request
import json
import logging
import werkzeug



class CRMUpdateController(http.Controller):


    # @http.route('/api/create_or_update_crm', type='http', auth='none', methods=['POST'], cors="*", csrf=False)
    # def create_or_update_crm(self, **post):
    #     try:
    #         self._authenticate_user()
    #         crm_data = self._get_crm_data()
            
    #         if not crm_data:
    #             return self._json_response("error", "Aucune donnée CRM reçue", status=400)

    #         CRM = request.env['crm.lead'].sudo()
    #         Partner = request.env['res.partner'].sudo()

    #         existing_crm = self._find_existing_crm(CRM, crm_data)
    #         partner = self._find_or_create_partner(Partner, crm_data)

    #         if existing_crm:
    #             crm_id = self._update_existing_crm(existing_crm, crm_data)
    #             message = "Tous les produits ont été ajoutés au CRM existant."
    #         else:
    #             crm_id = self._create_new_crm(CRM, partner, crm_data)
    #             message = "Nouveau CRM créé avec succès."

    #         return self._json_response("success", message, crm_id=crm_id)

    #     except Exception as e:
    #         return self._json_response("error", str(e), status=400)

    # def _authenticate_user(self):
    #     if not request.env.user or request.env.user._is_public():
    #         admin_user = request.env.ref('base.user_admin')
    #         request.env = request.env(user=admin_user.id)

    # def _get_crm_data(self):
    #     data = json.loads(request.httprequest.data)
    #     return data.get('data')

    # def _find_existing_crm(self, CRM, crm_data):
    #     return CRM.search([
    #         '|',
    #         ('email_from', '=', crm_data.get('email')),
    #         ('email_from', '=', crm_data.get('guest_id'))
    #     ], limit=1)

    # def _find_or_create_partner(self, Partner, crm_data):
    #     if crm_data.get('email') != "Guest":
    #         return Partner.search([('email', '=', crm_data.get('email'))], limit=1)
    #     return None

    # def _update_existing_crm(self, existing_crm, crm_data):
    #     existing_description = existing_crm.description or ""
    #     nouveaux_produits = self._format_products(crm_data.get('produits', []), crm_data.get('total'))

    #     existing_crm.write({
    #         'description': existing_description + nouveaux_produits,
    #         'expected_revenue': crm_data.get('total'),
    #         'date_maj': fields.Datetime.now()
    #     })
    #     return existing_crm.id

    # def _create_new_crm(self, CRM, partner, crm_data):
    #     description = self._format_crm_description(crm_data)
    #     new_crm = CRM.create({
    #         'name': f"Opportunité pour {crm_data.get('name')}",
    #         'partner_id': partner.id if partner else None,
    #         'email_from': crm_data.get('email') if partner else crm_data.get('guest_id'),
    #         'phone': crm_data.get('phone'),
    #         'description': description,
    #         'type': 'opportunity',
    #         'expected_revenue': crm_data.get('total'),
    #         'date_maj': fields.Datetime.now()
    #     })
    #     return new_crm.id

    # def _format_products(self, produits, total):
    #     formatted_products = "\n"
    #     for produit in produits:
    #         formatted_products += self._format_product(produit)
    #     formatted_products += f"\n---\n**Total Panier : {total} F CFA**\n"
    #     return formatted_products

    # def _format_product(self, produit):
    #     return (
    #         f"- **{produit['nom']}**\n"
    #         f"  - Quantité : {produit['quantité']}\n"
    #         f"  - Prix unitaire : {produit['prix']} F CFA\n"
    #         f"  - Montant : {produit['prix'] * produit['quantité']} F CFA\n"
    #         f"  - Date : {produit['date']}\n"
    #         f"  - Panier : {produit['panier']}\n"
    #     )

    # def _format_crm_description(self, crm_data):
    #     header = (
    #         f"**Type :** {crm_data.get('type')}\n"
    #         f"**Date :** {crm_data.get('date')}\n"
    #         f"**Localisation :** {crm_data.get('location')}\n"
    #         f"**Coordonnées :** {crm_data.get('localisation')}\n\n"
    #         f"**Produits :**\n"
    #     )
    #     products = self._format_products(crm_data.get('produits', []), crm_data.get('total'))
    #     return header + products

    # def _json_response(self, status, message, crm_id=None, status_code=200):
    #     data = {
    #         "status": status,
    #         "message": message
    #     }
    #     if crm_id:
    #         data["crm_id"] = crm_id

    #     return werkzeug.wrappers.Response(
    #         status=status_code,
    #         content_type='application/json; charset=utf-8',
    #         headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
    #         response=json.dumps(data)
    #     )
    


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
