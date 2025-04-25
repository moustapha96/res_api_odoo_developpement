
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
        


    # @http.route('/api/create_or_update_crm', type='http', auth='none', methods=['POST'], cors="*", csrf=False)
    # def create_or_update_crm(self, **post):
    #     try:
    #         # Validation des données
    #         crm_data, error_response = self._validate_request_data()
    #         if error_response:
    #             return error_response

    #         # Traitement principal
    #         crm_lead, partner = self._process_crm_data(crm_data)

    #         return self._prepare_success_response(crm_lead, partner)

    #     except Exception as e:
    #         _logger.error("CRM Error: %s", str(e), exc_info=True)
    #         return self._prepare_error_response(str(e))

    # def _switch_to_admin_user(self):
    #     """Force l'utilisation du compte admin si utilisateur public"""
    #     user = request.env.user
    #     if user and user._is_public():
    #         try:
    #             admin_user = request.env.ref('base.user_admin').sudo().ensure_one()
    #             request.update_env(user=admin_user.id)
    #         except ValueError:
    #             _logger.error("Multiple admin users found or admin user missing.")
    #             return self._prepare_error_response("Configuration error: Admin user issue", 500)

    # def _validate_request_data(self):
    #     """Validation des données de la requête"""
    #     try:
    #         crm_data = json.loads(request.httprequest.data)
    #     except json.JSONDecodeError:
    #         return None, self._prepare_error_response("Format JSON invalide", 400)

    #     required_fields = ['total', 'type', 'date', 'location', 'produits']
    #     missing_fields = [f for f in required_fields if f not in crm_data]

    #     if missing_fields:
    #         msg = _("Champs manquants: %s") % ", ".join(missing_fields)
    #         return None, self._prepare_error_response(msg, 400)

    #     return crm_data, None

    # def _process_crm_data(self, crm_data):
    #     """Logique principale de traitement des données CRM"""
    #     # Gestion du partenaire
    #     partner = self._find_or_create_partner(crm_data)

    #     # Recherche du CRM existant
    #     crm_lead = self._find_existing_crm(crm_data)

    #     # Création/Mise à jour du CRM
    #     if crm_lead:
    #         self._update_existing_crm(crm_lead, crm_data, partner)
    #     else:
    #         crm_lead = self._create_new_crm(crm_data, partner)

    #     # Ajout des produits
    #     self._create_lead_line(crm_lead, crm_data)

    #     return crm_lead, partner

    # def _find_or_create_partner(self, crm_data):
    #     """Gestion des partenaires (création ou récupération)"""
    #     Partner = request.env['res.partner'].sudo()
    #     email = crm_data.get('email')

    #     if email == "Guest":
    #         return None

    #     if email != "Guest":
    #         partner = Partner.search([('email', '=', email)], limit=1)
    #         if not partner:
    #             return None
    #         return partner

    # def _find_existing_crm(self, crm_data):
    #     """Recherche d'un CRM existant par différents critères"""
    #     CRM = request.env['crm.lead'].sudo()
    #     domains = []

    #     if crm_data.get('email'):
    #         domains.append(('email_from', '=', crm_data['email']))
    #     if crm_data.get('guest_id'):
    #         domains.append(('email_from', '=', crm_data['guest_id']))

    #     return CRM.search(domains, order='id desc', limit=1)

    # def _update_existing_crm(self, crm_lead, crm_data, partner):
    #     """Mise à jour d'un CRM existant"""
    #     update_values = {
    #         'expected_revenue': crm_data['total'],
    #         'date_maj': fields.Datetime.now(),
    #         'description': self._format_description(crm_lead.description, crm_data),
    #         'partner_id': partner.id if partner else crm_lead.partner_id.id,
    #         'email_from': crm_data.get('email') or crm_lead.email_from,
    #         'phone': crm_data.get('phone') or crm_lead.phone,
    #     }
    #     crm_lead.write(update_values)

    # def _create_new_crm(self, crm_data, partner):
    #     """Création d'un nouveau CRM"""
    #     return request.env['crm.lead'].sudo().create({
    #         'name': f"Opportunité pour {crm_data.get('name', 'Nouveau Client')}",
    #         'partner_id': partner.id if partner else None,
    #         'email_from': crm_data.get('email') or crm_data.get('guest_id'),
    #         'phone': crm_data.get('phone'),
    #         'type': 'opportunity',
    #         'expected_revenue': crm_data['total'],
    #         'date_maj': fields.Datetime.now(),
    #         'description': self._format_description('', crm_data),
    #     })

    # def _create_lead_line(self, crm_lead, crm_data):
    #     """Création d'une ligne de produit dans le CRM"""
    #     products = "\n".join(
    #         f"Nom: {p['nom']}, Quantité: {p['quantité']}, Prix: {p['prix']}"
    #         for p in crm_data['produits']
    #     )

    #     request.env['crm.lead.line'].sudo().create({
    #         'lead_id': crm_lead.id,
    #         'products': products,
    #         'date': fields.Datetime.now(),
    #         'amount': crm_data['total'],
    #         'type': crm_data['type'],
    #     })

    # def _format_description(self, existing_desc, crm_data):
    #     """Formatage de la description"""
    #     location = crm_data.get('location', 'Non spécifié')
    #     localisation = crm_data.get('localisation', '')
    #     return f"{existing_desc}\nLocalisation: {location} - {localisation}".strip()

    # def _prepare_success_response(self, crm_lead, partner):
    #     """Prépare la réponse de succès"""
    #     return werkzeug.wrappers.Response(
    #         status=200,
    #         content_type='application/json; charset=utf-8',
    #         headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
    #         response=json.dumps({
    #             "status": "success",
    #             "message": _("CRM mis à jour avec succès") if crm_lead.exists() else _("Nouveau CRM créé"),
    #             "crm_id": crm_lead.id,
    #             "partner_id": partner.id if partner else None
    #         })
    #     )

    # def _prepare_error_response(self, message, status_code=400):
    #     """Prépare la réponse d'erreur"""
    #     return werkzeug.wrappers.Response(
    #         status=status_code,
    #         content_type='application/json; charset=utf-8',
    #         response=json.dumps({
    #             "status": "error",
    #             "message": message
    #         })
    #     )




    