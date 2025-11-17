# -*- coding: utf-8 -*-
from odoo import http, fields , _
from odoo.http import request
import json
import datetime
import werkzeug
import logging
import base64
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def _json(status=200, payload=None):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
        response=json.dumps(payload if payload is not None else {}),
    )

def _json_error(status, message):
    return _json(status, {"error": message})

def _parse_iso(dt_str):
    if not dt_str:
        return None
    try:
        s = dt_str.replace('Z', '+00:00') if str(dt_str).endswith('Z') else str(dt_str)
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None

def _to_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

def _to_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def _ensure_admin_env():
    """Exécute les routes publiques avec l'admin pour éviter les droits Public User."""
    if (not request.env.user) or request.env.user._is_public():
        admin = request.env.ref('base.user_admin')
        request.env = request.env(user=admin.id)

def _manual_build_full_invoice_from_order(order):
    Move = request.env['account.move'].sudo()
    move_vals = order._prepare_invoice()
    move = Move.create(move_vals)
    invoice_lines_vals = []
    for so_line in order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment):
        line_vals = so_line._prepare_invoice_line()
        line_vals.update({
            'move_id': move.id,
            'quantity': so_line.product_uom_qty,
        })
        invoice_lines_vals.append((0, 0, line_vals))
    if invoice_lines_vals:
        move.write({'invoice_line_ids': invoice_lines_vals})
    return move

def _get_or_create_proforma_move(order, create_if_missing=True, mode=None, amount=None, post_if_draft=True):
    move = order.invoice_ids.filtered(lambda m: m.move_type == 'out_invoice')[:1]
    if not move and create_if_missing:
        if order.state in ('draft', 'sent'):
            order.action_confirm()
        try:
            moves = order.with_context(move_type='out_invoice')._create_invoices()
            move = moves[:1]
            if (not move) and mode in ('percentage', 'fixed'):
                wizard_env = request.env['sale.advance.payment.inv'].sudo().with_context(
                    active_model='sale.order', active_ids=order.ids,
                )
                if mode == 'percentage':
                    if amount is None:
                        raise UserError("Paramètre 'amount' requis pour mode=percentage")
                    wizard = wizard_env.create({'advance_payment_method': 'percentage', 'amount': float(amount)})
                else:
                    if amount is None:
                        raise UserError("Paramètre 'amount' requis pour mode=fixed")
                    wizard = wizard_env.create({'advance_payment_method': 'fixed', 'fixed_amount': float(amount)})
                wizard.create_invoices()
                move = order.invoice_ids.filtered(lambda m: m.move_type == 'out_invoice').sorted('id')[-1:]
        except UserError:
            move = _manual_build_full_invoice_from_order(order)
    if move and post_if_draft and getattr(move, 'state', '') == 'draft':
        move.sudo().action_post()
    return move

def _serialize_move_for_api(move):
    partner = move.partner_id
    company = move.company_id
    currency = move.currency_id and move.currency_id.name or (company.currency_id and company.currency_id.name) or None
    return {
        "id": move.id,
        "name": move.name,
        "state": move.state,
        "move_type": move.move_type,
        "invoice_date": move.invoice_date and move.invoice_date.isoformat() or None,
        "invoice_date_due": move.invoice_date_due and move.invoice_date_due.isoformat() or None,
        "amount_untaxed": move.amount_untaxed,
        "amount_tax": move.amount_tax,
        "amount_total": move.amount_total,
        "currency": currency,
        "company": {
            "id": company.id,
            "name": company.display_name,
        },
        "partner": {
            "id": partner.id,
            "name": partner.display_name,
            "email": partner.email,
            "phone": partner.phone or partner.mobile,
        },
        "download_url": f"/api/creditcommandes/proforma/{move.invoice_origin and move.invoice_origin or move.id}?from=move",
    }

def _get_invoice_report_action():
    Report = request.env['ir.actions.report'].sudo()
    action = Report.search([
        ('report_name', 'in', ['account.report_invoice', 'account.report_invoice_with_payments'])
    ], limit=1)
    if action:
        return action
    try:
        action = request.env.ref('account.action_report_invoice')
        return action.sudo()
    except Exception:
        pass
    action = Report.search([('report_name', '=', 'account.report_invoice_document')], limit=1)
    if action:
        return action
    return None

class CreditCommandeREST(http.Controller):

    @http.route('/api/creditcommandes/details', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_get_credit_order_details(self, **kw):
        try:
            data = json.loads(request.httprequest.data)
            partner_id = _to_int(data.get('partner_id'))
            order_id = _to_int(data.get('order_id'))
            if not partner_id or not order_id:
                return _json_error(400, "Données de commande invalides")
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
            order = request.env['sale.order'].sudo().search([
                ('id', '=', order_id),
                ('partner_id', '=', partner_id),
                ('type_sale', '=', 'creditorder')
            ], limit=1)
            if not partner or not order:
                return _json_error(400, "Client et commande invalides")

            payment_lines = []
            if hasattr(order, 'get_sale_order_credit_payment'):
                payment_lines = order.get_sale_order_credit_payment()

            order_lines = [{
                'id': l.id or None,
                'product_id': l.product_id.id or None,
                'product_name': l.product_id.name or None,
                'product_uom_qty': l.product_uom_qty or None,
                'product_uom': l.product_uom.id or None,
                'product_uom_name': l.product_uom.name or None,
                'price_unit': l.price_unit or None,
                'price_subtotal': l.price_subtotal or None,
                'price_tax': l.price_tax or None,
                'price_total': l.price_total or None,
                'qty_delivered': l.qty_delivered or None,
                'qty_to_invoice': l.qty_to_invoice or None,
                'qty_invoiced': l.qty_invoiced or None,
                'is_downpayment': l.is_downpayment or None,
            } for l in order.order_line if not l.is_downpayment]

            partner_info = {
                'id': partner.id or None,
                'name': partner.name or None,
                'street': partner.street or None,
                'street2': partner.street2 or None,
                'city': partner.city or None,
                'state_id': partner.state_id.id or None,
                'state_name': partner.state_id.name or None,
                'zip': partner.zip or None,
                'country_id': partner.country_id.id or None,
                'country_name': partner.country_id.name or None,
                'vat': partner.vat or None,
                'email': partner.email or None,
                'phone': partner.phone or None,
                'nom': partner.nom or None,
                'prenom': partner.prenom or None,
                'date_naissance': partner.date_naissance.isoformat() if partner.date_naissance else None,
                'lieu_naissance': partner.lieu_naissance or None,
                'cni_number': partner.cni_number or None,
                'profession': partner.profession or None,
                'rib': partner.rib or None,
                'adresse' : partner.adresse
            }

            order_info = {
                'id': order.id or None,
                'credit_type': order.credit_type or None,
                'name': order.name or None,
                'type_sale': order.type_sale or None,
                'date_order': order.date_order.isoformat() if order.date_order else None,
                'validation_rh_state': order.validation_rh_state or None,
                'validation_admin_state': order.validation_admin_state or None,
                'commitment_date': order.commitment_date.isoformat() if order.commitment_date else None,
                'state': order.state or None,
                'create_date': order.create_date.isoformat() if order.create_date else None,
                'payment_term_id': order.payment_term_id.id if order.payment_term_id else None,
                'payment_term_name': order.payment_term_id.name if order.payment_term_id else None,
                'amount_untaxed': order.amount_untaxed or None,
                'amount_tax': order.amount_tax or None,
                'amount_total': order.amount_total or None,
                'amount_residual': order.amount_residual or None,
                'advance_payment_status': order.advance_payment_status or None,
                'credit_month_rate': order.credit_month_rate or None,
                'creditorder_month_count': order.creditorder_month_count or None,
                'payment_lines': payment_lines,
                'order_lines': order_lines,
            }

            employer_info = None
            if partner.employer_partner_id:
                employer = partner.employer_partner_id
                employer_info = {
                    'id': employer.id or None,
                    'name': employer.name or None,
                    'street': employer.street or None,
                    'street2': employer.street2 or None,
                    'city': employer.city or None,
                    'state_id': employer.state_id.id or None,
                    'state_name': employer.state_id.name or None,
                    'zip': employer.zip or None,
                    'country_id': employer.country_id.id or None,
                    'country_name': employer.country_id.name or None,
                    'vat': employer.vat or None,
                    'email': employer.email or None,
                    'phone': employer.phone or None,
                }

            response_data = {
                'partner': partner_info,
                'order': order_info,
                'employer': employer_info,
            }
            return _json(200, response_data)
        except Exception as e:
            _logger.error("Erreur lors de la récupération des détails de la commande à crédit: %s", e, exc_info=True)
            return _json_error(500, "Erreur interne du serveur")



    @http.route('/api/creditcommandes', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_create_credit_order(self, **kw):
        try:
            data = json.loads(request.httprequest.data)
            partner_id = _to_int(data.get('partner_id'))
            parent_id = _to_int(data.get('parent_id'))
            company_id = _to_int(data.get('company_id')) if data.get('company_id') else None
            order_lines = data.get('order_lines', [])
            type_sale = (data.get('type_sale') or 'creditorder').strip()
            type_credit = (data.get('type_credit') or '').strip().lower()
            payment_mode = (data.get('payment_mode') or 'online').strip()
            commitment_date_str = data.get('commitment_date')
            acomptePercentage = _to_int(data.get('acomptePercentage') or 50)
            nombreMois = _to_int(data.get('nombreMois') or 4)
            bank_dossier = data.get('bank_dossier', {})

            # Normalisation du type de crédit
            # 'finance' et variantes sont normalisés en 'banque' pour la cohérence
            if type_credit in ('banque', 'bank', 'finance', 'financé', 'financer'):
                type_credit = 'banque'
            elif type_credit == 'direct':
                type_credit = 'direct'
            elif type_credit == 'particulier':
                # Type particulier accepté mais pas de notification RH
                type_credit = 'particulier'
            else:
                return _json_error(400, "type_credit invalide : 'direct', 'banque' ou 'particulier' attendu")

            if not partner_id or not order_lines:
                return _json_error(400, "Données de commande crédit invalides")

            _ensure_admin_env()
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
            if not partner:
                return _json_error(400, "Partenaire introuvable")

            # Mise à jour des informations du partenaire
            self._update_partner_from_payload(partner, bank_dossier)

            if company_id:
                employer_partner = request.env['res.partner'].sudo().search([('id', '=', company_id)], limit=1)
                if employer_partner:
                    partner.write({'employer_partner_id': employer_partner.id})
                else:
                    partner.write({'employer_partner_id': parent_id or False})

            company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            if not company:
                return _json_error(400, "Société introuvable")

            commitment_date = _parse_iso(commitment_date_str) if commitment_date_str else fields.Datetime.now() + datetime.timedelta(days=3)
            if commitment_date and commitment_date.tzinfo:
                commitment_date = commitment_date.replace(tzinfo=None)

            order_vals = {
                'state': 'validation',
                'partner_id': partner.id,
                'type_sale': type_sale,
                'company_id': company.id,
                'currency_id': company.currency_id.id,
                'payment_mode': payment_mode,
                'validation_rh_state': 'pending',
                'validation_admin_state': 'pending',
                'credit_type': type_credit,
                'commitment_date': commitment_date,
            }

            if type_credit == 'direct':
                order_vals.update({
                    'credit_month_rate': max(30, min(100, acomptePercentage)),
                    'creditorder_month_count': max(1, min(5, nombreMois)),
                })
            else:
                order_vals.update({
                    'credit_month_rate': 100,
                    'creditorder_month_count': 1,
                })

            order = request.env['sale.order'].sudo().create(order_vals)

            for item in order_lines:
                product_id = _to_int(item.get('id'))
                product_uom_qty = _to_float(item.get('quantity') or 0)
                price_unit = item.get('list_price')
                if not product_id or product_uom_qty <= 0:
                    return _json_error(400, "Ligne article invalide")
                product = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
                if not product:
                    return _json_error(400, "Produit introuvable")
                if price_unit is None:
                    if type_credit == 'direct' or type_credit == "banque":
                        price_unit = float(product.product_tmpl_id.creditorder_price)
                    else:
                        price_unit = float(product.product_tmpl_id.list_price or 0.0)

                request.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'product_uom_qty': product_uom_qty,
                    'price_unit': _to_float(price_unit),
                    'company_id': company.id,
                    'currency_id': company.currency_id.id,
                    'state': 'sale',
                    'invoice_status': 'to invoice',
                })

            # Envoi des mails selon le type de crédit (utilise les nouvelles méthodes unifiées de sale_a_credit.py)
            # Les mails sont automatiquement personnalisés selon le type de crédit :
            # - direct : mail client + notification RH normale (employeur)
            # - banque/finance : mail client + notification RH en tant qu'entité bancaire
            # - particulier : mail client uniquement (pas de notification RH)
            try:
                # 1. Notification au client de la création de la commande
                # Le contenu est automatiquement personnalisé selon le type de crédit
                if hasattr(order, 'send_credit_order_creation_notification_to_client'):
                    try:
                        order.send_credit_order_creation_notification_to_client()
                        _logger.info("Mail de création envoyé au client pour %s (type: %s)", order.name, type_credit)
                    except Exception as e:
                        _logger.warning("Erreur envoi mail création client %s: %s", order.name, e, exc_info=True)
                
                # 2. Notification à la RH selon le type de crédit
                # La méthode send_credit_order_creation_notification_to_hr() gère automatiquement :
                # - direct, banque, finance -> envoie notification RH (avec mention "entité bancaire" pour banque/finance)
                # - particulier -> retourne success avec message "No HR notification needed"
                if hasattr(order, 'send_credit_order_creation_notification_to_hr'):
                    try:
                        result = order.send_credit_order_creation_notification_to_hr()
                        if result.get('status') == 'success':
                            _logger.info("Mail de notification RH envoyé pour %s (type: %s)", order.name, type_credit)
                        else:
                            _logger.info("Pas de notification RH nécessaire pour %s (type: %s): %s", 
                                       order.name, type_credit, result.get('message', ''))
                    except Exception as e:
                        _logger.warning("Erreur envoi mail notification RH %s: %s", order.name, e, exc_info=True)
            except Exception as e:
                _logger.error("Erreur globale lors de l'envoi des mails pour %s: %s", order.name, e, exc_info=True)

            resp = self._serialize_order(order, include_lines=True, include_payments=True, include_partner_blocks=True)
            return _json(201, resp)
        except Exception as e:
            _logger.error("Erreur lors de la création de la commande à crédit: %s", e, exc_info=True)
            return _json_error(500, "Erreur interne du serveur")



    def _update_partner_from_payload(self, partner, bank_dossier=None):
        try:
            updates = {}
            if bank_dossier:
                if bank_dossier.get('nom'):
                    updates['nom'] = bank_dossier['nom']
                if bank_dossier.get('prenom'):
                    updates['prenom'] = bank_dossier['prenom']
                if bank_dossier.get('dateNaissance'):
                    updates['date_naissance'] = bank_dossier['dateNaissance']
                if bank_dossier.get('lieuNaissance'):
                    updates['lieu_naissance'] = bank_dossier['lieuNaissance']
                if bank_dossier.get('email'):
                    updates['email'] = bank_dossier['email']
                if bank_dossier.get('cniNumber'):
                    updates['cni_number'] = bank_dossier['cniNumber']
                if bank_dossier.get('profession'):
                    updates['profession'] = bank_dossier['profession']
                if bank_dossier.get('rib'):
                    updates['rib'] = bank_dossier['rib']
                if bank_dossier.get('adresse'):
                    updates['adresse'] = bank_dossier['adresse']
              
            if updates:
                partner.sudo().write(updates)
            _logger.info("Profil partenaire mis à jour : %s", partner.display_name)
            return True
        except Exception as e:
            _logger.error("Erreur lors de la mise à jour du partenaire : %s", e, exc_info=True)
            return False

    def _serialize_order(self, order, include_lines=False, include_payments=False,
                         include_partner_blocks=False, include_attachments=False):
        partner = order.partner_id
        employer_partner = getattr(partner, 'employer_partner_id', False) and partner.employer_partner_id or False
        company = order.company_id
        currency = company.currency_id and company.currency_id.name or None

        lines = []
        if include_lines:
            for l in order.order_line:
                lines.append({
                    "id": l.id,
                    "product_id": l.product_id.id,
                    "product_name": l.product_id.display_name,
                    "quantity": l.product_uom_qty,
                    "price_unit": l.price_unit,
                    "price_subtotal": l.price_subtotal,
                    "price_tax": l.price_tax,
                    "price_total": l.price_total,
                })

        payment_lines = []
        if include_payments:
            try:
                if hasattr(order, 'get_sale_order_credit_payment'):
                    payment_lines = order.get_sale_order_credit_payment()
            except Exception as e:
                _logger.warning("get_sale_order_credit_payment KO: %s", e)

        partner_blocks = None
        if include_partner_blocks:

            partner_blocks = {
                "header": {
                    "name": partner.display_name,
                    "company_parent": partner.parent_id and partner.parent_id.display_name or None,
                },
                "contact": {
                    "email": partner.email,
                    "phone": partner.phone or partner.mobile,
                },
                "employment": {
                    "employer": employer_partner and employer_partner.display_name or None,
                },
                "personal": {
                    "nom": getattr(partner, 'nom', None),
                    "prenom": getattr(partner, 'prenom', None),
                    "date_naissance": getattr(partner, 'date_naissance', None) and partner.date_naissance.isoformat() or None,
                    "lieu_naissance": getattr(partner, 'lieu_naissance', None),
                    "cni_number": getattr(partner, 'cni_number', None),
                    "profession": getattr(partner, 'profession', None),
                    "rib": getattr(partner, 'rib', None),
                },
            }

        return {
            "id": order.id,
            "name": order.name,
            "type_sale": getattr(order, 'type_sale', None),
            "type_credit": getattr(order, 'credit_type', None),
            "partner": {
                "id": partner.id,
                "name": partner.display_name,
                "email": partner.email,
                "phone": partner.phone or partner.mobile,
                "nom": getattr(partner, 'nom', None),
                "prenom": getattr(partner, 'prenom', None),
                "date_naissance": getattr(partner, 'date_naissance', None) and partner.date_naissance.isoformat() or None,
                "lieu_naissance": getattr(partner, 'lieu_naissance', None),
                "cni_number": getattr(partner, 'cni_number', None),
                "profession": getattr(partner, 'profession', None),
                "rib": getattr(partner, 'rib', None),
            },
            "employer": employer_partner and {
                "id": employer_partner.id,
                "name": employer_partner.display_name,
                "email": employer_partner.email,
                "phone": employer_partner.phone or employer_partner.mobile,
            } or None,
            "company": {
                "id": company.id,
                "name": company.name,
                "currency": currency,
            },
            "state": order.state,
            "validation_rh_state": getattr(order, 'validation_rh_state', None),
            "validation_admin_state": getattr(order, 'validation_admin_state', None),
            "bank_validation_state": getattr(order, 'bank_validation_state', None),
            "commitment_date": order.commitment_date and order.commitment_date.isoformat() or None,
            "amounts": {
                "untaxed": order.amount_untaxed,
                "tax": order.amount_tax,
                "total": order.amount_total,
                "residual": getattr(order, 'amount_residual', 0.0),
            },
            "credit_params": {
                "acomptePercentage": getattr(order, 'credit_month_rate', None),
                "nombreMois": getattr(order, 'creditorder_month_count', None),
            },
            "order_lines": lines if include_lines else None,
            "payment_lines": payment_lines if include_payments else None,
            "partner_blocks": partner_blocks,
        }

    @http.route('/api/creditcommandes/clients/<int:id>/liste', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandesCredit_liste(self, id, **kw):
        
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        
        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Commandes non trouvé"})
            )
        order_data = []
        orders = request.env['sale.order'].sudo().search([('partner_id','=', partner.id), ('type_sale', '=', 'creditorder')])
        if orders:
            for o in orders:
                order_data.append({
                    'id': o.id,
                    'validation_rh_state': o.validation_rh_state,
                    'validation_admin_state': o.validation_admin_state,
                    'type_sale': o.type_sale,
                    'date_order': o.date_order.isoformat() if o.date_order else None,
                    'name': o.name,
                    'payment_mode': o.payment_mode,
                    'partner_id': o.partner_id.id or None,
                    'partner_name': o.partner_id.name or None,
                    'partner_city': o.partner_id.city or None,
                    'partner_country_id': o.partner_id.country_id.id or None,
                    'partner_country_name': o.partner_id.country_id.name or None,
                    'partner_email': o.partner_id.email or None,
                    'partner_phone': o.partner_id.phone or None,
                    'amount_untaxed': o.amount_untaxed or None,
                    'amount_tax': o.amount_tax or None,
                    'amount_total': o.amount_total or None,
                    'state': o.state or None,
                    'advance_payment_status': o.advance_payment_status,
                    'amount_residual': o.amount_residual,
                    'create_date': o.create_date.isoformat() if o.create_date else None,
                    'payment_lines': o.get_sale_order_credit_payment(),
                    'credit_type': o.credit_type,
                    'order_lines': [{
                        'id': l.id or None,
                        'product_id': l.product_id.id or None,
                        'product_name': l.product_id.name or None,
                        'product_uom_qty': l.product_uom_qty or None,
                        'product_uom': l.product_uom.id or None,
                        'product_uom_name': l.product_uom.name or None,
                        'price_unit': l.price_unit or None,
                        'price_subtotal': l.price_subtotal or None,
                        'price_tax': l.price_tax or None,
                        'price_total': l.price_total or None,
                        'qty_delivered': l.qty_delivered or None,
                        'qty_to_invoice': l.qty_to_invoice or None,
                        'qty_invoiced': l.qty_invoiced or None
                    } for l in o.order_line]
                })
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(order_data)
            )
        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps([])
        )

    @http.route('/api/creditcommandes/clients/<int:id>/stateCommande', methods=['GET'], type='http', auth='none', cors="*")
    def api_get_commandesCredit_existe(self, id, **kw):
        if not request.env.user or request.env.user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        partner = request.env['res.partner'].sudo().search([('id', '=', id)], limit=1)
        if not partner:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "error", "message": "Client non rencontré"})
            )
        orders = request.env['sale.order'].sudo().search([('partner_id','=', partner.id), ('type_sale', '=', 'creditorder'), ('amount_residual', '>', 0)])
        if orders:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "code": 400, "message": "Vous avez des commandes à crédit non payées"})
            )
        else:
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({ "status": "success", "code": 200, "message": "Vous n'avez aucune commande à crédit non payée"})
            )

    @http.route('/api/commande-a-credit', methods=['POST'], type='http', auth='none', cors="*", csrf=False)
    def api_create_credit_order(self, **kw):
        try:
            data = json.loads(request.httprequest.data)
            partner_id = _to_int(data.get('partner_id'))
            parent_id = _to_int(data.get('parent_id'))
            company_id = _to_int(data.get('company_id')) if data.get('company_id') else None
            order_lines = data.get('order_lines', [])
            type_sale = (data.get('type_sale') or 'creditorder').strip()
            type_credit = (data.get('type_credit') or '').strip().lower()
            payment_mode = (data.get('payment_mode') or 'online').strip()
            commitment_date_str = data.get('commitment_date')
            acomptePercentage = _to_int(data.get('acomptePercentage') or 50)
            nombreMois = _to_int(data.get('nombreMois') or 4)
            bank_dossier = data.get('bank_dossier', {})

            # Normalisation du type de crédit
            # 'finance' et variantes sont normalisés en 'banque' pour la cohérence
            if type_credit in ('banque', 'bank', 'finance', 'financé', 'financer'):
                type_credit = 'banque'
            elif type_credit == 'direct':
                type_credit = 'direct'
            elif type_credit == 'particulier':
                # Type particulier accepté mais pas de notification RH
                type_credit = 'particulier'
            else:
                return _json_error(400, "type_credit invalide : 'direct', 'banque' ou 'particulier' attendu")

            if not partner_id or not order_lines:
                return _json_error(400, "Données de commande crédit invalides")

            _ensure_admin_env()
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id)], limit=1)
            if not partner:
                return _json_error(400, "Partenaire introuvable")

            self._update_partner_from_payload(partner, bank_dossier)

            if company_id:
                employer_partner = request.env['res.partner'].sudo().search([('id', '=', company_id)], limit=1)
                if employer_partner:
                    partner.write({'employer_partner_id': employer_partner.id})
                else:
                    partner.write({'employer_partner_id': parent_id or False})

            company = request.env['res.company'].sudo().search([('id', '=', 1)], limit=1)
            if not company:
                return _json_error(400, "Société introuvable")

            commitment_date = _parse_iso(commitment_date_str) if commitment_date_str else fields.Datetime.now() + datetime.timedelta(days=3)
            if commitment_date and commitment_date.tzinfo:
                commitment_date = commitment_date.replace(tzinfo=None)

            order_vals = {
                'state': 'validation',
                'partner_id': partner.id,
                'type_sale': type_sale,
                'company_id': company.id,
                'currency_id': company.currency_id.id,
                'payment_mode': payment_mode,
                'validation_rh_state': 'pending',
                'validation_admin_state': 'pending',
                'credit_type': type_credit,
                'commitment_date': commitment_date,
            }

            if type_credit == 'direct':
                order_vals.update({
                    'credit_month_rate': max(30, min(100, acomptePercentage)),
                    'creditorder_month_count': max(1, min(5, nombreMois)),
                })
            else:
                order_vals.update({
                    'credit_month_rate': 100,
                    'creditorder_month_count': 1,
                })

            order = request.env['sale.order'].sudo().create(order_vals)

            for item in order_lines:
                product_id = _to_int(item.get('id'))
                product_uom_qty = _to_float(item.get('quantity') or 0)
                price_unit = item.get('list_price')
                if not product_id or product_uom_qty <= 0:
                    return _json_error(400, "Ligne article invalide")
                product = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
                if not product:
                    return _json_error(400, "Produit introuvable")
                if price_unit is None:
                    if type_credit == 'direct' or type_credit == "banque":
                        price_unit = float(product.product_tmpl_id.creditorder_price)
                    else:
                        price_unit = float(product.product_tmpl_id.list_price or 0.0)

                request.env['sale.order.line'].sudo().create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'product_uom_qty': product_uom_qty,
                    'price_unit': _to_float(price_unit),
                    'company_id': company.id,
                    'currency_id': company.currency_id.id,
                    'state': 'sale',
                    'invoice_status': 'to invoice',
                })

            # Envoi des mails selon le type de crédit (utilise les nouvelles méthodes unifiées de sale_a_credit.py)
            # Les mails sont automatiquement personnalisés selon le type de crédit :
            # - direct : mail client + notification RH normale (employeur)
            # - banque/finance : mail client + notification RH en tant qu'entité bancaire
            # - particulier : mail client uniquement (pas de notification RH)
            try:
                # 1. Notification au client de la création de la commande
                # Le contenu est automatiquement personnalisé selon le type de crédit
                if hasattr(order, 'send_credit_order_creation_notification_to_client'):
                    try:
                        order.send_credit_order_creation_notification_to_client()
                        _logger.info("Mail de création envoyé au client pour %s (type: %s)", order.name, type_credit)
                    except Exception as e:
                        _logger.warning("Erreur envoi mail création client %s: %s", order.name, e, exc_info=True)
                
                # 2. Notification à la RH selon le type de crédit
                # La méthode send_credit_order_creation_notification_to_hr() gère automatiquement :
                # - direct, banque, finance -> envoie notification RH (avec mention "entité bancaire" pour banque/finance)
                # - particulier -> retourne success avec message "No HR notification needed"
                if hasattr(order, 'send_credit_order_creation_notification_to_hr'):
                    try:
                        result = order.send_credit_order_creation_notification_to_hr()
                        if result.get('status') == 'success':
                            _logger.info("Mail de notification RH envoyé pour %s (type: %s)", order.name, type_credit)
                        else:
                            _logger.info("Pas de notification RH nécessaire pour %s (type: %s): %s", 
                                       order.name, type_credit, result.get('message', ''))
                    except Exception as e:
                        _logger.warning("Erreur envoi mail notification RH %s: %s", order.name, e, exc_info=True)
            except Exception as e:
                _logger.error("Erreur globale lors de l'envoi des mails pour %s: %s", order.name, e, exc_info=True)

            resp = self._serialize_order(order, include_lines=True, include_payments=True, include_partner_blocks=True)
            return _json(201, resp)
        except Exception as e:
            _logger.error("Erreur lors de la création de la commande à crédit: %s", e, exc_info=True)
            return _json_error(500, "Erreur interne du serveur")
    

    def _build_invoice_pdf(self, order):
        """
        Construit un PDF Proforma/Devis pour une commande à crédit (CCBM).
        Retourne les bytes du PDF.
        """
        # Imports locaux
        from io import BytesIO
        from datetime import datetime
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        )
        from reportlab.pdfgen import canvas as pdfcanvas
        import requests
        from odoo import _
        from odoo.http import request  # <- utile si tu l'utilises ailleurs

        buf = BytesIO()

        # -------- Société & contexte --------
        company = order.company_id or request.env.company
        comp_partner = company.partner_id
        # ⚠️ Forcer la dénomination à "CCBM SHOP" en bleu
        comp_name = "CCBM SHOP"
        order_name = (order.name or f"{order.id}").strip()
        date_commande = (order.date_order and order.date_order.strftime("%d/%m/%Y")) or datetime.today().strftime("%d/%m/%Y")

        # -------- Mise en page --------
        margin = 18 * mm
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=margin, rightMargin=margin,
            topMargin=5 * mm, bottomMargin=10 * mm
        )

        styles = getSampleStyleSheet()
        ccbm_blue = colors.HexColor("#005EB8")

        Base = ParagraphStyle(
            name="Base", parent=styles["Normal"],
            fontName="Helvetica", fontSize=10, leading=14, textColor=colors.black
        )
        HLabel = ParagraphStyle(
            name="HLabel", parent=Base, fontSize=9, textColor=colors.HexColor("#555")
        )
        HLabelBlack = ParagraphStyle(
            name="HLabelBlack", parent=Base, fontSize=9, textColor=colors.black
        )
        # 🔵 Titre en bleu (PRO-FORMA)
        Title = ParagraphStyle(
            name="Title", parent=Base, fontSize=14, leading=18, alignment=0,
            spaceAfter=6, textColor=ccbm_blue
        )
        # 🔵 Nom de la société en bleu
        CompanyTitle = ParagraphStyle(
            name="CompanyTitle", parent=Base, fontName="Helvetica-Bold",
            fontSize=12, leading=14, textColor=ccbm_blue, spaceAfter=1
        )
        CompanyAddr = ParagraphStyle(
            name="CompanyAddr", parent=HLabel, fontSize=11, leading=12
        )
        ClientTitle = ParagraphStyle(  # Titre "Client" plus visible
            name="ClientTitle", parent=Base, fontName="Helvetica-Bold",
            fontSize=12, leading=14, textColor=colors.black
        )
        Small = ParagraphStyle(
            name="Small", parent=Base, fontSize=8, leading=10
        )
        Total = ParagraphStyle(
            name="Total", parent=Base, fontSize=11, leading=15
        )
        FooterStyle = ParagraphStyle(
            name="FooterStyle", parent=Base, fontSize=8, alignment=1, spaceAfter=2
        )

        def fmt_money(n, currency_name=None):
            try:
                v = float(n or 0)
                s = f"{int(round(v)):,}".replace(",", " ")
                cur = (currency_name or "").upper()
                if cur in ("XOF", "CFA", ""):
                    return f"{s} CFA"
                return f"{s} {currency_name}"
            except Exception:
                return f"{n} {currency_name or ''}".strip()

        def fmt_qty(q):
            try:
                q = float(q or 0)
                return f"{int(q)}" if abs(q - int(q)) < 1e-9 else f"{q:.2f}"
            except Exception:
                return str(q)

        def safe(v):
            return (v or "").strip()

        # ---- Logo (optionnel) ----
        story = []
        logo_img = None
        if company.logo:
            try:
                logo_img = Image(BytesIO(company.logo), width=110, height=80)
                logo_img.hAlign = "RIGHT"
            except Exception:
                logo_img = None
        if not logo_img:
            try:
                resp = requests.get("https://ccbmshop.com/logo.png", timeout=2)
                if resp.ok and resp.content:
                    logo_img = Image(BytesIO(resp.content), width=90, height=80)
                    logo_img.hAlign = "RIGHT"
            except Exception:
                pass
        if logo_img:
            story.append(logo_img)
            story.append(Spacer(1, 2 * mm))

        # Séparateur haut
        sep = Table([[""]], colWidths=[doc.width])
        sep.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black)]))
        story.append(sep)
        story.append(Spacer(1, 2 * mm))

        # En-tête société (nom + adresse si dispo)
        story.append(Paragraph(comp_name, CompanyTitle))  # 🔵 bleu
        comp_addr_lines = []
        if comp_partner:
            if comp_partner.street:
                comp_addr_lines.append(safe(comp_partner.street))
            cityline = " ".join(filter(None, [
                safe(comp_partner.city),
                (comp_partner.state_id and comp_partner.state_id.name) or "",
                safe(comp_partner.zip),
            ]))
            if cityline.strip():
                comp_addr_lines.append(cityline.strip())
            country = (comp_partner.country_id and comp_partner.country_id.name) or ""
            if country:
                comp_addr_lines.append(country)
        for line in comp_addr_lines:
            story.append(Paragraph(line, CompanyAddr))
        story.append(Spacer(1, 5 * mm))

        # Séparateur clair
        sep2 = Table([[""]], colWidths=[doc.width])
        sep2.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc"))]))
        story.append(sep2)
        story.append(Spacer(1, 4 * mm))

        # ----- TITRE ----- (🔵 bleu)
        story.append(Paragraph(f'<b>PRO-FORMA: {order_name}</b>', Title))
        story.append(Spacer(1, 3 * mm))

        # ====================== Métadonnées + Client ======================
        meta_data = [
            [Paragraph(_("Date Commande:"), HLabelBlack), Paragraph(date_commande, Base)],
        ]
        meta_tbl = Table(meta_data, colWidths=[38 * mm, 67 * mm])
        meta_tbl.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        # Bloc Client
        client_rows = [[Paragraph(_("Client"), ClientTitle)]]
        p = order.partner_id
        client_nom = safe(getattr(p, 'nom', '') or (p.nom if hasattr(p, 'nom') else ''))
        client_prenom = safe(getattr(p, 'prenom', '') or (p.prenom if hasattr(p, 'prenom') else ''))
        client_fullname = (f"{client_prenom} {client_nom}".strip()) or safe(p.name)
        client_email = safe(getattr(p, 'email', ''))
        client_phone = safe(getattr(p, 'telephone', '') or getattr(p, 'phone', '') or getattr(p, 'mobile', ''))
        client_rib = safe(getattr(p, 'rib', ''))
        client_street = safe(p.street)
        client_city = safe(p.city)
        client_country = safe(p.country_id and p.country_id.name)

        if client_fullname:
            client_rows.append([Paragraph(client_fullname, Base)])
        if client_email:
            client_rows.append([Paragraph(f"Email: {client_email}", Base)])
        if client_phone:
            client_rows.append([Paragraph(f"Téléphone: {client_phone}", Base)])
        if client_rib:
            client_rows.append([Paragraph(f"RIB: {client_rib}", Base)])
        if client_street:
            client_rows.append([Paragraph(client_street, Base)])
        if client_city or client_country:
            client_rows.append([Paragraph(", ".join(filter(None, [client_city, client_country])), Base)])

        client_tbl = Table(client_rows, colWidths=[95 * mm])
        client_tbl.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))

        combined_tbl = Table([[meta_tbl, client_tbl]], colWidths=[105 * mm, doc.width - 105 * mm])
        combined_tbl.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        story.append(combined_tbl)
        story.append(Spacer(1, 5 * mm))

        # ====================== Tableau des lignes ======================
        currency_name = safe(order.currency_id and order.currency_id.name) or "CFA"
        header = ["Description", "Quantité", "Prix Unitaire", "Taxes", "Montant"]
        data = [header]

        for line in order.order_line:
            desc = safe(line.name or (line.product_id and line.product_id.display_name))
            qty = fmt_qty(line.product_uom_qty)
            uom = safe(line.product_uom and line.product_uom.name)
            qty_txt = f"{qty} {uom}".strip()
            unit = fmt_money(line.price_unit, currency_name)

            tax_label = ""
            tax_names = [safe(t.name) for t in line.tax_id if safe(t.name)]
            if tax_names:
                tax_label = ", ".join(tax_names)
            else:
                tax_pct = sum(float(t.amount or 0.0) for t in line.tax_id)
                tax_label = f"{tax_pct:.0f}%" if abs(tax_pct - int(tax_pct)) < 1e-9 else f"{tax_pct:.2f}%"

            amt = fmt_money(line.price_subtotal, currency_name)
            data.append([
                Paragraph(desc, Base),
                Paragraph(qty_txt, Base),
                Paragraph(unit, Base),
                Paragraph(tax_label or "-", Base),
                Paragraph(amt, Base),
            ])

        tbl = Table(data, colWidths=[80 * mm, 24 * mm, 32 * mm, 30 * mm, 32 * mm])
        tbl.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#000")),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#cccccc")),
            ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 6 * mm))

        # ====================== Totaux ======================
        taxes = order.order_line.mapped('tax_id')
        unique_rates = set(round(float(t.amount or 0.0), 6) for t in taxes if t.amount is not None)
        if len(unique_rates) == 1:
            t_rate = list(unique_rates)[0]
            tva_label = f"TVA {int(t_rate) if abs(t_rate - int(t_rate)) < 1e-9 else t_rate}%"
        else:
            tva_label = "TVA"

        total_data = [
            [Paragraph("<b>Montant HT</b>", Total), Paragraph(f"<b>{fmt_money(order.amount_untaxed, currency_name)}</b>", Total)],
            [Paragraph(f"<b>{tva_label}</b>", Total), Paragraph(f"<b>{fmt_money(order.amount_tax, currency_name)}</b>", Total)],
            [Paragraph("<b>Total</b>", Total), Paragraph(f"<b>{fmt_money(order.amount_total, currency_name)}</b>", Total)],
        ]
        total_tbl = Table(total_data, colWidths=[154 * mm, 32 * mm])
        total_tbl.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 0.6, colors.HexColor("#000")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(total_tbl)
        story.append(Spacer(1, 8 * mm))

        # ----- Signature / Date -----
        story.append(Paragraph(_("Date: ") + datetime.today().strftime("%d-%m-%Y %H:%M"), Small))
        story.append(Spacer(1, 6 * mm))

        # ====================== Footer fixé en bas + pagination ======================
        FOOTER_ONE_LINE = "AGITECH / +221 70 922 17 75 / +221 33 849 65 49 / shop@ccbm.sn / https://www.ccbmshop.com"

        class NumberedCanvas(pdfcanvas.Canvas):
            def __init__(self, *args, **kwargs):
                pdfcanvas.Canvas.__init__(self, *args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                pdfcanvas.Canvas.showPage(self)

            def save(self):
                n_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self._draw_footer_and_page(n_pages)
                    pdfcanvas.Canvas.showPage(self)
                pdfcanvas.Canvas.save(self)

            def _draw_footer_and_page(self, page_count):
                w, h = A4
                self.setFont("Helvetica", 8)
                self.setFillColor(colors.black)
                self.drawCentredString(w / 2.0, 12 * mm, FOOTER_ONE_LINE)
                self.drawCentredString(w / 2.0, 7 * mm, _("Page : %s / %s") % (self._pageNumber, page_count))

        # (Tu gardes ton footer en flow ci-dessous si tu veux un texte dans le flux
        # en plus du footer fixe. Si tu ne veux QUE le footer fixe, supprime les 3 lignes suivantes.)
        story.append(Spacer(1, 4 * mm))
        footer_text = FOOTER_ONE_LINE
        story.append(Paragraph(footer_text, FooterStyle))

        # Pagination "on_page" (callable requis par ReportLab)
        def on_page(canvas, _doc):
            w, h = A4
            canvas.setFont("Helvetica", 8)
            canvas.drawCentredString(w / 2, 10 * mm, f"Page : {canvas.getPageNumber()}")

        # Génération du PDF
        # 👉 Si tu veux utiliser le footer fixé via NumberedCanvas,
        # remplace la ligne suivante par: doc.build(story, canvasmaker=NumberedCanvas)
        doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

        buf.seek(0)
        return buf.getvalue()

    
    

    # ==============================
    # Route HTTP
    # ==============================
    @http.route('/api/creditcommandes/proforma/<int:order_id>/info',
                type='http', auth='none', methods=['GET'], cors="*", csrf=False)
    def api_get_proforma_info(self, order_id, **kw):
        """
        GET /api/creditcommandes/proforma/<order_id>/info?format=json|base64|pdf&download=1
        - format=json (défaut): renvoie meta JSON; si format=base64, inclut le PDF en base64.
        - format=pdf: renvoie directement le PDF (Content-Type: application/pdf)
        - download=1 sur format=pdf force Content-Disposition: attachment
        """
        import json, base64
        try:
            fmt = str(kw.get('format', '')).lower() or 'json'
            download = str(kw.get('download', '')).strip() in ('1', 'true', 'yes')
            # Compat param frontend existant
            # create_if_missing = kw.get('create_if_missing')  # non utilisé ici

            Order = request.env['sale.order'].sudo()
            order = Order.search([
                ('id', '=', order_id),
                ('type_sale', '=', 'creditorder')
            ], limit=1)
            if not order:
                return request.make_response(
                    json.dumps({"message": "Commande introuvable"}), status=404,
                    headers={'Content-Type': 'application/json'}
                )

            pdf_bytes = self._build_invoice_pdf(order)
            filename = f"Devis-{order.name or order.id}.pdf"

            if fmt == 'pdf':
                headers = {'Content-Type': 'application/pdf'}
                dispo = 'attachment' if download else 'inline'
                headers['Content-Disposition'] = f'{dispo}; filename="{filename}"'
                return request.make_response(pdf_bytes, headers=headers)

            # format json ou base64
            payload = {
                "order": {
                    "id": order.id,
                    "name": order.name,
                    "state": order.state,
                },
                "proforma": {
                    "id": order.id,
                    "name": order.name,
                    "amount_untaxed": float(order.amount_untaxed or 0.0),
                    "amount_tax": float(order.amount_tax or 0.0),
                    "amount_total": float(order.amount_total or 0.0),
                    "currency": (order.currency_id and order.currency_id.name) or "CFA",
                    "pdf_filename": filename,
                }
            }

            if fmt == 'base64':
                payload["proforma"]["pdf_base64"] = base64.b64encode(pdf_bytes).decode("utf-8")

            return request.make_response(
                json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

        except Exception as e:
            _logger.exception("Erreur pro-forma info (order_id=%s)", order_id)
            return request.make_response(
                json.dumps({"message": "Erreur interne du serveur"}), status=500,
                headers={'Content-Type': 'application/json'}
            )
