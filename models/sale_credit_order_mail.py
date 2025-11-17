
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)

# Branding (uniformiser avec le 1er fichier)
SITE_URL = "https://ccbmshop.sn"
LOGO_URL = "https://ccbmshop.sn/logo.png"


class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    # ------------------------------------------------------------------
    # =====================  HELPERS COMMUNS  ===========================
    # ------------------------------------------------------------------
    def _mail_server_or_raise(self):
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        if not mail_server:
            raise UserError(_("Veuillez configurer un serveur de messagerie."))
        return mail_server

    # ---- Partner helpers (alignés avec tes champs custom) ----
    def _partner_display_name(self, p):
        """Privilégie 'prenom nom' (custom), sinon name."""
        if not p:
            return ""
        prenom = (getattr(p, 'prenom', '') or '').strip()
        nom = (getattr(p, 'nom', '') or '').strip()
        if prenom or nom:
            return (prenom + " " + nom).strip()
        return (p.name or '').strip()

    def _has_partner_email(self, partner):
        return bool((getattr(partner, 'email', '') or '').strip())

    def _partner_email(self, partner):
        return (getattr(partner, 'email', '') or '').strip()

    def _partner_phone(self, partner):
        """
        Priorité à ton champ custom 'telephone', puis phone, puis mobile.
        """
        for attr in ('telephone', 'phone', 'mobile'):
            v = getattr(partner, attr, False)
            if v:
                return v
        return ""

    def _fmt_money(self, amount):
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

    # ------------------------------------------------------------------
    # ==================  EMAIL HEADER/FOOTER  ==========================
    # ------------------------------------------------------------------
    def _email_header_block(self, title):
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

    # ------------------------------------------------------------------
    # ==================  ÉCHÉANCIER / TABLES  ==========================
    # ------------------------------------------------------------------
    def _coerce_date(self, v):
        if not v:
            return None
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        try:
            return datetime.fromisoformat(str(v)).date()
        except Exception:
            return None

    def _payment_rows_from_plan(self):
        """
        Utilise sale.order.credit.payment si dispo; sinon fallback 50/20/15/15.
        """
        rows = []
        plan = self.mapped('credit_payment_ids')
        if plan:
            for l in plan.sorted(lambda r: r.sequence):
                label = _("Premier Paiement (Acompte)") if l.sequence == 1 else _("Échéance %(n)s", n=l.sequence)
                due = self._coerce_date(l.due_date)
                rows.append((label, float(l.amount or 0.0), f"{l.rate}", due))
            return rows

        # Fallback
        today = datetime.now().date()
        total = float(self.amount_total or 0.0)
        fallback = [
            (_("Paiement initial"), total * 0.50, "50%", today + timedelta(days=3)),
            (_("Deuxième paiement"), total * 0.20, "20%", today + timedelta(days=30)),
            (_("Troisième paiement"), total * 0.15, "15%", today + timedelta(days=60)),
            (_("Quatrième paiement"), total * 0.15, "15%", today + timedelta(days=90)),
        ]
        return fallback

    def _payment_table_html(self):
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

    # ------------------------------------------------------------------
    # ==================  CORPS EMAILS / TYPES  ==========================
    # ------------------------------------------------------------------
    def _email_body_for(self, partner, email_type):
        pname = self._partner_display_name(partner)
        mm_rate = getattr(self, 'credit_month_rate', 0)
        content_map = {
            'validation': f"""
                <p>{_('Félicitations')} {pname},</p>
                <p>{_('Votre commande à crédit numéro')} <strong>{self.name}</strong> {_('a été créée avec succès')}.</p>
                <p>{_('Détails des échéances')} :</p>
                {self._payment_table_html()}
            """,
            'rejection': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Nous regrettons de vous informer que votre commande à crédit numéro')} <strong>{self.name}</strong> {_('a été rejetée')}.</p>
                <p>{_('Pour toute question, contactez notre service client.')}</p>
            """,
            'rh_rejection': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Votre commande à crédit numéro')} <strong>{self.name}</strong> {_('a été rejetée par votre service RH')}.</p>
            """,
            'admin_rejection': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Votre commande à crédit numéro')} <strong>{self.name}</strong> {_('a été rejetée par notre administration')}.</p>
            """,
            'admin_validation': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Nous vous informons que votre commande à crédit numéro')} <strong>{self.name}</strong> {_('a été validée par notre administration')}.</p>
                <p>{_('Veuillez vous connecter à la plateforme pour effectuer le paiement de')} <strong>{mm_rate}%</strong> {_('(acompte) du montant de la commande.')}</p>
            """,
            'rh_validation': f"""
                <p>{_('Cher(e)')} {pname},</p>
                <p>{_('Votre commande à crédit numéro')} <strong>{self.name}</strong> {_('a été validée par votre service RH')}.</p>
                <p>{_('En attente de la validation finale de CCBM Shop.')}</p>
            """,
            'request': f"""
                <p>{_('Bonjour')} {pname},</p>
                <p>{_('Nous avons bien reçu votre demande de commande à crédit')} <strong>{self.name}</strong>.</p>
                <p>{_('Elle est actuellement en cours de validation par nos services.')}</p>
            """,
            'creation': f"""
                <p>{_('Bonjour')} {pname},</p>
                <p>{_('Votre commande à crédit')} <strong>{self.name}</strong> {_('a été créée avec succès')}.</p>
                <p>{_('Elle est en attente de validation par votre service des Ressources Humaines.')}</p>
            """,
            'hr_notification': f"""
                <p>{_('Bonjour')},</p>
                <p>{_('Une nouvelle commande à crédit nécessite votre validation')} :</p>
                <ul>
                    <li>{_('Numéro')} : {self.name}</li>
                    <li>{_('Client')} : {self._partner_display_name(self.partner_id)}</li>
                    <li>{_('Montant total')} : {self._fmt_money(self.amount_total)}</li>
                </ul>
            """,
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

    # ------------------------------------------------------------------
    # ==================  ENVOI EMAIL + SMS =============================
    # ------------------------------------------------------------------
    def _sms_message(self, kind):
        partner_name = self._partner_display_name(self.partner_id)
        m = {
            'validation': _("Bonjour %(name)s, votre commande à crédit %(order)s a été créée.", name=partner_name, order=self.name),
            'rejection':  _("Bonjour %(name)s, votre commande à crédit %(order)s a été rejetée.", name=partner_name, order=self.name),
            'rh_rejection': _("Bonjour %(name)s, votre commande %(order)s a été rejetée par le service RH.", name=partner_name, order=self.name),
            'admin_rejection': _("Bonjour %(name)s, votre commande %(order)s a été rejetée par l'administration.", name=partner_name, order=self.name),
            'admin_validation': _("Bonjour %(name)s, votre commande %(order)s a été validée par l'administration.", name=partner_name, order=self.name),
            'rh_validation': _("Bonjour %(name)s, votre commande %(order)s a été validée par le service RH.", name=partner_name, order=self.name),
            'request': _("Bonjour %(name)s, votre demande de commande à crédit %(order)s est en cours.", name=partner_name, order=self.name),
            'creation': _("Bonjour %(name)s, votre commande à crédit %(order)s a été créée (en attente de validation RH).", name=partner_name, order=self.name),
            'hr_notification': _("Bonjour, la commande %(order)s nécessite une validation RH.", order=self.name),
        }
        return m.get(kind, _("Notification commande %(order)s", order=self.name))

    def _send_mail_common(self, partner, subject, body_html, sms_type=None, extra_recipients=None):
        """
        Envoi d'email standardisé + SMS optionnel.
        """
        try:
            mail_server = self._mail_server_or_raise()

            if not partner or not self._has_partner_email(partner):
                _logger.warning("Destinataire invalide: partner/email manquant — envoi annulé.")
                return {'status': 'error', 'message': 'Partner email not found'}

            email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
            recipients = [self._partner_email(partner)]
            if extra_recipients:
                recipients.extend([r for r in extra_recipients if r])

            email_values = {
                'email_from': email_from,
                'email_to': ', '.join(recipients),
                'subject': subject,
                'body_html': body_html,
                'state': 'outgoing',
                'auto_delete': False,
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            _logger.info("Mail '%s' envoyé à %s pour %s", subject, email_values['email_to'], self.name)

            # SMS si demandé et si un numéro exploitable existe
            if sms_type:
                phone = self._partner_phone(partner)
                if phone:
                    Sms = self.env.get('send.sms')
                    if Sms:
                        sms_body = self._sms_message(sms_type)
                        rec = Sms.create({'recipient': phone, 'message': sms_body})
                        try:
                            rec.send_sms()
                            _logger.info("SMS '%s' envoyé à %s pour %s", sms_type, phone, self.name)
                        except Exception as se:
                            _logger.error("Échec envoi SMS (%s) à %s: %s", sms_type, phone, se, exc_info=True)
                    else:
                        _logger.warning("Module send.sms indisponible — SMS non envoyé")
            return {'status': 'success'}
        except Exception as e:
            _logger.error("Erreur envoi mail %s: %s", self.name, e, exc_info=True)
            return {'status': 'error', 'message': str(e)}

    # ------------------------------------------------------------------
    # ==================  API ENVELOPPES PUBLIQUES  =====================
    # ------------------------------------------------------------------
    def _send_type(self, email_type, to_partner=None, sms_type=None, include_create_account=False, extra_recipients=None):
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

        subject_map = {
            'validation': _('Validation de votre commande à crédit'),
            'rejection':  _('Rejet de votre commande à crédit'),
            'rh_rejection': _('Rejet de votre commande à crédit par le service RH'),
            'admin_rejection': _("Rejet de votre commande à crédit par l'administration"),
            'admin_validation': _("Validation administrative de votre commande à crédit"),
            'rh_validation': _("Validation RH de votre commande à crédit"),
            'request': _("Demande de commande à crédit en cours"),
            'creation': _("Votre commande à crédit a été créée"),
            'hr_notification': _("Nouvelle commande à valider"),
        }
        subject = subject_map[email_type]
        return self._send_mail_common(
            partner=partner,
            subject=subject,
            body_html=body_html,
            sms_type=sms_type or email_type,
            extra_recipients=extra_recipients or ['shop@ccbm.sn'],
        )

    # ---- Expositions 1:1 (compat) ----
    def send_credit_order_validation_mail(self):
        return self._send_type('validation', include_create_account=True)

    def send_credit_order_rejection_mail(self):
        return self._send_type('rejection')

    def send_credit_order_rh_rejected(self):
        return self._send_type('rh_rejection')

    def send_credit_order_admin_rejected(self):
        return self._send_type('admin_rejection')

    def send_credit_order_admin_validation(self):
        return self._send_type('admin_validation')

    def send_credit_order_rh_validation(self):
        return self._send_type('rh_validation')

    def send_credit_order_request_mail(self):
        return self._send_type('request', include_create_account=True)

    def send_credit_order_creation_notification_to_client(self):
        return self._send_type('creation', include_create_account=True)

    def send_credit_order_creation_notification_to_hr(self):
        """
        RH = partenaire enfant de la société (parent du client) avec role='main_user'.
        """
        self.ensure_one()
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

    def send_credit_order_to_admin_for_validation(self):
        """
        Notifie un administrateur (group_system). Sujet/texte = hr_notification (clair et court).
        """
        admin_group = self.env.ref('base.group_system')
        admin_user = self.env['res.users'].sudo().search([('groups_id', 'in', admin_group.id)], limit=1)
        if not admin_user:
            _logger.error('No admin user found to send the confirmation email')
            return {'status': 'error', 'message': 'No admin user found'}
        return self._send_type('hr_notification', to_partner=admin_user.partner_id, sms_type=None)

    # ------------------------------------------------------------------
    # ==================  DETECTEUR D’ÉTATS / WRITE  ====================
    # ------------------------------------------------------------------
    def _snapshot_states(self):
        return {
            'rh': self.validation_rh_state,
            'admin': self.validation_admin_state,
        }

    def _handle_state_transitions(self, before_states):
        """
        Compare l’état avant/après et envoie les notifications adaptées.
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

    def write(self, vals):
        """
        Redéfinition write :
        - on prend un snapshot des états,
        - on écrit,
        - on notifie si transitions (plus fiable que d’appeler avant).
        """
        befores = {rec.id: rec._snapshot_states() for rec in self}
        res = super().write(vals)
        for rec in self:
            try:
                if getattr(rec, 'type_sale', '') == 'creditorder':
                    rec._handle_state_transitions(befores.get(rec.id, {}))
            except Exception as e:
                _logger.error("Erreur post-write (notifications) sur %s: %s", rec.name, e, exc_info=True)
        return res
