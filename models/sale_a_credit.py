# # -*- coding: utf-8 -*-
# from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
# import logging
# from datetime import datetime, date, timedelta

# _logger = logging.getLogger(__name__)

# SITE_URL = "https://ccbmshop.sn"
# LOGO_URL = "https://ccbmshop.sn/logo.png"  # adapte si besoin

# class SaleCreditOrderMail(models.Model):
#     _inherit = 'sale.order'

#     # ------------------------------------------------
#     # HELPERS PARTNER : normalisation champs custom
#     # ------------------------------------------------
#     def _partner_display_name(self, p):
#         """Nom lisible: 'Prénom Nom' > name."""
#         if not p:
#             return ""
#         prenom = (p.prenom or "").strip()
#         nom = (p.nom or "").strip()
#         if prenom or nom:
#             return (prenom + " " + nom).strip()
#         return p.name or ""

#     def _partner_email(self, p):
#         """Email du contact (priorité au champ custom/standard)."""
#         return (p.email or "").strip()

#     def _partner_phone(self, p):
#         """Téléphone priorise le champ custom 'telephone' puis standard."""
#         for attr in ("telephone", "phone", "mobile"):
#             val = getattr(p, attr, False)
#             if val:
#                 return val
#         return ""

#     def _partner_address_text(self, p):
#         """Adresse lisible. Priorité au champ custom 'adresse'."""
#         if not p:
#             return ""
#         if getattr(p, "adresse", False):
#             return p.adresse
#         parts = [
#             (p.street or ""),
#             (p.street2 or ""),
#             (p.city or ""),
#             (p.state_id.name if p.state_id else ""),
#             (p.zip or ""),
#             (p.country_id.name if p.country_id else ""),
#         ]
#         return " ".join(x for x in parts if x).strip()

#     def _partner_company(self, p):
#         """Société de rattachement: employer_partner_id > parent_id."""
#         if not p:
#             return False
#         return p.employer_partner_id or p.parent_id

#     def _find_company_rh_user(self, company_partner):
#         """Trouve le partenaire RH (role=main_user) de la société."""
#         if not company_partner:
#             return False
#         return self.env['res.partner'].sudo().search([
#             ('role', '=', 'main_user'),
#             ('parent_id', '=', company_partner.id),
#         ], limit=1)

#     # ------------------------------------------------
#     # HELPERS: snapshots & diffs pour mail "mise à jour"
#     # ------------------------------------------------
#     def _snapshot_for_update(self):
#         def paylines(sale):
#             rows = []
#             for l in sale.credit_payment_ids.sorted(lambda x: x.sequence):
#                 rows.append({
#                     'seq': l.sequence,
#                     'due': l.due_date.isoformat() if isinstance(l.due_date, (date, datetime)) else (l.due_date or None),
#                     'amount': float(l.amount or 0.0),
#                     'rate': l.rate,
#                     'state': bool(l.state),
#                 })
#             return rows

#         def orderlines(sale):
#             rows = []
#             for l in sale.order_line:
#                 rows.append({
#                     'id': l.id,
#                     'product': l.product_id.display_name,
#                     'qty': float(l.product_uom_qty or 0.0),
#                     'price_unit': float(l.price_unit or 0.0),
#                     'subtotal': float(l.price_subtotal or 0.0),
#                     'total': float(l.price_total or 0.0),
#                 })
#             rows.sort(key=lambda r: (r['id'] or 0))
#             return rows

#         return {
#             'amount_total': float(self.amount_total or 0.0),
#             'amount_residual': float(getattr(self, 'amount_residual', 0.0) or 0.0),
#             'advance_payment_status': self.advance_payment_status or '',
#             'paylines': paylines(self),
#             'orderlines': orderlines(self),
#         }

#     def _detect_order_updates(self, before, after):
#         reasons = []
#         if round(before.get('amount_total', 0.0), 2) != round(after.get('amount_total', 0.0), 2):
#             reasons.append(f"Montant total: {before['amount_total']:,.0f} → {after['amount_total']:,.0f} {self.currency_id.name}")
#         if round(before.get('amount_residual', 0.0), 2) != round(after.get('amount_residual', 0.0), 2):
#             reasons.append(f"Reste à payer: {before['amount_residual']:,.0f} → {after['amount_residual']:,.0f} {self.currency_id.name}")
#         if (before.get('advance_payment_status') or '') != (after.get('advance_payment_status') or ''):
#             reasons.append(f"Statut de paiement: {before.get('advance_payment_status') or '—'} → {after.get('advance_payment_status') or '—'}")
#         if before.get('orderlines') != after.get('orderlines'):
#             reasons.append("Lignes de commande mises à jour (prix/quantités).")
#         if before.get('paylines') != after.get('paylines'):
#             reasons.append("Échéancier de paiement mis à jour.")
#         return (len(reasons) > 0, reasons)

#     # ------------------------------------------------
#     # POINT D’ENTRÉE : on notifie APRÈS l’écriture
#     # ------------------------------------------------
#     def write(self, vals):
#         snapshots = {rec.id: rec._snapshot_for_update() for rec in self}
#         prev_states = {r.id: (r.validation_rh_state, r.validation_admin_state) for r in self}

#         res = super().write(vals)

#         for order in self:
#             if order.type_sale == 'creditorder':
#                 # 1) Logique RH/Admin
#                 old_rh, old_admin = prev_states.get(order.id, (None, None))
#                 new_rh, new_admin = order.validation_rh_state, order.validation_admin_state
#                 try:
#                     if old_rh != new_rh:
#                         if new_rh == 'validated':
#                             order.send_credit_order_rh_validation()
#                             order.send_credit_order_to_admin_for_validation()
#                         elif new_rh == 'rejected':
#                             order.send_credit_order_rh_rejected()
#                     if old_admin != new_admin:
#                         if new_admin == 'validated':
#                             order.send_credit_order_admin_validation()
#                         elif new_admin == 'rejected':
#                             order.send_credit_order_admin_rejected()
#                 except Exception as e:
#                     _logger.error("Erreur notif write(%s): %s", order.name, e, exc_info=True)

#                 # 2) Mail “mise à jour client”
#                 try:
#                     before = snapshots.get(order.id) or {}
#                     after = order._snapshot_for_update()
#                     changed, reasons = order._detect_order_updates(before, after)
#                     if changed:
#                         order._send_update_mail_to_customer(reasons)
#                 except Exception as e:
#                     _logger.error("Erreur mail update client %s: %s", order.name, e, exc_info=True)

#             elif order.type_sale == 'order' and order.state == 'sale':
#                 order.send_order_confirmation_mail()

#         return res

#     # ------------------------------------------------
#     # Aides échéancier
#     # ------------------------------------------------
#     def _coerce_to_date(self, value):
#         if not value:
#             return None
#         if isinstance(value, date) and not isinstance(value, datetime):
#             return value
#         if isinstance(value, datetime):
#             return value.date()
#         try:
#             return datetime.fromisoformat(str(value)).date()
#         except Exception:
#             return None

#     def _get_credit_payments(self):
#         payments = []
#         for line in self.credit_payment_ids.sorted(lambda l: l.sequence):
#             label = "Premier Paiement (Acompte)" if line.sequence == 1 else f"ÉCHÉANCE {line.sequence}"
#             payments.append({
#                 'label': label,
#                 'amount': float(line.amount or 0.0),
#                 'rate': line.rate,
#                 'due_date': self._coerce_to_date(line.due_date),
#                 'state': 'payé' if bool(line.state) else 'non payé',
#             })
#         return payments

#     # ------------------------------------------------
#     # RENDUS HTML (tables)
#     # ------------------------------------------------
#     def _payment_schedule_table(self, payments):
#         if not payments:
#             return None
#         rows = []
#         for p in payments:
#             date_str = p['due_date'].strftime('%d/%m/%Y') if p['due_date'] else '—'
#             status_text = p['state']
#             is_acompte = 'Acompte' in p['label']
#             rows.append(f"""
#                 <tr style="background-color:{'#e8f4fd' if is_acompte else 'transparent'}">
#                     <td style="padding:8px;border:1px solid #ddd;{'font-weight:bold;' if is_acompte else ''}">{p['label']}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{date_str}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{p['amount']:,.0f} {self.currency_id.name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{p['rate']}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{status_text}</td>
#                 </tr>
#             """)
#         return f"""
#         <h3 style="color:#333;margin-top:20px;">Échéancier de Paiement</h3>
#         <table border="1" cellpadding="5" cellspacing="0" width="100%" style="border-collapse:collapse;margin-top:10px;">
#             <thead>
#                 <tr style="background-color:#f8f9fa;">
#                     <th style="padding:10px;border:1px solid #ddd;text-align:left;">Échéance</th>
#                     <th style="padding:10px;border:1px solid #ddd;text-align:center;">Date d'échéance</th>
#                     <th style="padding:10px;border:1px solid #ddd;text-align:center;">Montant dû</th>
#                     <th style="padding:10px;border:1px solid #ddd;text-align:center;">Taux (%)</th>
#                     <th style="padding:10px;border:1px solid #ddd;text-align:center;">Statut</th>
#                 </tr>
#             </thead>
#             <tbody>{''.join(rows)}</tbody>
#         </table>
#         """

#     def _payment_info_table(self, payments):
#         if not payments:
#             return "<p>Aucune information de paiement disponible.</p>"
#         rows = []
#         for p in payments:
#             date_str = p['due_date'].strftime('%d/%m/%Y') if p['due_date'] else '—'
#             state_val = str(p['state']).lower()
#             paid_flag = state_val in ('paid', 'payé', 'true', '1')
#             status_text = 'Payé' if paid_flag else 'Non Payé'
#             is_acompte = 'Acompte' in p['label']
#             rows.append(f"""
#                 <tr style="background-color:{'#e8f4fd' if is_acompte else 'transparent'}">
#                     <td style="padding:8px;border:1px solid #ddd;{'font-weight:bold;' if is_acompte else ''}">{p['label']}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{p['amount']:,.0f} {self.currency_id.name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{p['rate']}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{date_str}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{status_text}</td>
#                 </tr>
#             """)
#         return f"""
#         <div style="margin-top:20px;">
#             <h3 style="color:#333;border-bottom:2px solid #875A7B;padding-bottom:5px;">Échéancier de Paiement</h3>
#             <table style="width:100%;border-collapse:collapse;margin-top:15px;">
#                 <thead>
#                     <tr style="background-color:#f8f9fa;">
#                         <th style="padding:10px;border:1px solid #ddd;text-align:left;">Échéance</th>
#                         <th style="padding:10px;border:1px solid #ddd;text-align:center;">Montant</th>
#                         <th style="padding:10px;border:1px solid #ddd;text-align:center;">Pourcentage</th>
#                         <th style="padding:10px;border:1px solid #ddd;text-align:center;">Date</th>
#                         <th style="padding:10px;border:1px solid #ddd;text-align:center;">Statut</th>
#                     </tr>
#                 </thead>
#                 <tbody>{''.join(rows)}</tbody>
#             </table>
#             <div style="margin-top:15px;background-color:#f8f9fa;padding:10px;border-radius:5px;">
#                 <p style="margin:5px 0;"><strong>Total commande:</strong> {self.amount_total:,.0f} {self.currency_id.name}</p>
#                 <p style="margin:5px 0;"><strong>Nombre d'échéances:</strong> {len(payments)}</p>
#             </div>
#         </div>
#         """

#     def _render_lines_table(self):
#         lines = []
#         for l in self.order_line:
#             lines.append(f"""
#                 <tr>
#                     <td style="padding:8px;border:1px solid #ddd;">{l.product_id.display_name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{int(l.product_uom_qty)}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_unit:,.0f} {self.currency_id.name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_total:,.0f} {self.currency_id.name}</td>
#                 </tr>
#             """)
#         return f"""
#             <h3 style="color:#333;margin:15px 0 10px 0;">Produits commandés</h3>
#             <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;border:1px solid #DDD;">
#                 <thead>
#                     <tr style="background:#F8F9FA;">
#                         <th align="left"  style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">Produit</th>
#                         <th align="center"style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">Qté</th>
#                         <th align="right" style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">PU</th>
#                         <th align="right" style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">Total</th>
#                     </tr>
#                 </thead>
#                 <tbody>
#                     {''.join(lines)}
#                     <tr style="background:#F8F9FA;font-weight:bold;">
#                         <td colspan="3" align="right" style="padding:10px;border-top:1px solid #DDD;">Total panier</td>
#                         <td align="right" style="padding:10px;border-top:1px solid #DDD;">{self.amount_total:,.0f} {self.currency_id.name}</td>
#                     </tr>
#                 </tbody>
#             </table>
#         """

#     def _render_payments_table_compact(self):
#         rows = []
#         total = float(self.amount_total or 0.0)
#         residual = float(getattr(self, 'amount_residual', 0.0) or 0.0)
#         paid = max(0.0, total - residual)
#         percent = (paid / total * 100.0) if total else 0.0

#         for l in self.credit_payment_ids.sorted(lambda x: x.sequence):
#             label = "Acompte" if l.sequence == 1 else f"Échéance {l.sequence}"
#             due = (l.due_date.strftime('%d/%m/%Y') if isinstance(l.due_date, (date, datetime)) and l.due_date else '—')
#             rows.append(f"""
#                 <tr>
#                     <td style="padding:8px;border:1px solid #ddd;">{label}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{due}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{(l.amount or 0.0):,.0f} {self.currency_id.name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{l.rate}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{"Payé" if l.state else "Non payé"}</td>
#                 </tr>
#             """)
#         return f"""
#             <h3 style="color:#333;margin:20px 0 10px 0;">Récapitulatif des paiements</h3>
#             <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;border:1px solid #DDD;">
#                 <thead>
#                     <tr style="background:#F8F9FA;">
#                         <th style="padding:10px;border-bottom:1px solid #DDD;text-align:left;">Échéance</th>
#                         <th style="padding:10px;border-bottom:1px solid #DDD;text-align:center;">Date</th>
#                         <th style="padding:10px;border-bottom:1px solid #DDD;text-align:right;">Montant</th>
#                         <th style="padding:10px;border-bottom:1px solid #DDD;text-align:center;">%</th>
#                         <th style="padding:10px;border-bottom:1px solid #DDD;text-align:center;">Statut</th>
#                     </tr>
#                 </thead>
#                 <tbody>{''.join(rows)}</tbody>
#             </table>

#             <div style="margin-top:12px;background:#F8F9FA;padding:10px;border-radius:6px;">
#                 <p style="margin:4px 0;"><strong>Montant payé :</strong> {paid:,.0f} {self.currency_id.name}</p>
#                 <p style="margin:4px 0;"><strong>Reste à payer :</strong> {residual:,.0f} {self.currency_id.name}</p>
#                 <p style="margin:4px 0;"><strong>Avancement :</strong> {percent:.1f}%</p>
#             </div>
#         """

#     def _render_update_mail(self, reasons):
#         partner = self.partner_id
#         partner_name = self._partner_display_name(partner)
#         return f"""
#         <table role="presentation" border="0" cellpadding="0" cellspacing="0"
#                style="width:100%;background:#FFFFFF;font-family:Verdana, Arial, sans-serif;color:#454748;border-collapse:separate;padding-top:16px;">
#           <tr><td align="center" style="padding:0 8px;">
#             <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
#                    style="background:#FFFFFF;color:#454748;border-collapse:separate;padding:16px;">
#               <tr>
#                 <td valign="middle" style="padding:0;">
#                   <span style="font-size:10px;display:block;line-height:1.4;">Mise à jour de votre commande à crédit</span>
#                   <span style="font-size:20px;font-weight:bold;display:block;line-height:1.4;">{self.name}</span>
#                 </td>
#                 <td valign="middle" align="right" style="padding:0;">
#                   <img src="{LOGO_URL}" width="120" height="auto" alt="Logo CCBM SHOP"
#                        style="display:block;border:0;outline:none;text-decoration:none;" />
#                 </td>
#               </tr>
#               <tr><td colspan="2"><hr style="border:none;height:1px;background:#CCC;margin:16px 0;" /></td></tr>

#               <tr><td colspan="2" style="padding:0;">
#                 <p style="margin:0 0 12px 0;line-height:1.6;">Bonjour {partner_name},</p>
#                 <p style="margin:0 0 12px 0;line-height:1.6;">Nous vous informons qu’un changement a été effectué sur votre commande :</p>
#                 <ul style="margin:0 0 12px 16px;padding:0;line-height:1.6;">
#                   {''.join([f"<li>{r}</li>" for r in reasons])}
#                 </ul>
#               </td></tr>

#               <tr><td colspan="2" style="padding:0;">{self._render_lines_table()}</td></tr>
#               <tr><td colspan="2" style="padding-top:12px;">{self._render_payments_table_compact()}</td></tr>
#             </table>

#             <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
#                    style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
#               <tr>
#                 <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
#                   <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
#                   <div>🛍️ <a href="{SITE_URL}" target="_blank" rel="noopener"
#                              style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
#                 </td>
#               </tr>
#             </table>
#           </td></tr>
#         </table>
#         """

#     def _send_update_mail_to_customer(self, reasons):
#         mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#         if not mail_server:
#             _logger.warning("Pas de serveur mail configuré — email non envoyé.")
#             return
#         partner = self.partner_id
#         email = self._partner_email(partner)
#         if not email:
#             _logger.warning("Aucun e-mail client — email non envoyé.")
#             return

#         body_html = self._render_update_mail(reasons)
#         email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
#         email_to = ', '.join(filter(None, [email, 'shop@ccbm.sn']))
#         mail_values = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'subject': _("Mise à jour de votre commande à crédit %s") % (self.name,),
#             'body_html': body_html,
#             'state': 'outgoing',
#             'auto_delete': False,
#         }
#         mail = self.env['mail.mail'].sudo().create(mail_values)
#         mail.send()
#         _logger.info("Mail update envoyé à %s pour %s", email_to, self.name)

#     # ------------------------------------------------
#     # ENVOIS MAILS existants (conservés mais normalisés)
#     # ------------------------------------------------
#     def get_sale_order_credit_payment(self):
#         try:
#             payments = self.env['sale.order.credit.payment'].search([('order_id', '=', self.id)])
#             data = []
#             for payment in payments:
#                 data.append({
#                     'sequence': payment.sequence,
#                     'due_date': payment.due_date.isoformat() if hasattr(payment.due_date, 'isoformat') else str(payment.due_date),
#                     'amount': payment.amount,
#                     'rate': payment.rate,
#                     'state': payment.state,
#                 })
#             return data
#         except Exception as e:
#             _logger.error(f'Erreur lors de la récupération des paiements : {e}', exc_info=True)
#             return []

#     def send_credit_order_validation_mail(self):
#         try:
#             mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#             if not mail_server:
#                 return {'status': 'error', 'message': 'Mail server not configured'}

#             partner = self.partner_id
#             email = self._partner_email(partner)
#             if not email:
#                 return {'status': 'error', 'message': 'Partner email not found'}

#             payments = self._get_credit_payments()
#             payment_schedule_html = self._payment_schedule_table(payments)

#             total_amount = 0.0
#             lines_html = []
#             for l in self.order_line:
#                 total_amount += l.price_total
#                 lines_html.append(f"""
#                     <tr>
#                         <td style="padding:8px;border:1px solid #ddd;">{l.product_id.display_name}</td>
#                         <td style="padding:8px;border:1px solid #ddd;text-align:center;">{int(l.product_uom_qty)}</td>
#                         <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_unit:,.0f} {self.currency_id.name}</td>
#                         <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_total:,.0f} {self.currency_id.name}</td>
#                     </tr>
#                 """)

#             partner_name = self._partner_display_name(partner)
#             body_html = f"""
#                 <table border="0" cellpadding="0" cellspacing="0" style="padding-top:16px;background:#FFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
#                     <tr><td align="center">
#                         <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding:16px;background:#FFF;color:#454748;border-collapse:separate;">
#                             <tr>
#                                 <td valign="middle">
#                                     <span style="font-size:10px;">Validation de votre commande à crédit</span><br/>
#                                     <span style="font-size:20px;font-weight:bold;">{self.name}</span>
#                                 </td>
#                                 <td valign="middle" align="right">
#                                     <img style="width:120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
#                                 </td>
#                             </tr>
#                             <tr><td colspan="2"><hr style="border:none;height:1px;background:#ccc;margin:16px 0"/></td></tr>
#                             <tr><td colspan="2">
#                                 <p>Félicitations {partner_name}, votre commande à crédit a été créée.</p>
#                                 <h3 style="color:#333;margin:15px 0;">Produits commandés</h3>
#                                 <table border="1" cellpadding="5" cellspacing="0" width="100%" style="border-collapse:collapse;">
#                                     <thead>
#                                         <tr style="background:#f8f9fa;">
#                                             <th style="padding:10px;border:1px solid #ddd;">Produit</th>
#                                             <th style="padding:10px;border:1px solid #ddd;">Qté</th>
#                                             <th style="padding:10px;border:1px solid #ddd;">PU</th>
#                                             <th style="padding:10px;border:1px solid #ddd;">Total</th>
#                                         </tr>
#                                     </thead>
#                                     <tbody>
#                                         {''.join(lines_html)}
#                                         <tr style="background:#f8f9fa;font-weight:bold;">
#                                             <td colspan="3" style="padding:10px;border:1px solid #ddd;text-align:right;">Total du panier</td>
#                                             <td style="padding:10px;border:1px solid #ddd;text-align:right;">{total_amount:,.0f} {self.currency_id.name}</td>
#                                         </tr>
#                                     </tbody>
#                                 </table>
#                                 {payment_schedule_html or ''}
#                             </td></tr>
#                         </table>
#                     </td></tr>
#                      <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                         <td colspan="2" style="padding: 12px; text-align: center;">
#                             <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                             <p><a href="{SITE_URL}" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                         </td>
#                     </tr>
#                 </table>
#             """

#             return self._send_mail_common(mail_server, partner, _('Validation de votre commande à crédit'), body_html, sms_type='validation')

#         except Exception as e:
#             _logger.error("Erreur mail validation %s: %s", self.name, e, exc_info=True)
#             return {'status': 'error', 'message': str(e)}

#     def send_payment_status_mail_creditorder(self):
#         try:
#             mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#             if not mail_server:
#                 return {'status': 'error', 'message': 'Mail server not configured'}
#             partner = self.partner_id
#             email = self._partner_email(partner)
#             if not email:
#                 return {'status': 'error', 'message': 'Partner email not found'}

#             payments = self._get_credit_payments()
#             payment_info = self._payment_info_table(payments)

#             total = float(self.amount_total or 0.0)
#             residual = float(getattr(self, 'amount_residual', 0.0) or 0.0)
#             paid = max(0.0, total - residual)
#             percent = (paid / total * 100.0) if total else 0.0

#             partner_name = self._partner_display_name(partner)
#             summary = f"""
#                 <div style="margin-top:20px;background:#f8f9fa;padding:12px;border-radius:6px;">
#                     <p><strong>Prix total:</strong> {total:,.0f} {self.currency_id.name}</p>
#                     <p><strong>Montant payé:</strong> {paid:,.0f} {self.currency_id.name}</p>
#                     <p><strong>Reste à payer:</strong> {residual:,.0f} {self.currency_id.name}</p>
#                     <p><strong>Pourcentage payé:</strong> {percent:.1f}%</p>
#                 </div>
#                 <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                 <td colspan="2" style="padding: 12px; text-align: center;">
#                     <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                     <p><a href="{SITE_URL}" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                 </td>
#             </tr>
#             """

#             body_html = f"""
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                         <tr>
#                             <td valign="middle">
#                                 <span style="font-size: 10px;">Commande à crédit</span><br/>
#                                 <span style="font-size: 20px; font-weight: bold;">{self.name}</span>
#                             </td>
#                             <td valign="middle" align="right">
#                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
#                             </td>
#                         </tr>
#                         <tr>
#                             <td colspan="2" style="text-align:center;">
#                                 <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>

#             <p>Bonjour {partner_name}, voici une mise à jour de l'état de votre commande {self.name}.</p>
#             {payment_info}
#             {summary}
#             """
#             return self._send_mail_common(mail_server, partner, _("Mise à jour de l'état de votre commande à crédit"), body_html)

#         except Exception as e:
#             _logger.error("Erreur mail statut %s: %s", self.name, e, exc_info=True)
#             return {'status': 'error', 'message': str(e)}

#     # ---- RH / ADMIN (contenu conservé) ----
#     def send_credit_order_rh_rejected(self):
#         return self._simple_templated_mail('rh_rejection', _('Rejet de votre commande à crédit par le service RH'))

#     def send_credit_order_rh_validation(self):
#         return self._simple_templated_mail('rh_validation', _('Validation RH de votre commande à crédit'))

#     def send_credit_order_admin_validation(self):
#         return self._simple_templated_mail('admin_validation', _("Validation administrative de votre commande à crédit"))

#     def send_credit_order_admin_rejected(self):
#         return self._simple_templated_mail('admin_rejection', _("Rejet de votre commande à crédit par l'administration"))

#     def _simple_templated_mail(self, template_key, subject):
#         mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#         if not mail_server:
#             return {'status': 'error', 'message': 'Mail server not configured'}
#         partner = self.partner_id
#         email = self._partner_email(partner)
#         if not email:
#             return {'status': 'error', 'message': 'Partner email not found'}
#         body_html = self._generate_email_body_html(partner, template_key)
#         return self._send_mail_common(mail_server, partner, subject, body_html,
#                                       sms_type=template_key if template_key in (
#                                           'validation', 'rejection',
#                                           'rh_rejection', 'admin_rejection',
#                                           'admin_validation', 'rh_validation'
#                                       ) else None)

#     # ------------------------------------------------
#     # UTILITAIRES COMMUNS (mail + sms)
#     # ------------------------------------------------
#     def _send_mail_common(self, mail_server, partner, subject, body_html, sms_type=None):
#         try:
#             email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
#             email_to = ', '.join(filter(None, [self._partner_email(partner), 'shop@ccbm.sn']))
#             mail_values = {
#                 'email_from': email_from,
#                 'email_to': email_to,
#                 'subject': subject,
#                 'body_html': body_html,
#                 'state': 'outgoing',
#                 'auto_delete': False,
#             }
#             mail = self.env['mail.mail'].sudo().create(mail_values)
#             mail.send()
#             _logger.info("Mail '%s' envoyé à %s pour %s", subject, email_to, self.name)

#             if sms_type:
#                 phone = self._partner_phone(partner)
#                 if phone:
#                     Sms = self.env.get('send.sms')
#                     if Sms:
#                         sms_rec = Sms.create({'recipient': phone, 'message': self._sms_message(sms_type)})
#                         sms_rec.send_sms()
#                     else:
#                         _logger.warning("Module send.sms indisponible — SMS non envoyé")
#             return {'status': 'success'}
#         except Exception as e:
#             _logger.error("Erreur envoi mail %s: %s", self.name, e, exc_info=True)
#             return {'status': 'error', 'message': str(e)}

#     def _sms_message(self, kind):
#         partner_name = self._partner_display_name(self.partner_id)
#         m = {
#             'validation': f"Bonjour {partner_name}, votre commande à crédit {self.name} a été créée.",
#             'rejection': f"Bonjour {partner_name}, votre commande à crédit {self.name} a été rejetée.",
#             'rh_rejection': f"Bonjour {partner_name}, votre commande {self.name} a été rejetée par le service RH.",
#             'admin_rejection': f"Bonjour {partner_name}, votre commande {self.name} a été rejetée par l'administration.",
#             'admin_validation': f"Bonjour {partner_name}, votre commande {self.name} a été validée par l'administration.",
#             'rh_validation': f"Bonjour {partner_name}, votre commande {self.name} a été validée par le service RH.",
#             'request': f"Bonjour {partner_name}, votre demande de commande à crédit {self.name} est en cours.",
#             'creation': f"Bonjour {partner_name}, votre commande {self.name} a été créée.",
#             'hr_notification': f"Bonjour, la commande {self.name} nécessite une validation RH.",
#         }
#         return m.get(kind, f"Notification commande {self.name}")

#     # ------------------------------------------------
#     # Notifications vers ADMIN / RH (RH = role main_user)
#     # ------------------------------------------------
#     def send_credit_order_to_admin_for_validation(self):
#         try:
#             mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#             if not mail_server:
#                 return {'status': 'error', 'message': 'Mail server not configured'}

#             admin_group = self.env.ref('base.group_system')
#             admin_user = self.env['res.users'].sudo().search([('groups_id', 'in', admin_group.id)], limit=1)
#             if not admin_user or not admin_user.partner_id.email:
#                 return {'status': 'error', 'message': 'No admin user with email'}

#             subject = _('Confirmation requise pour la commande à crédit - %s') % self.name
#             body_html = self._generate_admin_notification_email(admin_user)
#             return self._send_mail_common(mail_server, admin_user.partner_id, subject, body_html)
#         except Exception as e:
#             _logger.error("Erreur notif admin %s: %s", self.name, e, exc_info=True)
#             return {'status': 'error', 'message': str(e)}

#     def send_credit_order_creation_notification_to_hr(self):
#         try:
#             mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#             if not mail_server:
#                 return {'status': 'error', 'message': 'Mail server not configured'}

#             company = self._partner_company(self.partner_id)
#             if not company:
#                 return {'status': 'error', 'message': 'No company (employer/parent) found'}

#             rh_user = self._find_company_rh_user(company)
#             if not rh_user or not self._partner_email(rh_user):
#                 return {'status': 'error', 'message': 'HR user not found'}

#             subject = _('Nouvelle commande à valider')
#             body_html = self._generate_hr_notification_email()
#             return self._send_mail_common(mail_server, rh_user, subject, body_html, sms_type='hr_notification')
#         except Exception as e:
#             _logger.error("Erreur notif RH %s: %s", self.name, e, exc_info=True)
#             return {'status': 'error', 'message': str(e)}

#     # ---- Gabarits emails (conservés avec URLs/LOGO normalisés)
#     def _generate_admin_notification_email(self, admin_user):
#         return f'''
#         <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
#             <tr>
#                 <td align="center">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
#                         <tbody>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td valign="middle">
#                                                 <span style="font-size: 10px;">Commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
#                                             </td>
#                                         </tr>
#                                         <tr>
#                                             <td colspan="2" style="text-align:center;">
#                                                 <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td>
#                                                 <p>Bonjour {self.company_id.name},</p>
#                                                 <p>Le service RH a confirmé la commande à crédit suivante :</p>
#                                                 <ul>
#                                                     <li>Numéro de commande : {self.name}</li>
#                                                     <li>Client : {self._partner_display_name(self.partner_id)}</li>
#                                                     <li>Montant total : {self.amount_total:,.0f} {self.currency_id.name}</li>
#                                                     <li>Pourcentage d'acompte : {getattr(self, 'credit_month_rate', 0)}%</li>
#                                                     <li>Nombre d'échéances : {getattr(self, 'creditorder_month_count', 0)} Paiement(s)</li>
#                                                 </ul>
#                                                 <p>Votre confirmation est maintenant requise pour finaliser cette commande.</p>
#                                                 <p>Veuillez vous connecter au système pour examiner et valider cette commande.</p>
#                                                 <p>Cordialement,<br/>Le système automatique</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                 <td colspan="2" style="padding: 12px; text-align: center;">
#                     <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                     <p><a href="{SITE_URL}" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                 </td>
#             </tr>
#         </table>
#         '''

#     def _generate_hr_notification_email(self):
#         return f'''
#         <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
#             <tr>
#                 <td align="center">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
#                         <tbody>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td valign="middle">
#                                                 <span style="font-size: 10px;">Commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
#                                             </td>
#                                         </tr>
#                                         <tr>
#                                             <td colspan="2" style="text-align:center;">
#                                                 <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td>
#                                                 <p>Bonjour,</p>
#                                                 <p>Une nouvelle demande de commande à crédit a été créée et nécessite votre validation :</p>
#                                                 <ul>
#                                                     <li>Numéro de commande : {self.name}</li>
#                                                     <li>Client : {self._partner_display_name(self.partner_id)}</li>
#                                                     <li>Montant total : {self.amount_total:,.0f} {self.currency_id.name}</li>
#                                                     <li>Date de création : {self.create_date.strftime('%d/%m/%Y %H:%M') if self.create_date else 'Non définie'}</li>
#                                                 </ul>
#                                                 <p>Veuillez examiner cette demande et prendre les mesures appropriées dans votre interface d'administration.</p>
#                                                 <p>Cordialement,<br/>Le système automatique CCBM Shop</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                 <td colspan="2" style="padding: 12px; text-align: center;">
#                     <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                     <p><a href="{SITE_URL}" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                 </td>
#             </tr>
#         </table>
#         '''

#     def _generate_email_body_html(self, partner, email_type, additional_content=""):
#         partner_name = self._partner_display_name(partner)
#         email_content = {
#             'validation': {
#                 'title': 'Validation de votre commande à crédit',
#                 'content': f"""
#                     <p>Félicitations {partner_name},</p>
#                     <p>Votre commande à crédit numéro {self.name} a été créée avec succès.</p>
#                     <p>Détails des échéances :</p>
#                 """
#             },
#             'rejection': {
#                 'title': 'Rejet de votre commande à crédit',
#                 'content': f"""
#                     <p>Cher(e) {partner_name},</p>
#                     <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.</p>
#                     <p>Si vous avez des questions concernant cette décision, n'hésitez pas à nous contacter pour plus d'informations.</p>
#                 """
#             },
#             'rh_rejection': {
#                 'title': 'Rejet de votre commande à crédit par le service RH',
#                 'content': f"""
#                     <p>Cher(e) {partner_name},</p>
#                     <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par votre service des Ressources Humaines.</p>
#                     <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
#                 """
#             },
#             'admin_rejection': {
#                 'title': 'Rejet de votre commande à crédit par l\'administration',
#                 'content': f"""
#                     <p>Cher(e) {partner_name},</p>
#                     <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre administration.</p>
#                     <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
#                 """
#             },
#             'admin_validation': {
#                 'title': 'Validation administrative de votre commande à crédit',
#                 'content': f"""
#                     <p>Cher(e) {partner_name},</p>
#                     <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre administration.</p>
#                     <p>Nous vous invitons à vous connecter dès maintenant à la plateforme afin d'effectuer le paiement de {getattr(self, 'credit_month_rate', 0)}% du montant de la commande.</p>
#                     <p>Nous vous tiendrons informé des prochaines étapes.</p>
#                 """
#             },
#             'rh_validation': {
#                 'title': 'Validation RH de votre commande à crédit',
#                 'content': f"""
#                     <p>Cher(e) {partner_name},</p>
#                     <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par votre service des Ressources Humaines.</p>
#                     <p>Vous pouvez à présent attendre la validation finale de CCBM Shop avant de procéder au paiement.</p>
#                     <p>Nous vous tiendrons informé des prochaines étapes.</p>
#                 """
#             },
#             'request': {
#                 'title': 'Votre demande de commande à crédit',
#                 'content': f"""
#                     <p>Bonjour {partner_name},</p>
#                     <p>Nous avons bien reçu votre demande de commande à crédit numéro {self.name}.</p>
#                     <p>Elle est actuellement en cours de validation par nos services.</p>
#                     <p>Nous vous tiendrons informé de l'avancement de votre demande.</p>
#                 """
#             },
#             'payment_status': {
#                 'title': "Mise à jour de l'état de votre commande à crédit",
#                 'content': f"""
#                     <p>Bonjour {partner_name},</p>
#                     <p>Voici la mise à jour de l'état de votre commande à crédit numéro {self.name}.</p>
#                 """
#             }
#         }

#         content_info = email_content.get(email_type, {
#             'title': 'Notification de commande à crédit',
#             'content': f'<p>Bonjour {partner_name},</p><p>Notification concernant votre commande {self.name}.</p>'
#         })

#         return f"""
#         <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
#             <tr>
#                 <td align="center">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
#                         <tbody>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td valign="middle">
#                                                 <span style="font-size: 10px;">{content_info['title']}</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
#                                             </td>
#                                         </tr>
#                                         <tr>
#                                             <td colspan="2" style="text-align:center;">
#                                                 <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td>
#                                                 {content_info['content']}
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             {additional_content}
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                 <td colspan="2" style="padding: 12px; text-align: center;">
#                     <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                     <p><a href="{SITE_URL}" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                 </td>
#             </tr>
#         </table>
#         """

#     # ------------------------------------------------
#     # Confirmation commande (hors crédit) — normalisée
#     # ------------------------------------------------
#     def send_order_confirmation_mail(self):
#         self.ensure_one()
#         mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#         if not mail_server:
#             return True

#         partner = self.partner_id
#         email = self._partner_email(partner)
#         if not email:
#             return True

#         base_url = SITE_URL.rstrip('/')
#         # Fenêtre de livraison estimée
#         commitment_date = getattr(self, 'commitment_date', False) or (datetime.now() + timedelta(days=7))
#         if isinstance(commitment_date, datetime):
#             d0 = commitment_date
#         else:
#             try:
#                 d0 = datetime.combine(commitment_date, datetime.min.time())
#             except Exception:
#                 d0 = datetime.now() + timedelta(days=7)
#         d1 = d0 + timedelta(days=3)
#         delivery_window_str = f"Entre le {d0.strftime('%d/%m/%Y')} et {d1.strftime('%d/%m/%Y')}"

#         payment_label = getattr(self, 'payment_term_id', False) and self.payment_term_id.name or "Paiement à la livraison"

#         # S’il n’a pas (encore) de compte portail, proposer la création
#         partner_name = self._partner_display_name(partner)
#         has_user = bool(email)  # tu peux raffiner en vérifiant res.users
#         create_account_section = ""
#         if not has_user:
#             create_account_link = f"{base_url}/create-compte?mail={email}"
#             create_account_section = f'''
#                 <tr>
#                     <td align="center" style="min-width: 590px; padding-top: 20px;">
#                         <span style="font-size: 14px;">Créez un compte pour suivre votre commande :</span><br/>
#                         <a href="{create_account_link}" style="font-size: 16px; font-weight: bold; color:#875A7B;">Créer un compte</a>
#                     </td>
#                 </tr>
#             '''

#         lines_html = []
#         for l in self.order_line:
#             lines_html.append(f"""
#                 <tr>
#                     <td style="padding:8px;border:1px solid #ddd;">{l.product_id.display_name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:center;">{int(l.product_uom_qty)}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_unit:,.0f} {self.currency_id.name}</td>
#                     <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_total:,.0f} {self.currency_id.name}</td>
#                 </tr>
#             """)

#         # Coordonnées normalisées
#         phone_txt = self._partner_phone(partner)
#         address_txt = self._partner_address_text(partner)

#         subject = 'Confirmation de votre commande'
#         body_html = f'''
#         <table border="0" cellpadding="0" cellspacing="0" style="padding-top:16px;background:#FFFFFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
#         <tr><td align="center">
#             <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding:16px;background:#FFFFFF;color:#454748;border-collapse:separate;">
#             <tbody>
#                 <tr>
#                 <td align="center" style="min-width:590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
#                     <tr>
#                         <td valign="middle">
#                         <span style="font-size:10px;">Votre commande</span><br/>
#                         <span style="font-size:20px;font-weight:bold;">{self.name}</span>
#                         </td>
#                         <td valign="middle" align="right">
#                         <img src="{LOGO_URL}" alt="Logo CCBM SHOP" style="width:120px;height:auto;display:block;border:0;outline:none;text-decoration:none;"/>
#                         </td>
#                     </tr>
#                     <tr>
#                         <td colspan="2" style="text-align:center;">
#                         <hr width="100%" style="background:#ccc;border:none;display:block;height:1px;margin:16px 0;"/>
#                         </td>
#                     </tr>
#                     </table>
#                 </td>
#                 </tr>

#                 <tr>
#                 <td align="center" style="min-width:590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
#                     <tr>
#                         <td valign="middle" style="width:50%;">
#                         <span style="font-size:15px;font-weight:bold;">Détails du destinataire</span>
#                         </td>
#                         <td valign="middle" align="right" style="width:50%;">
#                         {partner_name}<br/>{phone_txt or ''}
#                         </td>
#                     </tr>
#                     <tr>
#                         <td valign="middle" style="width:50%;">
#                         <span style="font-size:15px;font-weight:bold;">Adresse</span>
#                         </td>
#                         <td valign="middle" align="right" style="width:50%;">{address_txt}</td>
#                     </tr>
#                     <tr>
#                         <td valign="middle" style="width:50%;">
#                         <span style="font-size:15px;font-weight:bold;">Date de livraison estimée</span>
#                         </td>
#                         <td valign="middle" align="right" style="width:50%;">{delivery_window_str}</td>
#                     </tr>
#                     <tr>
#                         <td valign="middle" style="width:50%;">
#                         <span style="font-size:15px;font-weight:bold;">Méthode de paiement</span>
#                         </td>
#                         <td valign="middle" align="right" style="width:50%;">{payment_label}</td>
#                     </tr>
#                     </table>
#                 </td>
#                 </tr>

#                 <tr>
#                 <td align="center" style="min-width:590px;">
#                     <table border="1" cellpadding="5" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:collapse;">
#                     <thead>
#                         <tr style="background:#f8f9fa;">
#                         <th align="left"  style="padding:10px;border:1px solid #ddd;">Produit</th>
#                         <th align="center"style="padding:10px;border:1px solid #ddd;">Quantité</th>
#                         <th align="right" style="padding:10px;border:1px solid #ddd;">Prix unitaire</th>
#                         <th align="right" style="padding:10px;border:1px solid #ddd;">Total</th>
#                         </tr>
#                     </thead>
#                     <tbody>
#                         {''.join(lines_html)}
#                         <tr style="background:#f8f9fa;font-weight:bold;">
#                         <td colspan="3" align="right" style="padding:10px;border:1px solid #ddd;">Total du panier</td>
#                         <td align="right" style="padding:10px;border:1px solid #ddd;">{self.amount_total:,.0f} {self.currency_id.name}</td>
#                         </tr>
#                     </tbody>
#                     </table>
#                 </td>
#                 </tr>

#                 {create_account_section}

#             </tbody>
#             </table>

#             <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
#                 style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
#             <tr>
#                 <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
#                 <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
#                 <div>🛍️ <a href="{SITE_URL}" target="_blank" rel="noopener"
#                             style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
#                 </td>
#             </tr>
#             </table>

#         </td></tr>
#         </table>
#         '''
#         return self._send_mail_common(
#             mail_server=mail_server,
#             partner=partner,
#             subject=subject,
#             body_html=body_html,
#             sms_type=None,
#         )


# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)

# Personnalise si besoin
SITE_URL = "https://ccbmshop.sn"
LOGO_URL = "https://ccbmshop.sn/logo.png"


class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    # ---------------------------------------------------------------------
    # =======================  HELPERS PARTNER  ============================
    # ---------------------------------------------------------------------
    def _partner_display_name(self, p):
        """Affiche d'abord 'Prénom Nom' (tes champs custom), sinon name."""
        if not p:
            return ""
        prenom = (getattr(p, 'prenom', '') or '').strip()
        nom = (getattr(p, 'nom', '') or '').strip()
        if prenom or nom:
            return (prenom + " " + nom).strip()
        return (p.name or '').strip()

    def _partner_email(self, p):
        """Email prioritaire: champ standard email, sinon vide."""
        return (getattr(p, 'email', '') or '').strip()

    def _partner_phone(self, p):
        """
        Téléphone priorise ton champ custom 'telephone', sinon phone/mobile.
        """
        for attr in ('telephone', 'phone', 'mobile'):
            val = getattr(p, attr, False)
            if val:
                return val
        return ""

    def _partner_address_text(self, p):
        """Adresse textuelle. Priorité au champ custom 'adresse'."""
        if not p:
            return ""
        if getattr(p, 'adresse', False):
            return p.adresse
        parts = [
            (p.street or ""),
            (p.street2 or ""),
            (p.city or ""),
            (p.state_id.name if p.state_id else ""),
            (p.zip or ""),
            (p.country_id.name if p.country_id else ""),
        ]
        return " ".join(x for x in parts if x).strip()

    def _partner_company(self, p):
        """Société: ton Many2one 'employer_partner_id' sinon parent_id."""
        if not p:
            return False
        return getattr(p, 'employer_partner_id', False) or p.parent_id

    def _find_company_rh_user(self, company_partner):
        """
        Partenaire RH (rôle main_user) au sein de la société (=parent).
        On cherche un contact enfant avec role='main_user'.
        """
        if not company_partner:
            return False
        return self.env['res.partner'].sudo().search([
            ('role', '=', 'main_user'),
            ('parent_id', '=', company_partner.id),
        ], limit=1)

    # ---------------------------------------------------------------------
    # ======================  SNAPSHOT / DIFFS  ============================
    # ---------------------------------------------------------------------
    def _snapshot_for_update(self):
        def paylines(sale):
            rows = []
            for l in sale.credit_payment_ids.sorted(lambda x: x.sequence):
                rows.append({
                    'seq': l.sequence,
                    'due': (l.due_date.isoformat()
                            if isinstance(l.due_date, (date, datetime)) else (l.due_date or None)),
                    'amount': float(l.amount or 0.0),
                    'rate': l.rate,
                    'state': bool(l.state),
                })
            return rows

        def orderlines(sale):
            rows = []
            for l in sale.order_line:
                rows.append({
                    'id': l.id,
                    'product': l.product_id.display_name,
                    'qty': float(l.product_uom_qty or 0.0),
                    'price_unit': float(l.price_unit or 0.0),
                    'subtotal': float(l.price_subtotal or 0.0),
                    'total': float(l.price_total or 0.0),
                })
            rows.sort(key=lambda r: (r['id'] or 0))
            return rows

        return {
            'amount_total': float(self.amount_total or 0.0),
            'amount_residual': float(getattr(self, 'amount_residual', 0.0) or 0.0),
            'advance_payment_status': self.advance_payment_status or '',
            'paylines': paylines(self),
            'orderlines': orderlines(self),
        }

    def _detect_order_updates(self, before, after):
        reasons = []
        if round(before.get('amount_total', 0.0), 2) != round(after.get('amount_total', 0.0), 2):
            reasons.append(
                _("Montant total: %(before)s → %(after)s %(currency)s", before=f"{before['amount_total']:,.0f}",
                  after=f"{after['amount_total']:,.0f}", currency=self.currency_id.name)
            )
        if round(before.get('amount_residual', 0.0), 2) != round(after.get('amount_residual', 0.0), 2):
            reasons.append(
                _("Reste à payer: %(before)s → %(after)s %(currency)s", before=f"{before['amount_residual']:,.0f}",
                  after=f"{after['amount_residual']:,.0f}", currency=self.currency_id.name)
            )
        if (before.get('advance_payment_status') or '') != (after.get('advance_payment_status') or ''):
            reasons.append(
                _("Statut de paiement: %(before)s → %(after)s",
                  before=(before.get('advance_payment_status') or '—'),
                  after=(after.get('advance_payment_status') or '—'))
            )
        if before.get('orderlines') != after.get('orderlines'):
            reasons.append(_("Lignes de commande mises à jour (prix/quantités)."))
        if before.get('paylines') != after.get('paylines'):
            reasons.append(_("Échéancier de paiement mis à jour."))
        return (len(reasons) > 0, reasons)

    # ---------------------------------------------------------------------
    # ========================  TRIGGER WRITE()  ===========================
    # ---------------------------------------------------------------------
    def write(self, vals):
        # Sauvegarde avant écriture
        snapshots = {rec.id: rec._snapshot_for_update() for rec in self}
        prev_states = {r.id: (r.validation_rh_state, r.validation_admin_state) for r in self}

        res = super().write(vals)

        # Après écriture: décisions/notifications
        for order in self:
            try:
                if order.type_sale == 'creditorder':
                    old_rh, old_admin = prev_states.get(order.id, (None, None))
                    new_rh, new_admin = order.validation_rh_state, order.validation_admin_state

                    # 1) Flux RH et Admin
                    if old_rh != new_rh:
                        if new_rh == 'validated':
                            order.send_credit_order_rh_validation()
                            order.send_credit_order_to_admin_for_validation()
                        elif new_rh == 'rejected':
                            order.send_credit_order_rh_rejected()

                    if old_admin != new_admin:
                        if new_admin == 'validated':
                            order.send_credit_order_admin_validation()
                        elif new_admin == 'rejected':
                            order.send_credit_order_admin_rejected()

                    # 2) Mail client “mise à jour”
                    before = snapshots.get(order.id) or {}
                    after = order._snapshot_for_update()
                    changed, reasons = order._detect_order_updates(before, after)
                    if changed:
                        order._send_update_mail_to_customer(reasons)

                elif order.type_sale == 'order' and order.state == 'sale':
                    order.send_order_confirmation_mail()

            except Exception as e:
                _logger.error("Erreur post-write sur %s: %s", order.name, e, exc_info=True)

        return res

    # ---------------------------------------------------------------------
    # ==================  UTILITAIRES AFFICHAGE TABLES  ====================
    # ---------------------------------------------------------------------
    def _coerce_to_date(self, value):
        if not value:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.fromisoformat(str(value)).date()
        except Exception:
            return None

    def _get_credit_payments(self):
        payments = []
        for line in self.credit_payment_ids.sorted(lambda l: l.sequence):
            label = _("Premier Paiement (Acompte)") if line.sequence == 1 else _("ÉCHÉANCE %(n)s", n=line.sequence)
            payments.append({
                'label': label,
                'amount': float(line.amount or 0.0),
                'rate': line.rate,
                'due_date': self._coerce_to_date(line.due_date),
                'state': _('payé') if bool(line.state) else _('non payé'),
            })
        return payments

    def _payment_schedule_table(self, payments):
        if not payments:
            return ""
        rows = []
        for p in payments:
            date_str = p['due_date'].strftime('%d/%m/%Y') if p['due_date'] else '—'
            is_acompte = 'Acompte' in p['label']
            rows.append(f"""
                <tr style="background-color:{'#e8f4fd' if is_acompte else 'transparent'}">
                    <td style="padding:8px;border:1px solid #ddd;{'font-weight:bold;' if is_acompte else ''}">{p['label']}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{date_str}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{p['amount']:,.0f} {self.currency_id.name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{p['rate']}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{p['state']}</td>
                </tr>
            """)
        return f"""
        <h3 style="color:#333;margin-top:20px;">{_('Échéancier de Paiement')}</h3>
        <table border="1" cellpadding="5" cellspacing="0" width="100%" style="border-collapse:collapse;margin-top:10px;">
            <thead>
                <tr style="background-color:#f8f9fa;">
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">{_('Échéance')}</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_("Date d'échéance")}</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_('Montant dû')}</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_('Taux (%)')}</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_('Statut')}</th>
                </tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        """

    def _render_lines_table(self):
        lines = []
        for l in self.order_line:
            lines.append(f"""
                <tr>
                    <td style="padding:8px;border:1px solid #ddd;">{l.product_id.display_name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{int(l.product_uom_qty)}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_unit:,.0f} {self.currency_id.name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_total:,.0f} {self.currency_id.name}</td>
                </tr>
            """)
        return f"""
            <h3 style="color:#333;margin:15px 0 10px 0;">{_('Produits commandés')}</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;border:1px solid #DDD;">
                <thead>
                    <tr style="background:#F8F9FA;">
                        <th align="left"  style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">{_('Produit')}</th>
                        <th align="center"style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">{_('Qté')}</th>
                        <th align="right" style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">{_('PU')}</th>
                        <th align="right" style="padding:10px;border-bottom:1px solid #DDD;font-size:13px;">{_('Total')}</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(lines)}
                    <tr style="background:#F8F9FA;font-weight:bold;">
                        <td colspan="3" align="right" style="padding:10px;border-top:1px solid #DDD;">{_('Total panier')}</td>
                        <td align="right" style="padding:10px;border-top:1px solid #DDD;">{self.amount_total:,.0f} {self.currency_id.name}</td>
                    </tr>
                </tbody>
            </table>
        """

    def _render_payments_table_compact(self):
        rows = []
        total = float(self.amount_total or 0.0)
        residual = float(getattr(self, 'amount_residual', 0.0) or 0.0)
        paid = max(0.0, total - residual)
        percent = (paid / total * 100.0) if total else 0.0

        for l in self.credit_payment_ids.sorted(lambda x: x.sequence):
            label = _("Acompte") if l.sequence == 1 else _("Échéance %(n)s", n=l.sequence)
            due = (l.due_date.strftime('%d/%m/%Y')
                   if isinstance(l.due_date, (date, datetime)) and l.due_date else '—')
            rows.append(f"""
                <tr>
                    <td style="padding:8px;border:1px solid #ddd;">{label}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{due}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{(l.amount or 0.0):,.0f} {self.currency_id.name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{l.rate}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{(_("Payé") if l.state else _("Non payé"))}</td>
                </tr>
            """)
        return f"""
            <h3 style="color:#333;margin:20px 0 10px 0;">{_('Récapitulatif des paiements')}</h3>
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;border:1px solid #DDD;">
                <thead>
                    <tr style="background:#F8F9FA;">
                        <th style="padding:10px;border-bottom:1px solid #DDD;text-align:left;">{_('Échéance')}</th>
                        <th style="padding:10px;border-bottom:1px solid #DDD;text-align:center;">{_('Date')}</th>
                        <th style="padding:10px;border-bottom:1px solid #DDD;text-align:right;">{_('Montant')}</th>
                        <th style="padding:10px;border-bottom:1px solid #DDD;text-align:center;">%</th>
                        <th style="padding:10px;border-bottom:1px solid #DDD;text-align:center;">{_('Statut')}</th>
                    </tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>

            <div style="margin-top:12px;background:#F8F9FA;padding:10px;border-radius:6px;">
                <p style="margin:4px 0;"><strong>{_('Montant payé')} :</strong> {paid:,.0f} {self.currency_id.name}</p>
                <p style="margin:4px 0;"><strong>{_('Reste à payer')} :</strong> {residual:,.0f} {self.currency_id.name}</p>
                <p style="margin:4px 0;"><strong>{_('Avancement')} :</strong> {percent:.1f}%</p>
            </div>
        """

    # ---------------------------------------------------------------------
    # ======================  MAIL "MISE À JOUR"  ==========================
    # ---------------------------------------------------------------------
    def _render_update_mail(self, reasons):
        partner = self.partner_id
        partner_name = self._partner_display_name(partner)
        return f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               style="width:100%;background:#FFFFFF;font-family:Verdana, Arial, sans-serif;color:#454748;border-collapse:separate;padding-top:16px;">
          <tr><td align="center" style="padding:0 8px;">
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
                   style="background:#FFFFFF;color:#454748;border-collapse:separate;padding:16px;">
              <tr>
                <td valign="middle" style="padding:0;">
                  <span style="font-size:10px;display:block;line-height:1.4;">{_('Mise à jour de votre commande à crédit')}</span>
                  <span style="font-size:20px;font-weight:bold;display:block;line-height:1.4;">{self.name}</span>
                </td>
                <td valign="middle" align="right" style="padding:0;">
                  <img src="{LOGO_URL}" width="120" height="auto" alt="Logo CCBM SHOP"
                       style="display:block;border:0;outline:none;text-decoration:none;" />
                </td>
              </tr>
              <tr><td colspan="2"><hr style="border:none;height:1px;background:#CCC;margin:16px 0;" /></td></tr>

              <tr><td colspan="2" style="padding:0;">
                <p style="margin:0 0 12px 0;line-height:1.6;">{_('Bonjour')} {partner_name},</p>
                <p style="margin:0 0 12px 0;line-height:1.6;">{_('Nous vous informons qu’un changement a été effectué sur votre commande')}:</p>
                <ul style="margin:0 0 12px 16px;padding:0;line-height:1.6;">
                  {''.join([f"<li>{r}</li>" for r in reasons])}
                </ul>
              </td></tr>

              <tr><td colspan="2" style="padding:0;">{self._render_lines_table()}</td></tr>
              <tr><td colspan="2" style="padding-top:12px;">{self._render_payments_table_compact()}</td></tr>
            </table>

            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
                   style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
              <tr>
                <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
                  <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
                  <div>🛍️ <a href="{SITE_URL}" target="_blank" rel="noopener"
                             style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        """

    def _send_update_mail_to_customer(self, reasons):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            _logger.warning("Pas de serveur mail configuré — email non envoyé.")
            return
        partner = self.partner_id
        email = self._partner_email(partner)
        if not email:
            _logger.warning("Aucun e-mail client — email non envoyé.")
            return

        body_html = self._render_update_mail(reasons)
        email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
        email_to = ', '.join(filter(None, [email, 'shop@ccbm.sn']))
        mail_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': _("Mise à jour de votre commande à crédit %s") % (self.name,),
            'body_html': body_html,
            'state': 'outgoing',
            'auto_delete': False,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
        _logger.info("Mail update envoyé à %s pour %s", email_to, self.name)

    # ---------------------------------------------------------------------
    # ======================  ENVOIS MAILS CRÉDIT  =========================
    # ---------------------------------------------------------------------
    def get_sale_order_credit_payment(self):
        """API simple (pérennisée) — retourne l'échéancier au format dict."""
        try:
            payments = self.env['sale.order.credit.payment'].search([('order_id', '=', self.id)])
            data = []
            for payment in payments:
                data.append({
                    'sequence': payment.sequence,
                    'due_date': (payment.due_date.isoformat()
                                 if hasattr(payment.due_date, 'isoformat')
                                 else str(payment.due_date)),
                    'amount': payment.amount,
                    'rate': payment.rate,
                    'state': payment.state,
                })
            return data
        except Exception as e:
            _logger.error('Erreur lors de la récupération des paiements : %s', e, exc_info=True)
            return []

    def send_credit_order_validation_mail(self):
        """
        Mail de validation de la création d'une commande à crédit (au client).
        """
        try:
            mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                return {'status': 'error', 'message': 'Mail server not configured'}

            partner = self.partner_id
            email = self._partner_email(partner)
            if not email:
                return {'status': 'error', 'message': 'Partner email not found'}

            payments = self._get_credit_payments()
            payment_schedule_html = self._payment_schedule_table(payments)

            total_amount = sum(l.price_total for l in self.order_line)
            lines_html = []
            for l in self.order_line:
                lines_html.append(f"""
                    <tr>
                        <td style="padding:8px;border:1px solid #ddd;">{l.product_id.display_name}</td>
                        <td style="padding:8px;border:1px solid #ddd;text-align:center;">{int(l.product_uom_qty)}</td>
                        <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_unit:,.0f} {self.currency_id.name}</td>
                        <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_total:,.0f} {self.currency_id.name}</td>
                    </tr>
                """)

            partner_name = self._partner_display_name(partner)
            body_html = f"""
                <table border="0" cellpadding="0" cellspacing="0" style="padding-top:16px;background:#FFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
                    <tr><td align="center">
                        <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding:16px;background:#FFF;color:#454748;border-collapse:separate;">
                            <tr>
                                <td valign="middle">
                                    <span style="font-size:10px;">{_('Validation de votre commande à crédit')}</span><br/>
                                    <span style="font-size:20px;font-weight:bold;">{self.name}</span>
                                </td>
                                <td valign="middle" align="right">
                                    <img style="width:120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
                                </td>
                            </tr>
                            <tr><td colspan="2"><hr style="border:none;height:1px;background:#ccc;margin:16px 0"/></td></tr>
                            <tr><td colspan="2">
                                <p>{_('Félicitations')} {partner_name}, {_('votre commande à crédit a été créée.')}</p>
                                <h3 style="color:#333;margin:15px 0;">{_('Produits commandés')}</h3>
                                <table border="1" cellpadding="5" cellspacing="0" width="100%" style="border-collapse:collapse;">
                                    <thead>
                                        <tr style="background:#f8f9fa;">
                                            <th style="padding:10px;border:1px solid #ddd;">{_('Produit')}</th>
                                            <th style="padding:10px;border:1px solid #ddd;">{_('Qté')}</th>
                                            <th style="padding:10px;border:1px solid #ddd;">{_('PU')}</th>
                                            <th style="padding:10px;border:1px solid #ddd;">{_('Total')}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {''.join(lines_html)}
                                        <tr style="background:#f8f9fa;font-weight:bold;">
                                            <td colspan="3" style="padding:10px;border:1px solid #ddd;text-align:right;">{_('Total du panier')}</td>
                                            <td style="padding:10px;border:1px solid #ddd;text-align:right;">{total_amount:,.0f} {self.currency_id.name}</td>
                                        </tr>
                                    </tbody>
                                </table>
                                {payment_schedule_html or ''}
                            </td></tr>
                        </table>
                    </td></tr>
                     <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
                        <td colspan="2" style="padding: 12px; text-align: center;">
                            <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                            <p><a href="{SITE_URL}" style="color: #875A7B;">www.ccbmshop.sn</a></p>
                        </td>
                    </tr>
                </table>
            """

            return self._send_mail_common(mail_server, partner, _('Validation de votre commande à crédit'), body_html, sms_type='validation')

        except Exception as e:
            _logger.error("Erreur mail validation %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}


    def send_payment_status_mail_creditorder(self):
        """Mail de mise à jour de statut de paiement (au client)."""
        try:
            mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                return {'status': 'error', 'message': 'Mail server not configured'}
            partner = self.partner_id
            email = self._partner_email(partner)
            if not email:
                return {'status': 'error', 'message': 'Partner email not found'}

            payments = self._get_credit_payments()
            payment_info = self._payment_schedule_table(payments)

            total = float(self.amount_total or 0.0)
            residual = float(getattr(self, 'amount_residual', 0.0) or 0.0)
            paid = max(0.0, total - residual)
            percent = (paid / total * 100.0) if total else 0.0

            partner_name = self._partner_display_name(partner)
            summary = f"""
                <div style="margin-top:20px;background:#f8f9fa;padding:12px;border-radius:6px;">
                    <p><strong>{_('Prix total')}:</strong> {total:,.0f} {self.currency_id.name}</p>
                    <p><strong>{_('Montant payé')}:</strong> {paid:,.0f} {self.currency_id.name}</p>
                    <p><strong>{_('Reste à payer')}:</strong> {residual:,.0f} {self.currency_id.name}</p>
                    <p><strong>{_('Pourcentage payé')}:</strong> {percent:.1f}%</p>
                </div>
            """

            head = f"""
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
                <tr>
                    <td valign="middle">
                        <span style="font-size:10px;">{_('Commande à crédit')}</span><br/>
                        <span style="font-size:20px;font-weight:bold;">{self.name}</span>
                    </td>
                    <td valign="middle" align="right">
                        <img style="width:120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
                    </td>
                </tr>
                <tr>
                    <td colspan="2" style="text-align:center;">
                        <hr width="100%" style="background:#ccc;border:none;display:block;height:1px;margin:16px 0;"/>
                    </td>
                </tr>
            </table>
            """

            body_html = f"""
            <tr><td align="center" style="min-width:590px;">{head}</td></tr>
            <p>{_('Bonjour')} {partner_name}, {_('voici une mise à jour de l\'état de votre commande')} {self.name}.</p>
            {payment_info}
            {summary}
            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
                style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
              <tr>
                <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
                  <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
                  <div>🛍️ <a href="{SITE_URL}" target="_blank" rel="noopener"
                             style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
                </td>
              </tr>
            </table>
            """
            return self._send_mail_common(mail_server, partner, _("Mise à jour de l'état de votre commande à crédit"), body_html)

        except Exception as e:
            _logger.error("Erreur mail statut %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    # ---- Enveloppes simples RH/Admin vers client ----
    def send_credit_order_rh_rejected(self):
        return self._simple_templated_mail('rh_rejection', _('Rejet de votre commande à crédit par le service RH'))

    def send_credit_order_rh_validation(self):
        return self._simple_templated_mail('rh_validation', _('Validation RH de votre commande à crédit'))

    def send_credit_order_admin_validation(self):
        return self._simple_templated_mail('admin_validation', _("Validation administrative de votre commande à crédit"))

    def send_credit_order_admin_rejected(self):
        return self._simple_templated_mail('admin_rejection', _("Rejet de votre commande à crédit par l'administration"))

    def _simple_templated_mail(self, template_key, subject):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return {'status': 'error', 'message': 'Mail server not configured'}
        partner = self.partner_id
        email = self._partner_email(partner)
        if not email:
            return {'status': 'error', 'message': 'Partner email not found'}
        body_html = self._generate_email_body_html(partner, template_key)
        return self._send_mail_common(mail_server, partner, subject, body_html,
                                      sms_type=template_key if template_key in (
                                          'validation', 'rejection',
                                          'rh_rejection', 'admin_rejection',
                                          'admin_validation', 'rh_validation'
                                      ) else None)

    # ---------------------------------------------------------------------
    # ======================  NOTIFS RH / ADMIN  ===========================
    # ---------------------------------------------------------------------
    def send_credit_order_to_admin_for_validation(self):
        """
        Après validation RH: prévenir un admin système par mail.
        """
        try:
            mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                return {'status': 'error', 'message': 'Mail server not configured'}

            admin_group = self.env.ref('base.group_system')
            admin_user = self.env['res.users'].sudo().search([('groups_id', 'in', admin_group.id)], limit=1)
            if not admin_user or not admin_user.partner_id.email:
                return {'status': 'error', 'message': 'No admin user with email'}

            subject = _('Confirmation requise pour la commande à crédit - %s') % self.name
            body_html = self._generate_admin_notification_email(admin_user)
            return self._send_mail_common(mail_server, admin_user.partner_id, subject, body_html)
        except Exception as e:
            _logger.error("Erreur notif admin %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def send_credit_order_creation_notification_to_hr(self):
        """
        À la création d'une demande de crédit: prévenir la RH (de l'employeur).
        """
        try:
            mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            if not mail_server:
                return {'status': 'error', 'message': 'Mail server not configured'}

            company = self._partner_company(self.partner_id)
            if not company:
                return {'status': 'error', 'message': 'No company (employer/parent) found'}

            rh_user = self._find_company_rh_user(company)
            if not rh_user or not self._partner_email(rh_user):
                return {'status': 'error', 'message': 'HR user not found'}

            subject = _('Nouvelle commande à valider')
            body_html = self._generate_hr_notification_email()
            return self._send_mail_common(mail_server, rh_user, subject, body_html, sms_type='hr_notification')
        except Exception as e:
            _logger.error("Erreur notif RH %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    # ---------------------------------------------------------------------
    # =====================  GABARITS HTML COMMUNS  ========================
    # ---------------------------------------------------------------------
    def _generate_admin_notification_email(self, admin_user):
        return f'''
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
            <tr><td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
                    <tbody>
                        <tr><td align="center" style="min-width: 590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                <tr>
                                    <td valign="middle">
                                        <span style="font-size: 10px;">{_('Commande à crédit')}</span><br/>
                                        <span style="font-size: 20px; font-weight: bold;">{self.name}</span>
                                    </td>
                                    <td valign="middle" align="right">
                                        <img style="height:auto;width:120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
                                    </td>
                                </tr>
                                <tr><td colspan="2" style="text-align:center;">
                                    <hr width="100%" style="background-color:#CCC;border:none;display:block;height:1px;margin:16px 0;"/>
                                </td></tr>
                            </table>
                        </td></tr>
                        <tr><td align="center" style="min-width:590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:white;padding:0 8px;border-collapse:separate;">
                                <tr><td>
                                    <p>{_('Bonjour')} {self.company_id.name or ''},</p>
                                    <p>{_('Le service RH a confirmé la commande à crédit suivante')} :</p>
                                    <ul>
                                        <li>{_('Numéro de commande')} : {self.name}</li>
                                        <li>{_('Client')} : {self._partner_display_name(self.partner_id)}</li>
                                        <li>{_('Montant total')} : {self.amount_total:,.0f} {self.currency_id.name}</li>
                                        <li>{_("Pourcentage d'acompte")} : {getattr(self, 'credit_month_rate', 0)}%</li>
                                        <li>{_('Nombre d’échéances')} : {getattr(self, 'creditorder_month_count', 0)} {_('Paiement(s)')}</li>
                                    </ul>
                                    <p>{_('Votre confirmation est maintenant requise pour finaliser cette commande.')}<br/>{_('Veuillez vous connecter au système pour examiner et valider cette commande.')}</p>
                                    <p>{_('Cordialement')},<br/>{_('Système automatique')}</p>
                                </td></tr>
                            </table>
                        </td></tr>
                    </tbody>
                </table>
            </td></tr>
            <tr style="background:#F1F1F1;font-size:13px;color:#555;">
                <td style="padding:12px;text-align:center;">
                    <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                    <p><a href="{SITE_URL}" style="color:#875A7B;">www.ccbmshop.sn</a></p>
                </td>
            </tr>
        </table>
        '''

    def _generate_hr_notification_email(self):
        return f'''
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
            <tr><td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
                    <tbody>
                        <tr><td align="center" style="min-width:590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:white;padding:0 8px;border-collapse:separate;">
                                <tr>
                                    <td valign="middle">
                                        <span style="font-size: 10px;">{_('Commande à crédit')}</span><br/>
                                        <span style="font-size: 20px; font-weight: bold;">{self.name}</span>
                                    </td>
                                    <td valign="middle" align="right">
                                        <img style="height:auto;width:120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
                                    </td>
                                </tr>
                                <tr><td colspan="2" style="text-align:center;">
                                    <hr width="100%" style="background-color:#CCC;border:none;display:block;height:1px;margin:16px 0;"/>
                                </td></tr>
                            </table>
                        </td></tr>
                        <tr><td align="center" style="min-width:590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:white;padding:0 8px;border-collapse:separate;">
                                <tr><td>
                                    <p>{_('Bonjour')},</p>
                                    <p>{_('Une nouvelle demande de commande à crédit a été créée et nécessite votre validation')} :</p>
                                    <ul>
                                        <li>{_('Numéro de commande')} : {self.name}</li>
                                        <li>{_('Client')} : {self._partner_display_name(self.partner_id)}</li>
                                        <li>{_('Montant total')} : {self.amount_total:,.0f} {self.currency_id.name}</li>
                                        <li>{_('Date de création')} : {self.create_date.strftime('%d/%m/%Y %H:%M') if self.create_date else '—'}</li>
                                    </ul>
                                    <p>{_('Veuillez examiner cette demande et prendre les mesures appropriées dans votre interface d’administration.')}<br/>{_('Cordialement')},<br/>{_('Système automatique CCBM Shop')}</p>
                                </td></tr>
                            </table>
                        </td></tr>
                    </tbody>
                </table>
            </td></tr>
            <tr style="background:#F1F1F1;font-size:13px;color:#555;">
                <td style="padding:12px;text-align:center;">
                    <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                    <p><a href="{SITE_URL}" style="color:#875A7B;">www.ccbmshop.sn</a></p>
                </td>
            </tr>
        </table>
        '''

    def _generate_email_body_html(self, partner, email_type, additional_content=""):
        partner_name = self._partner_display_name(partner)
        email_content = {
            'validation': {
                'title': _('Validation de votre commande à crédit'),
                'content': f"""
                    <p>{_('Félicitations')} {partner_name},</p>
                    <p>{_('Votre commande à crédit numéro')} {self.name} {_('a été créée avec succès')}.</p>
                    <p>{_('Détails des échéances')} :</p>
                """
            },
            'rejection': {
                'title': _('Rejet de votre commande à crédit'),
                'content': f"""
                    <p>{_('Cher(e)')} {partner_name},</p>
                    <p>{_('Nous regrettons de vous informer que votre commande à crédit numéro')} {self.name} {_('a été rejetée')}.</p>
                    <p>{_("Si vous avez des questions, n'hésitez pas à nous contacter.")}</p>
                """
            },
            'rh_rejection': {
                'title': _('Rejet de votre commande à crédit par le service RH'),
                'content': f"""
                    <p>{_('Cher(e)')} {partner_name},</p>
                    <p>{_('Votre commande à crédit numéro')} {self.name} {_('a été rejetée par votre service des Ressources Humaines')}.</p>
                    <p>{_("Pour plus d'informations, contactez notre service client.")}</p>
                """
            },
            'admin_rejection': {
                'title': _("Rejet de votre commande à crédit par l'administration"),
                'content': f"""
                    <p>{_('Cher(e)')} {partner_name},</p>
                    <p>{_('Votre commande à crédit numéro')} {self.name} {_('a été rejetée par notre administration')}.</p>
                    <p>{_("Pour plus d'informations, contactez notre service client.")}</p>
                """
            },
            'admin_validation': {
                'title': _('Validation administrative de votre commande à crédit'),
                'content': f"""
                    <p>{_('Cher(e)')} {partner_name},</p>
                    <p>{_('Votre commande à crédit numéro')} {self.name} {_('a été validée par notre administration')}.</p>
                    <p>{_('Veuillez vous connecter pour régler')} {getattr(self, 'credit_month_rate', 0)}% {_('du montant de la commande')}.</p>
                """
            },
            'rh_validation': {
                'title': _('Validation RH de votre commande à crédit'),
                'content': f"""
                    <p>{_('Cher(e)')} {partner_name},</p>
                    <p>{_('Votre commande à crédit numéro')} {self.name} {_('a été validée par votre service RH')}.</p>
                    <p>{_("Patientez la validation finale de CCBM Shop avant de procéder au paiement.")}</p>
                """
            },
            'request': {
                'title': _('Votre demande de commande à crédit'),
                'content': f"""
                    <p>{_('Bonjour')} {partner_name},</p>
                    <p>{_('Nous avons bien reçu votre demande de commande à crédit numéro')} {self.name}.</p>
                    <p>{_('Elle est en cours de validation par nos services.')} {_('Nous vous tiendrons informé.')}</p>
                """
            },
            'payment_status': {
                'title': _("Mise à jour de l'état de votre commande à crédit"),
                'content': f"""
                    <p>{_('Bonjour')} {partner_name},</p>
                    <p>{_("Voici la mise à jour de l'état de votre commande à crédit numéro")} {self.name}.</p>
                """
            }
        }

        content_info = email_content.get(email_type, {
            'title': _('Notification de commande à crédit'),
            'content': f'<p>{_("Bonjour")} {partner_name},</p><p>{_("Notification concernant votre commande")} {self.name}.</p>'
        })

        return f"""
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top:16px;background:#FFFFFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
            <tr><td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding:16px;background:#FFFFFF;color:#454748;border-collapse:separate;">
                    <tbody>
                        <tr><td align="center" style="min-width:590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
                                <tr>
                                    <td valign="middle">
                                        <span style="font-size:10px;">{content_info['title']}</span><br/>
                                        <span style="font-size:20px;font-weight:bold;">{self.name}</span>
                                    </td>
                                    <td valign="middle" align="right">
                                        <img style="height:auto;width:120px;" src="{LOGO_URL}" alt="logo CCBM SHOP"/>
                                    </td>
                                </tr>
                                <tr><td colspan="2" style="text-align:center;">
                                    <hr width="100%" style="background:#CCC;border:none;display:block;height:1px;margin:16px 0;"/>
                                </td></tr>
                            </table>
                        </td></tr>
                        <tr><td align="center" style="min-width:590px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
                                <tr><td>
                                    {content_info['content']}
                                </td></tr>
                            </table>
                        </td></tr>
                        {additional_content}
                    </tbody>
                </table>
            </td></tr>
            <tr style="background:#F1F1F1;font-size:13px;color:#555;">
                <td style="padding:12px;text-align:center;">
                    <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
                    <p><a href="{SITE_URL}" style="color:#875A7B;">www.ccbmshop.sn</a></p>
                </td>
            </tr>
        </table>
        """

    # ---------------------------------------------------------------------
    # ==================  ENVOI COMMUN MAIL + SMS  ========================
    # ---------------------------------------------------------------------
    def _send_mail_common(self, mail_server, partner, subject, body_html, sms_type=None):
        """
        Envoi mail via mail.mail + SMS optionnel via module 'send.sms' (si dispo).
        """
        try:
            email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
            email_to = ', '.join(filter(None, [self._partner_email(partner), 'shop@ccbm.sn']))
            if not email_to:
                return {'status': 'error', 'message': 'No recipient'}

            mail_values = {
                'email_from': email_from,
                'email_to': email_to,
                'subject': subject,
                'body_html': body_html,
                'state': 'outgoing',
                'auto_delete': False,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
            _logger.info("Mail '%s' envoyé à %s pour %s", subject, email_to, self.name)

            # Envoi SMS si demandé et si module présent
            if sms_type:
                phone = self._partner_phone(partner)
                if phone:
                    Sms = self.env.get('send.sms')
                    if Sms:
                        sms_rec = Sms.create({'recipient': phone, 'message': self._sms_message(sms_type)})
                        try:
                            sms_rec.send_sms()
                            _logger.info("SMS '%s' envoyé à %s pour %s", sms_type, phone, self.name)
                        except Exception as se:
                            _logger.error("Échec envoi SMS (%s) à %s: %s", sms_type, phone, se, exc_info=True)
                    else:
                        _logger.warning("Module send.sms indisponible — SMS non envoyé")
            return {'status': 'success'}

        except Exception as e:
            _logger.error("Erreur envoi mail %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _sms_message(self, kind):
        partner_name = self._partner_display_name(self.partner_id)
        m = {
            'validation': _("Bonjour %(name)s, votre commande à crédit %(order)s a été créée.", name=partner_name, order=self.name),
            'rejection': _("Bonjour %(name)s, votre commande à crédit %(order)s a été rejetée.", name=partner_name, order=self.name),
            'rh_rejection': _("Bonjour %(name)s, votre commande %(order)s a été rejetée par le service RH.", name=partner_name, order=self.name),
            'admin_rejection': _("Bonjour %(name)s, votre commande %(order)s a été rejetée par l'administration.", name=partner_name, order=self.name),
            'admin_validation': _("Bonjour %(name)s, votre commande %(order)s a été validée par l'administration.", name=partner_name, order=self.name),
            'rh_validation': _("Bonjour %(name)s, votre commande %(order)s a été validée par le service RH.", name=partner_name, order=self.name),
            'request': _("Bonjour %(name)s, votre demande de commande à crédit %(order)s est en cours.", name=partner_name, order=self.name),
            'creation': _("Bonjour %(name)s, votre commande %(order)s a été créée.", name=partner_name, order=self.name),
            'hr_notification': _("Bonjour, la commande %(order)s nécessite une validation RH.", order=self.name),
        }
        return m.get(kind, _("Notification commande %(order)s", order=self.name))

    # ---------------------------------------------------------------------
    # =============  CONFIRMATION COMMANDE (hors crédit)  ==================
    # ---------------------------------------------------------------------
    def send_order_confirmation_mail(self):
        """Confirmation de commande classique (type_sale == 'order')."""
        self.ensure_one()
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            return True

        partner = self.partner_id
        email = self._partner_email(partner)
        if not email:
            return True

        base_url = SITE_URL.rstrip('/')

        # Fenêtre de livraison estimée
        commitment_date = getattr(self, 'commitment_date', False) or (datetime.now() + timedelta(days=7))
        if isinstance(commitment_date, datetime):
            d0 = commitment_date
        else:
            try:
                d0 = datetime.combine(commitment_date, datetime.min.time())
            except Exception:
                d0 = datetime.now() + timedelta(days=7)
        d1 = d0 + timedelta(days=3)
        delivery_window_str = _("Entre le %(d0)s et %(d1)s", d0=d0.strftime('%d/%m/%Y'), d1=d1.strftime('%d/%m/%Y'))

        payment_label = getattr(self, 'payment_term_id', False) and self.payment_term_id.name or _("Paiement à la livraison")

        partner_name = self._partner_display_name(partner)
        has_user = bool(email)  # simplifié ; ajuste si tu veux vérifier res.users
        create_account_section = ""
        if not has_user:
            create_account_link = f"{base_url}/create-compte?mail={email}"
            create_account_section = f'''
                <tr>
                    <td align="center" style="min-width:590px;padding-top:20px;">
                        <span style="font-size:14px;">{_('Créez un compte pour suivre votre commande')} :</span><br/>
                        <a href="{create_account_link}" style="font-size:16px;font-weight:bold;color:#875A7B;">{_('Créer un compte')}</a>
                    </td>
                </tr>
            '''

        lines_html = []
        for l in self.order_line:
            lines_html.append(f"""
                <tr>
                    <td style="padding:8px;border:1px solid #ddd;">{l.product_id.display_name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:center;">{int(l.product_uom_qty)}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_unit:,.0f} {self.currency_id.name}</td>
                    <td style="padding:8px;border:1px solid #ddd;text-align:right;">{l.price_total:,.0f} {self.currency_id.name}</td>
                </tr>
            """)

        phone_txt = self._partner_phone(partner)
        address_txt = self._partner_address_text(partner)

        subject = _('Confirmation de votre commande')
        body_html = f'''
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top:16px;background:#FFFFFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
        <tr><td align="center">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding:16px;background:#FFFFFF;color:#454748;border-collapse:separate;">
            <tbody>
                <tr><td align="center" style="min-width:590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
                    <tr>
                        <td valign="middle">
                        <span style="font-size:10px;">{_('Votre commande')}</span><br/>
                        <span style="font-size:20px;font-weight:bold;">{self.name}</span>
                        </td>
                        <td valign="middle" align="right">
                        <img src="{LOGO_URL}" alt="Logo CCBM SHOP" style="width:120px;height:auto;display:block;border:0;outline:none;text-decoration:none;"/>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" style="text-align:center;">
                        <hr width="100%" style="background:#ccc;border:none;display:block;height:1px;margin:16px 0;"/>
                        </td>
                    </tr>
                    </table>
                </td></tr>

                <tr><td align="center" style="min-width:590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
                    <tr>
                        <td valign="middle" style="width:50%;">
                        <span style="font-size:15px;font-weight:bold;">{_('Détails du destinataire')}</span>
                        </td>
                        <td valign="middle" align="right" style="width:50%;">
                        {partner_name}<br/>{phone_txt or ''}
                        </td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width:50%;">
                        <span style="font-size:15px;font-weight:bold;">{_('Adresse')}</span>
                        </td>
                        <td valign="middle" align="right" style="width:50%;">{address_txt}</td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width:50%;">
                        <span style="font-size:15px;font-weight:bold;">{_('Date de livraison estimée')}</span>
                        </td>
                        <td valign="middle" align="right" style="width:50%;">{delivery_window_str}</td>
                    </tr>
                    <tr>
                        <td valign="middle" style="width:50%;">
                        <span style="font-size:15px;font-weight:bold;">{_('Méthode de paiement')}</span>
                        </td>
                        <td valign="middle" align="right" style="width:50%;">{payment_label}</td>
                    </tr>
                    </table>
                </td></tr>

                <tr><td align="center" style="min-width:590px;">
                    <table border="1" cellpadding="5" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#f8f9fa;">
                        <th align="left"  style="padding:10px;border:1px solid #ddd;">{_('Produit')}</th>
                        <th align="center"style="padding:10px;border:1px solid #ddd;">{_('Quantité')}</th>
                        <th align="right" style="padding:10px;border:1px solid #ddd;">{_('Prix unitaire')}</th>
                        <th align="right" style="padding:10px;border:1px solid #ddd;">{_('Total')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(lines_html)}
                        <tr style="background:#f8f9fa;font-weight:bold;">
                        <td colspan="3" align="right" style="padding:10px;border:1px solid #ddd;">{_('Total du panier')}</td>
                        <td align="right" style="padding:10px;border:1px solid #ddd;">{self.amount_total:,.0f} {self.currency_id.name}</td>
                        </tr>
                    </tbody>
                    </table>
                </td></tr>

                {create_account_section}

            </tbody>
            </table>

            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
                style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
            <tr>
                <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
                <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
                <div>🛍️ <a href="{SITE_URL}" target="_blank" rel="noopener"
                            style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
                </td>
            </tr>
            </table>

        </td></tr>
        </table>
        '''
        return self._send_mail_common(
            mail_server=mail_server,
            partner=partner,
            subject=subject,
            body_html=body_html,
            sms_type=None,
        )
