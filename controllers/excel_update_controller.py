
from .main import *
from odoo import http
from odoo.http import request
import json
import logging


class CRMUpdateController(http.Controller):
    @http.route('/api/create_or_update_crm', type='http',  auth='none', methods=['POST'], cors="*", csrf=False)
    def create_or_update_crm(self, **post):
        try:

            if not request.env.user or request.env.user._is_public():
                admin_user = request.env.ref('base.user_admin')
                request.env = request.env(user=admin_user.id)

            data = json.loads(request.httprequest.data)
            crm_data = data.get('data')

            if not crm_data:
                return json.dumps({"status": "error", "message": "Aucune donnée CRM reçue"})

            CRM = request.env['crm.lead'].sudo()
            Partner = request.env['res.partner'].sudo()

         
            existing_crm = CRM.search([('email_from', '=', crm_data.get('email'))], limit=1)


            existing_crm = CRM.search([
                '|',
                ('email_from', '=', crm_data.get('email')),
                ('email_from', '=', crm_data.get('guest_id'))
            ], limit=1)


            partner = None
            if crm_data.get('email') != "Guest":
                partner = Partner.search([('email', '=', crm_data.get('email'))], limit=1)



            montant_esperer = 0
            crm_values = {
                'name': f"Opportunité pour {crm_data.get('name')}",
                'partner_id': partner.id if partner else None,
                'email_from': crm_data.get('email') if partner else crm_data.get('guest_id'),
                'phone': crm_data.get('phone'),
                'description': (
                    f"**Type :** {crm_data.get('type')}\n"
                    f"**Date :** {crm_data.get('date')}\n"
                    f"**Localisation :** {crm_data.get('location')}\n"
                    f"**Coordonnées :** {crm_data.get('localisation')}\n\n"
                    f"**Produits :**\n"
                    + "\n".join(
                        f"- **{produit['nom']}**\n"
                        f"  - Quantité : {produit['quantité']}\n"
                        f"  - Prix unitaire : {produit['prix']} F CFA\n"
                        f"  - Date : {produit['date']}\n"
                        for produit in crm_data.get('produits', [])
                    )
                ),
                'type': 'opportunity',
                'expected_revenue': 0
            }

            if crm_data.get('produits'):
                crm_values['description'] += "\n\nProduits:\n\n"
                for produit in crm_data['produits']:
                    crm_values['description'] += (
                        f"- {produit['nom']} (Quantité: {produit['quantité']}, "
                        f"Prix: {produit['prix']}, Date: {produit['date']} \n\n"
                    )
                    montant_esperer += produit['prix'] * produit['quantité']
                crm_values['expected_revenue'] = montant_esperer

            # Mise à jour ou création du CRM
            if existing_crm:
                existing_crm.write(crm_values)
                crm_id = existing_crm.id
                message = "CRM mis à jour avec succès"
            else:
                new_crm = CRM.create(crm_values)
                crm_id = new_crm.id
                message = "Nouveau CRM créé avec succès"

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