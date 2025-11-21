

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
import logging
import unicodedata
import re

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

    def _has_partner_email(self, partner):
        """Vérifie si le partenaire a un email."""
        return bool((getattr(partner, 'email', '') or '').strip())

    def _mail_server_or_raise(self):
        """Récupère le serveur mail ou lève une exception."""
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))
        return mail_server

    def _fmt_money(self, amount):
        """Formate un montant avec la devise."""
        cur = self.currency_id.name or ''
        try:
            return f"{float(amount or 0.0):,.0f} {cur}"
        except Exception:
            return f"{amount} {cur}"

    def _create_account_section_if_needed(self, partner):
        """
        Affiche 'Créer un compte' si le partenaire a un email mais pas de password (champ custom).
        """
        if not partner or not self._has_partner_email(partner):
            return ""
        if getattr(partner, 'password', False):
            return ""
        base_url = SITE_URL.rstrip('/')
        link = f"{base_url}/create-compte?mail={self._partner_email(partner)}"
        return f"""
        <tr>
          <td align="center" style="min-width:590px;padding-top:20px;">
            <span style="font-size:14px;">{_('Créez un compte pour suivre votre commande à crédit')} :</span><br/>
            <a href="{link}" style="font-size:16px;font-weight:bold;color:#875A7B;">{_('Créer un compte')}</a>
          </td>
        </tr>
        """

    def _coerce_date(self, v):
        """Alias pour _coerce_to_date pour compatibilité."""
        return self._coerce_to_date(v)

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
        """
        Redéfinition write :
        - on prend un snapshot des états et des données,
        - on écrit,
        - on notifie si transitions d'états ou changements de données.
        """
        # Sauvegarde avant écriture
        snapshots = {rec.id: rec._snapshot_for_update() for rec in self}
        prev_states = {r.id: r._snapshot_states() for r in self}

        res = super().write(vals)

        # Après écriture: décisions/notifications
        for order in self:
            try:
                if order.type_sale == 'creditorder':
                    # 1) Gestion des transitions d'états RH/Admin
                    before_states = prev_states.get(order.id, {})
                    order._handle_state_transitions(before_states)

                    # 2) Mail client "mise à jour" si changements de données
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

    def _coerce_date(self, v):
        """Alias pour _coerce_to_date pour compatibilité."""
        return self._coerce_to_date(v)

    def _get_credit_type_label(self):
        """Retourne le libellé du type de crédit."""
        credit_type_map = {
            'particulier': _('Particulier'),
            'direct': _('Crédit Direct'),
            'banque': _('Crédit bancaire'),
            'finance': _('Crédit financier'),
        }
        credit_type = getattr(self, 'credit_type', '') or ''
        return credit_type_map.get(credit_type, _('Crédit'))

    def _is_bank_credit(self):
        """Vérifie si le type de crédit est bancaire ou financier."""
        credit_type = getattr(self, 'credit_type', '') or ''
        return credit_type in ('banque', 'finance')

    def _is_direct_credit(self):
        """Vérifie si le type de crédit est direct."""
        credit_type = getattr(self, 'credit_type', '') or ''
        return credit_type == 'direct'

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
<<<<<<< Updated upstream

    def _payment_schedule_table(self, payments):
=======
    
    def generate_payment_schedule_html(self, payments): 
        """
        Génère le HTML pour afficher l'échéancier de paiement
        """
>>>>>>> Stashed changes
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

    def _payment_rows_from_plan(self):
        """
        Utilise sale.order.credit.payment si dispo; sinon fallback 50/20/15/15.
        Pour les crédits banque/finance, les dates d'échéance sont ajustées à la fin du mois.
        """
        from calendar import monthrange
        
        rows = []
        plan = self.mapped('credit_payment_ids')
        is_bank = self._is_bank_credit()
        
        if plan:
            for l in plan.sorted(lambda r: r.sequence):
                label = _("Premier Paiement (Acompte)") if l.sequence == 1 else _("Échéance %(n)s", n=l.sequence)
                due = self._coerce_date(l.due_date)
                
                # Pour crédits banque/finance, ajuster les dates à la fin du mois
                if is_bank and due and l.sequence > 1:  # Pas pour l'acompte
                    # Calculer la fin du mois pour la date d'échéance
                    year = due.year
                    month = due.month
                    last_day = monthrange(year, month)[1]
                    due = date(year, month, last_day)
                
                rows.append((label, float(l.amount or 0.0), f"{l.rate}", due))
            return rows

        # Fallback
        today = datetime.now().date()
        total = float(self.amount_total or 0.0)
        
        # Pour crédits banque/finance, utiliser la fin du mois
        if is_bank:
            # Calculer les dates à la fin des mois suivants
            current_year = today.year
            current_month = today.month
            
            # Premier paiement : dans 3 jours (pas de changement)
            first_payment_date = today + timedelta(days=3)
            
            # Deuxième paiement : fin du mois suivant
            next_month = current_month + 1
            next_year = current_year
            if next_month > 12:
                next_month = 1
                next_year += 1
            last_day_month1 = monthrange(next_year, next_month)[1]
            second_payment_date = date(next_year, next_month, last_day_month1)
            
            # Troisième paiement : fin du mois +2
            month_plus2 = next_month + 1
            year_plus2 = next_year
            if month_plus2 > 12:
                month_plus2 = 1
                year_plus2 += 1
            last_day_month2 = monthrange(year_plus2, month_plus2)[1]
            third_payment_date = date(year_plus2, month_plus2, last_day_month2)
            
            # Quatrième paiement : fin du mois +3
            month_plus3 = month_plus2 + 1
            year_plus3 = year_plus2
            if month_plus3 > 12:
                month_plus3 = 1
                year_plus3 += 1
            last_day_month3 = monthrange(year_plus3, month_plus3)[1]
            fourth_payment_date = date(year_plus3, month_plus3, last_day_month3)
            
            fallback = [
                (_("Paiement initial"), total * 0.50, "50%", first_payment_date),
                (_("Deuxième paiement"), total * 0.20, "20%", second_payment_date),
                (_("Troisième paiement"), total * 0.15, "15%", third_payment_date),
                (_("Quatrième paiement"), total * 0.15, "15%", fourth_payment_date),
            ]
        else:
            # Pour les autres types de crédit, dates normales
            fallback = [
                (_("Paiement initial"), total * 0.50, "50%", today + timedelta(days=3)),
                (_("Deuxième paiement"), total * 0.20, "20%", today + timedelta(days=30)),
                (_("Troisième paiement"), total * 0.15, "15%", today + timedelta(days=60)),
                (_("Quatrième paiement"), total * 0.15, "15%", today + timedelta(days=90)),
            ]
        return fallback

    def _payment_table_html(self):
        """Table HTML pour les paiements avec fallback."""
        rows = []
        for label, amount, rate, due in self._payment_rows_from_plan():
            due_str = due.strftime('%d/%m/%Y') if isinstance(due, (date, datetime)) and due else '—'
            rows.append(f"""
            <tr>
              <td style="padding:8px;border:1px solid #ddd;">{label}</td>
              <td style="padding:8px;border:1px solid #ddd;text-align:right;">{self._fmt_money(amount)}</td>
              <td style="padding:8px;border:1px solid #ddd;text-align:center;">{rate}</td>
              <td style="padding:8px;border:1px solid #ddd;text-align:center;">{due_str}</td>
            </tr>
            """)

        return f"""
        <h3 style="color:#333;border-bottom:2px solid #875A7B;padding-bottom:5px;margin-top:16px;">{_('Informations de paiement')}</h3>
        <p>{_('Le paiement initial (acompte) après validation RH et validation CCBM déclenchera la mise en exécution de la commande.')}</p>
        <table border="1" cellpadding="5" cellspacing="0" width="100%" style="border-collapse:collapse;margin-top:10px;">
          <thead>
            <tr style="background:#f8f9fa;">
              <th style="padding:10px;border:1px solid #ddd;text-align:left;">{_('Échéance')}</th>
              <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_('Montant')}</th>
              <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_('Pourcentage')}</th>
              <th style="padding:10px;border:1px solid #ddd;text-align:center;">{_("Date d'échéance")}</th>
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
        """

    def _email_header_block(self, title):
        """Bloc header d'email standardisé."""
        return f"""
        <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
          <tr>
            <td valign="middle">
              <span style="font-size:10px;">{title}</span><br/>
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
        """

    def _email_footer_block(self):
        """Bloc footer d'email standardisé."""
        return f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
               style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
          <tr>
            <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
              <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
              <div>🛍️ <a href="{SITE_URL}" target="_blank" rel="noopener" style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
            </td>
          </tr>
        </table>
        """

    def _wrap_email(self, inner_html, title):
        """Wrapper pour email avec header et footer."""
        return f"""
        <table border="0" cellpadding="0" cellspacing="0"
               style="padding-top:16px;background:#FFFFFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
          <tr><td align="center">
            <table border="0" cellpadding="0" cellspacing="0" width="590"
                   style="padding:16px;background:#FFFFFF;color:#454748;border-collapse:separate;">
              <tbody>
                <tr><td align="center" style="min-width:590px;">{self._email_header_block(title)}</td></tr>
                <tr>
                  <td align="center" style="min-width:590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590"
                           style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
                      <tr><td>{inner_html}</td></tr>
                    </table>
                  </td>
                </tr>
              </tbody>
            </table>
            {self._email_footer_block()}
          </td></tr>
        </table>
        """

    def _email_body_for(self, partner, email_type):
        """Génère le corps d'email selon le type et le type de crédit."""
        pname = self._partner_display_name(partner)
        mm_rate = getattr(self, 'credit_month_rate', 0)
        credit_type_label = self._get_credit_type_label()
        is_bank = self._is_bank_credit()
        is_direct = self._is_direct_credit()
        total_amount = self._fmt_money(self.amount_total)
        
        # Messages personnalisés selon le type de crédit
        if is_bank:
            validation_entity = _('votre institution bancaire')
            rejection_entity = _('votre institution bancaire')
            validation_wait = _('En attente de la validation finale de votre institution bancaire et de CCBM Shop.')
        elif is_direct:
            validation_entity = _('votre service RH')
            rejection_entity = _('votre service RH')
            validation_wait = _('En attente de la validation finale de CCBM Shop.')
        else:
            validation_entity = _('votre service RH')
            rejection_entity = _('votre service RH')
            validation_wait = _('En attente de la validation finale de CCBM Shop.')
        
        # Pour tous les mails au client, on ajoute le montant total
        amount_info = f"<p><strong>{_('Montant total de la commande')} : {total_amount}</strong></p>"

        content_map = {
            'validation': f"""
                <p>{_('Félicitations')} {pname},</p>
                <p>{_('Votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été créée avec succès')}.</p>
                {amount_info}
                <p>{_('Détails des échéances')} :</p>
                {self._payment_table_html()}
            """,
            'rejection': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Nous regrettons de vous informer que votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été rejetée')}.</p>
                {amount_info}
                <p>{_('Pour toute question, contactez notre service client.')}</p>
            """,
            'rh_rejection': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été rejetée par')} {rejection_entity}.</p>
                {amount_info}
            """,
            'admin_rejection': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été rejetée par notre administration')}.</p>
                {amount_info}
            """,
            'admin_validation': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Nous vous informons que votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été validée par notre administration')}.</p>
                {amount_info}
                <p>{_('Veuillez vous connecter à la plateforme pour effectuer le paiement de')} <strong>{mm_rate}%</strong> {_('(acompte) du montant de la commande.')}</p>
            """,
            'rh_validation': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été validée par')} {validation_entity}.</p>
                {amount_info}
                <p>{validation_wait}</p>
            """,
            'request': f"""
                <p>{_('Bonjour')} {pname},</p>
                <p>{_('Nous avons bien reçu votre demande de commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong>.</p>
                {amount_info}
                <p>{_('Elle est actuellement en cours de validation par nos services.')}</p>
            """,
            'creation': f"""
                <p>{_('Bonjour')} {pname},</p>
                <p>{_('Votre commande à crédit')} <strong>({credit_type_label})</strong> {_('numéro')} <strong>{self.name}</strong> {_('a été créée avec succès')}.</p>
                {amount_info}
                <p>{_('Elle est en attente de validation par')} {validation_entity}.</p>
            """,
            'hr_notification': self._get_hr_notification_content(is_bank, credit_type_label),
        }
        title_map = {
            'validation': _('Validation de votre commande à crédit'),
            'rejection': _('Rejet de votre commande à crédit'),
            'rh_rejection': _('Rejet de votre commande à crédit par le service RH'),
            'admin_rejection': _("Rejet de votre commande à crédit par l'administration"),
            'admin_validation': _("Validation administrative de votre commande à crédit"),
            'rh_validation': _("Validation RH de votre commande à crédit"),
            'request': _("Votre demande de commande à crédit"),
            'creation': _("Votre commande à crédit a été créée"),
            'hr_notification': _("Nouvelle commande à valider"),
        }
        return self._wrap_email(content_map[email_type], title_map[email_type])

    def _get_hr_notification_content(self, is_bank, credit_type_label):
        """Génère le contenu de notification RH selon le type de crédit."""
        if is_bank:
            return f"""
                <p>{_('Bonjour')},</p>
                <p>{_('Une nouvelle commande à crédit bancaire/financier nécessite votre validation en tant qu\'entité bancaire')} :</p>
                <ul>
                    <li>{_('Numéro')} : {self.name}</li>
                    <li>{_('Type de crédit')} : {credit_type_label}</li>
                    <li>{_('Client')} : {self._partner_display_name(self.partner_id)}</li>
                    <li>{_('Montant total')} : {self._fmt_money(self.amount_total)}</li>
                    <li>{_('Date de création')} : {self.create_date.strftime('%d/%m/%Y %H:%M') if self.create_date else '—'}</li>
                </ul>
                <p>{_('Veuillez examiner cette demande de crédit bancaire/financier et prendre les mesures appropriées dans votre interface d\'administration.')}</p>
            """
        else:
            return f"""
                <p>{_('Bonjour')},</p>
                <p>{_('Une nouvelle commande à crédit nécessite votre validation')} :</p>
                <ul>
                    <li>{_('Numéro')} : {self.name}</li>
                    <li>{_('Type de crédit')} : {credit_type_label}</li>
                    <li>{_('Client')} : {self._partner_display_name(self.partner_id)}</li>
                    <li>{_('Montant total')} : {self._fmt_money(self.amount_total)}</li>
                    <li>{_('Date de création')} : {self.create_date.strftime('%d/%m/%Y %H:%M') if self.create_date else '—'}</li>
                </ul>
                <p>{_('Veuillez examiner cette demande et prendre les mesures appropriées dans votre interface d\'administration.')}</p>
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
        """Envoie un mail de mise à jour au client avec SMS optionnel."""
        partner = self.partner_id
        if not partner:
            _logger.warning("Aucun partenaire — email non envoyé.")
            return
        
        body_html = self._render_update_mail(reasons)
        return self._send_mail_common(
            partner=partner,
            subject=_("Mise à jour de votre commande à crédit %s") % (self.name,),
            body_html=body_html,
            sms_type='update',  # SMS pour mise à jour de commande
            extra_recipients=['shop@ccbm.sn'],
        )

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
        Utilise la nouvelle méthode _send_type pour cohérence.
        """
        return self._send_type('validation', include_create_account=True)


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
            return self._send_mail_common(
                partner=partner,
                subject=_("Mise à jour de l'état de votre commande à crédit"),
                body_html=body_html,
                sms_type='payment_status',  # SMS pour mise à jour de statut de paiement
                extra_recipients=['shop@ccbm.sn'],
            )

        except Exception as e:
            _logger.error("Erreur mail statut %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    # ---------------------------------------------------------------------
    # ==================  API ENVELOPPES PUBLIQUES  =======================
    # ---------------------------------------------------------------------
    def _send_type(self, email_type, to_partner=None, sms_type=None, include_create_account=False, extra_recipients=None):
        """Méthode générique pour envoyer différents types d'emails."""
        self.ensure_one()
        partner = to_partner or self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}

        body_html = self._email_body_for(partner, email_type)
        if include_create_account:
            # Ajoute la section "Créer un compte" à la fin du bloc principal
            body_html = body_html.replace(
                "</tbody></table>",  # ancre interne de _wrap_email (suffisant ici)
                "</tbody></table>" + self._create_account_section_if_needed(partner)
            )

        # Personnalisation du sujet selon le type de crédit
        credit_type_label = self._get_credit_type_label()
        is_bank = self._is_bank_credit()
        
        if is_bank:
            hr_notification_subject = _("Nouvelle commande à crédit bancaire/financier à valider")
        else:
            hr_notification_subject = _("Nouvelle commande à valider")
        
        subject_map = {
            'validation': _('Validation de votre commande à crédit'),
            'rejection':  _('Rejet de votre commande à crédit'),
            'rh_rejection': _('Rejet de votre commande à crédit par le service RH'),
            'admin_rejection': _("Rejet de votre commande à crédit par l'administration"),
            'admin_validation': _("Validation administrative de votre commande à crédit"),
            'rh_validation': _("Validation RH de votre commande à crédit"),
            'request': _("Demande de commande à crédit en cours"),
            'creation': _("Votre commande à crédit a été créée"),
            'hr_notification': hr_notification_subject,
        }
        subject = subject_map[email_type]
        return self._send_mail_common(
            partner=partner,
            subject=subject,
            body_html=body_html,
            sms_type=sms_type or email_type,
            extra_recipients=extra_recipients or ['shop@ccbm.sn'],
        )

    # ---- Enveloppes simples RH/Admin vers client ----
    def send_credit_order_rh_rejected(self):
        return self._send_type('rh_rejection')

    def send_credit_order_rh_validation(self):
        return self._send_type('rh_validation')

    def send_credit_order_admin_validation(self):
        return self._send_type('admin_validation')

    def send_credit_order_admin_rejected(self):
        return self._send_type('admin_rejection')

    def send_credit_order_rejection_mail(self):
        """Mail de rejet général."""
        return self._send_type('rejection')

    def send_credit_order_request_mail(self):
        """Mail de demande en cours."""
        return self._send_type('request', include_create_account=True)

    def send_credit_order_creation_notification_to_client(self):
        """Notification de création au client."""
        return self._send_type('creation', include_create_account=True)

    def _snapshot_states(self):
        """Capture l'état actuel des validations."""
        return {
            'rh': self.validation_rh_state,
            'admin': self.validation_admin_state,
        }

    def _handle_state_transitions(self, before_states):
        """
        Compare l'état avant/après et envoie les notifications adaptées.
        """
        after_states = self._snapshot_states()
        # RH
        if before_states.get('rh') != after_states.get('rh'):
            if after_states['rh'] == 'validated':
                self.send_credit_order_rh_validation()
                self.send_credit_order_to_admin_for_validation()
            elif after_states['rh'] == 'rejected':
                self.send_credit_order_rh_rejected()
        # Admin
        if before_states.get('admin') != after_states.get('admin'):
            if after_states['admin'] == 'validated':
                self.send_credit_order_admin_validation()
            elif after_states['admin'] == 'rejected':
                self.send_credit_order_admin_rejected()

    # ---------------------------------------------------------------------
    # ======================  NOTIFS RH / ADMIN  ===========================
    # ---------------------------------------------------------------------
    def send_credit_order_to_admin_for_validation(self):
        """
        Après validation RH: prévenir un admin système par mail.
        """
        try:
            admin_group = self.env.ref('base.group_system')
            admin_user = self.env['res.users'].sudo().search([('groups_id', 'in', admin_group.id)], limit=1)
            if not admin_user:
                _logger.error('No admin user found to send the confirmation email')
                return {'status': 'error', 'message': 'No admin user found'}
            return self._send_type('hr_notification', to_partner=admin_user.partner_id, sms_type=None)
        except Exception as e:
            _logger.error("Erreur notif admin %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def send_credit_order_creation_notification_to_hr(self):
        """
        À la création d'une demande de crédit: prévenir la RH selon le type de crédit.
        - Crédit direct : notification RH normale (employeur)
        - Crédit banque/finance : notification RH en tant qu'entité bancaire
        """
        try:
            self.ensure_one()
            credit_type = getattr(self, 'credit_type', '') or ''
            
            # Pour crédit direct, banque ou finance, on notifie la RH
            if credit_type in ('direct', 'banque', 'finance'):
                company = getattr(self.partner_id, 'employer_partner_id', False) or self.partner_id.parent_id
                if not company:
                    return {'status': 'error', 'message': 'No company (employer/parent) found'}
                rh_user = self.env['res.partner'].sudo().search([
                    ('role', '=', 'main_user'),
                    ('parent_id', '=', company.id),
                ], limit=1)
                if not rh_user:
                    return {'status': 'error', 'message': 'HR user not found'}
                return self._send_type('hr_notification', to_partner=rh_user, sms_type='hr_notification')
            else:
                # Pour particulier, pas de notification RH
                _logger.info("Type de crédit '%s' ne nécessite pas de notification RH", credit_type)
                return {'status': 'success', 'message': 'No HR notification needed for this credit type'}
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
        """Génère l'email de notification RH avec personnalisation selon le type de crédit."""
        is_bank = self._is_bank_credit()
        credit_type_label = self._get_credit_type_label()
        
        if is_bank:
            intro_text = _('Une nouvelle demande de commande à crédit bancaire/financier a été créée et nécessite votre validation en tant qu\'entité bancaire')
            outro_text = _('Veuillez examiner cette demande de crédit bancaire/financier et prendre les mesures appropriées dans votre interface d\'administration.')
        else:
            intro_text = _('Une nouvelle demande de commande à crédit a été créée et nécessite votre validation')
            outro_text = _('Veuillez examiner cette demande et prendre les mesures appropriées dans votre interface d\'administration.')
        
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
                                    <p>{intro_text} :</p>
                                    <ul>
                                        <li>{_('Numéro de commande')} : {self.name}</li>
                                        <li>{_('Type de crédit')} : {credit_type_label}</li>
                                        <li>{_('Client')} : {self._partner_display_name(self.partner_id)}</li>
                                        <li>{_('Montant total')} : {self.amount_total:,.0f} {self.currency_id.name}</li>
                                        <li>{_('Date de création')} : {self.create_date.strftime('%d/%m/%Y %H:%M') if self.create_date else '—'}</li>
                                    </ul>
                                    <p>{outro_text}<br/>{_('Cordialement')},<br/>{_('Système automatique CCBM Shop')}</p>
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
    def _send_mail_common(self, mail_server=None, partner=None, subject=None, body_html=None, sms_type=None, extra_recipients=None):
        """
        Envoi mail via mail.mail + SMS optionnel via module 'send.sms' (si dispo).
        Supporte deux signatures : (mail_server, partner, ...) ou (partner, subject, ...)
        """
        try:
            # Support de deux signatures différentes
            if mail_server is None and partner is not None and subject is not None:
                # Nouvelle signature: (partner, subject, body_html, sms_type, extra_recipients)
                mail_server = self._mail_server_or_raise()
                if not partner or not self._has_partner_email(partner):
                    _logger.warning("Destinataire invalide: partner/email manquant — envoi annulé.")
                    return {'status': 'error', 'message': 'Partner email not found'}
                email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
                recipients = [self._partner_email(partner)]
                if extra_recipients:
                    recipients.extend([r for r in extra_recipients if r])
                email_to = ', '.join(recipients)
            else:
                # Ancienne signature: (mail_server, partner, subject, body_html, sms_type)
                if not mail_server:
                    mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                    if not mail_server:
                        return {'status': 'error', 'message': 'Mail server not configured'}
                email_from = mail_server.smtp_user or 'shop@ccbm.sn'
                recipients = [self._partner_email(partner), 'shop@ccbm.sn']
                email_to = ', '.join(filter(None, recipients))

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
                        sms_body = self._sms_message(sms_type)
                        sms_rec = Sms.create({'recipient': phone, 'message': sms_body})
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
        """
        Génère les messages SMS pour les notifications, personnalisés selon le type de crédit.
        Messages formatés en UTF-8 pour éviter les erreurs 400 de l'API SMS.
        """
        try:
            partner_name = self._partner_display_name(self.partner_id) or ""
            # Nettoyer le nom du partenaire pour éviter les caractères problématiques
            partner_name = partner_name.strip()[:50]  # Limiter la longueur
            
            is_bank = self._is_bank_credit()
            
            # Messages personnalisés selon le type de crédit (avec accents, format UTF-8)
            if is_bank:
                validation_entity = "votre institution bancaire"
                rejection_entity = "votre institution bancaire"
            else:
                validation_entity = "votre service RH"
                rejection_entity = "votre service RH"
            
            # Messages avec accents, formatés en UTF-8
            m = {
                'validation': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été créée avec succès.",
                'rejection': f"Bonjour {partner_name}, nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.",
                'rh_rejection': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été rejetée par {rejection_entity}.",
                'admin_rejection': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été rejetée par notre administration.",
                'admin_validation': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été validée par notre administration.",
                'rh_validation': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été validée par {validation_entity}.",
                'request': f"Bonjour {partner_name}, nous avons bien reçu votre demande de commande à crédit numéro {self.name}. Elle est en cours de validation.",
                'creation': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été créée avec succès. Elle est en attente de validation par {validation_entity}.",
                'hr_notification': f"Bonjour, une nouvelle demande de validation de commande à crédit numéro {self.name} nécessite votre validation.",
                'payment_status': f"Bonjour {partner_name}, mise à jour de l'état de paiement de votre commande à crédit numéro {self.name}. Connectez-vous pour voir les détails.",
                'update': f"Bonjour {partner_name}, votre commande à crédit numéro {self.name} a été mise à jour. Connectez-vous pour voir les modifications.",
            }
            
            message = m.get(kind, f"Notification commande {self.name}")
            
            # S'assurer que le message est bien une chaîne UTF-8 valide
            if not isinstance(message, str):
                message = str(message)
            
            # Nettoyer les caractères de contrôle et normaliser
            # Normaliser en NFC (Canonical Composition) pour éviter les problèmes d'encodage
            message = unicodedata.normalize('NFC', message)
            
            # Supprimer les caractères de contrôle (sauf \n)
            message = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', message)
            
            # Limiter la longueur du message (SMS standard = 160 caractères, mais on peut aller jusqu'à 1600 pour SMS concaténés)
            if len(message) > 500:
                message = message[:497] + "..."
            
            # S'assurer que le message peut être encodé en UTF-8
            try:
                message.encode('utf-8')
            except UnicodeEncodeError:
                # En cas d'erreur, utiliser une version ASCII simplifiée
                _logger.warning("Caractères non-UTF-8 détectés dans le message SMS, conversion en ASCII")
                message = message.encode('ascii', 'ignore').decode('ascii')
            
            return message
            
        except Exception as e:
            _logger.error("Erreur lors de la génération du message SMS (%s) pour %s: %s", kind, self.name, e, exc_info=True)
            # Message de fallback simple
            return f"Notification commande {self.name}"

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
