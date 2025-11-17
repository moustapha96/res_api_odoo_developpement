# from odoo import models, fields, api
# from datetime import datetime
# import logging

# _logger = logging.getLogger(__name__)


# class SaleCreditOrderMail(models.Model):
#     _inherit = 'sale.order'

#     def send_payment_reminder(self):
#         """
#         Parcourt les paiements échus et envoie les notifications (e-mail + SMS).
#         """
#         today = datetime.now().date()
#         overdue_payments = self._get_overdue_payments(today)

#         for payment in overdue_payments:
#             self._notify_overdue_payment(payment)

#     def _get_overdue_payments(self, today):
#         """
#         Récupère les lignes de paiements échus pour la commande.
#         :param today: date actuelle
#         :return: liste des paiements échus sous forme de dictionnaires
#         """
#         overdue = []
#         payments = self._generate_payments(today)

#         for payment in payments:
#             label, amount, state, rate, due_date = payment
#             if not state and due_date < today and amount > 0:
#                 _logger.info(f"[ÉCHU] {label} | Montant: {amount} | Date: {due_date}")
#                 overdue.append({
#                     'label': label,
#                     'amount': amount,
#                     'due_date': due_date,
#                 })
#         return overdue

#     def _notify_overdue_payment(self, payment):
#         """
#         Envoie une notification (e-mail + SMS) pour un paiement échu donné.
#         """
#         partner = self.partner_id
#         if not partner:
#             _logger.warning(f"[ERREUR] Aucun partenaire trouvé pour la commande {self.name}")
#             return

#         subject = f'🔔 Rappel : Paiement en retard - {payment["label"]}'
      
#         body_html = f"""
#             <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f4; padding: 20px;">
#              <tr>
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
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbmshop.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                 <tr>
#                     <td align="center">
#                         <table border="0" cellpadding="0" cellspacing="0" width="600" style="background-color: #ffffff; padding: 30px; border-radius: 6px;">
#                             <tr>
#                                 <td align="center" style="font-size: 22px; font-weight: bold; padding-bottom: 20px; color: #dc3545;">
#                                     ⚠️ Rappel de paiement échu
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 16px; color: #333333; padding-bottom: 10px;">
#                                     Bonjour {partner.name},
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 15px;">
#                                     Nous vous informons que le paiement de <strong>{payment['amount']} {self.currency_id.name}</strong>,
#                                     prévu le <strong>{payment['due_date']}</strong>, est <span style="color: red; font-weight: bold;">en retard</span>.
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 20px;">
#                                     Voici les détails de la commande concernée :
#                                     <ul style="margin-top: 10px; margin-bottom: 10px; padding-left: 20px; color: #444;">
#                                         <li><strong>Référence :</strong> {self.name}</li>
#                                         <li><strong>Date de commande :</strong> {self.date_order.strftime('%d/%m/%Y')}</li>
#                                         <li><strong>Montant total :</strong> {self.amount_total:,.0f} {self.currency_id.name}</li>
#                                     </ul>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td style="font-size: 15px; color: #333333; line-height: 1.6; padding-bottom: 15px;">
#                                     Merci de bien vouloir régulariser votre situation dans les plus brefs délais afin d’éviter toute interruption ou pénalité éventuelle.
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="padding-bottom: 30px;">
#                                     <a href="https://www.ccbmshop.sn/login" style="display: inline-block; background-color: #007bff; color: #ffffff; text-decoration: none; padding: 12px 25px; font-size: 15px; border-radius: 5px;">
#                                         Connectez vous maintenant
#                                     </a>
#                                 </td>
#                             </tr>
                           
#                         </table>
#                     </td>
#                 </tr>

#                 <!-- Footer CCBM -->
#                  <tr style="background-color: #F1F1F1; font-size: 13px; color: #555555;">
#                             <td colspan="2" style="padding: 12px; text-align: center;">
#                                 <p>📞 +221 33 849 65 49 / +221 70 922 17 75 | 📍 Ouest foire, après la fédération</p>
#                                 <p> <a href="https://ccbmshop.sn" style="color: #875A7B;">www.ccbmshop.sn</a></p>
#                             </td>
#                         </tr>
#             </table>
#             """


#         mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
#         self.send_mail(mail_server, partner, subject, body_html)

#         if partner.phone:
#             sms_msg = (
#                 f"Bonjour {partner.name}, votre paiement de {payment['amount']} {self.currency_id.name} "
#                 f"(commande {self.name}, échéance {payment['due_date']}) est en retard. "
#                 f"Merci de régulariser au plus vite.\n{self.company_id.name}"
#             )

#             self.env['send.sms'].create({
#                 'recipient': partner.phone,
#                 'message': sms_msg,
#             }).send_sms()
#         else:
#             _logger.warning(f"[SMS NON ENVOYÉ] Numéro manquant pour {partner.name}")

#     def _generate_payments(self, today):
#         """
#         Génère une liste des échéances de paiement à partir de la méthode `get_sale_order_credit_payment`.
#         :param today: date du jour
#         :return: liste de tuples (label, montant, état, taux, date d'échéance)
#         """
#         payments = []
#         payment_lines = self.get_sale_order_credit_payment()

#         for line in sorted(payment_lines, key=lambda x: x['sequence']):
#             due_date = line['due_date']
#             if isinstance(due_date, str):
#                 due_date = datetime.fromisoformat(due_date).date()

#             label = "Premier Paiement (Acompte)" if line['sequence'] == 1 else f"Échéance {line['sequence']}"
#             payments.append((
#                 label,
#                 line['amount'],
#                 line['state'],
#                 f"{line['rate']:.1f}%",
#                 due_date
#             ))

#         return payments


#     def send_mail(self, mail_server, partner, subject, body_html):
        
#         if not mail_server:
#             _logger.error('Mail server not configured')
#             return {'status': 'error', 'message': 'Mail server not configured'}

#         email_from = mail_server.smtp_user
#         additional_email = 'shop@ccbm.sn'
#         email_to = None

#         if hasattr(partner, 'email') and partner.email:
#             email_to = f'{partner.email}, {additional_email}'
#         else:
#             _logger.error(f'Partner email not found for partner: {partner.name}')
#             return {'status': 'error', 'message': 'Partner email not found'}

#         email_values = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'subject': subject,
#             'body_html': body_html,
#             'state': 'outgoing',
#         }
#         # return True
#         mail_mail = self.env['mail.mail'].sudo().create(email_values)
#         try:
#             mail_mail.send()
#             return {'status': 'success', 'message': 'Mail envoyé avec succès'}
#         except Exception as e:
#             _logger.error(f'Error sending email: {str(e)}')
#             return {'status': 'error', 'message': str(e)}

   

#     def check_overdue_payments_cron(self):
#         """
#         Méthode appelée par la tâche cron pour vérifier les paiements échus.
#         """
#         _logger.info("[CRON] Démarrage du cron de notifications pour commandes à crédit")

#         orders = self.search([('type_sale', '=', 'creditorder')])
#         _logger.info(f"[CRON] Commandes à traiter : {len(orders)}")

#         for order in orders:
#             if order.state == "draft" or order.state == "cancel" :
#                 _logger.info(f"[CRON] Traitement de la commande {order.name} pour {order.partner_id.name} annulée ou en brouliion ")

#             if order.state == "to_delivered" or order.state == "delivered" or order.state == "sale" :
#                 _logger.info(f"[CRON] Traitement de la commande {order.name} pour {order.partner_id.name}")
#                 order.send_payment_reminder()
            


#     def check_and_send_overdue_payments(self):
#         """
#         Vérifie et envoie les notifications de paiements échus pour toutes les commandes.
#         """
#         for order in self.search([]):
#             order.send_payment_reminder()

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)


def _safe_date(v):
    """Convertit v en date (str/datetime/date) sans lever d'exception."""
    if not v:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    try:
        # supporte 'YYYY-MM-DD' & ISO
        return datetime.fromisoformat(str(v)).date()
    except Exception:
        try:
            # fallback simple: 'YYYY-MM-DD HH:MM:SS'
            return datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S").date()
        except Exception:
            return None


class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    # -------------------- Petits wrappers -> utilisent tes helpers s'ils existent --------------------
    def _brand_logo(self):
        return getattr(self, 'LOGO_URL', None) or "https://ccbmshop.sn/logo.png"

    def _brand_site(self):
        return getattr(self, 'SITE_URL', None) or "https://ccbmshop.sn"

    def _p_display_name(self, p):
        f = getattr(self, "_partner_display_name", None)
        return f(p) if callable(f) else (p and (p.name or "") or "")

    def _p_email(self, p):
        f = getattr(self, "_partner_email", None)
        if callable(f):
            return f(p)
        return (getattr(p, "email", "") or "").strip()

    def _p_phone(self, p):
        f = getattr(self, "_partner_phone", None)
        if callable(f):
            return f(p)
        for attr in ("telephone", "phone", "mobile"):
            v = getattr(p, attr, False)
            if v:
                return v
        return ""

    def _fmt_money(self, amount):
        """
        Formate un montant avec la devise.
        Implémentation directe pour éviter toute récursion.
        Si une méthode parente existe (dans sale_a_credit.py), elle sera utilisée via l'ordre d'héritage.
        """
        # Implémentation directe pour éviter toute récursion
        cur = getattr(self, 'currency_id', None) and self.currency_id.name or ""
        try:
            return f"{float(amount or 0.0):,.0f} {cur}"
        except Exception:
            return f"{amount} {cur}"

    def _wrap_header(self, title):
        f = getattr(self, "_email_header_block", None)
        if callable(f):
            return f(title)
        # fallback minimal si ton header n'est pas importé
        return f"""
        <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width:590px;background:#FFF;padding:0 8px;border-collapse:separate;">
          <tr>
            <td valign="middle">
              <span style="font-size:10px;">{title}</span><br/>
              <span style="font-size:20px;font-weight:bold;">{self.name}</span>
            </td>
            <td valign="middle" align="right">
              <img src="{self._brand_logo()}" alt="Logo CCBM SHOP" style="width:120px;height:auto;display:block;border:0;outline:none;text-decoration:none;"/>
            </td>
          </tr>
          <tr>
            <td colspan="2" style="text-align:center;">
              <hr width="100%" style="background:#ccc;border:none;display:block;height:1px;margin:16px 0;"/>
            </td>
          </tr>
        </table>
        """

    def _wrap_footer(self):
        f = getattr(self, "_email_footer_block", None)
        if callable(f):
            return f()
        site = self._brand_site()
        return f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="590"
               style="background:#F1F1F1;color:#555;border-collapse:separate;margin-top:8px;">
          <tr>
            <td style="padding:12px;text-align:center;font-size:13px;line-height:1.6;">
              <div>📞 +221 33 849 65 49 / +221 70 922 17 75 &nbsp; | &nbsp; 📍 Ouest foire, après la fédération</div>
              <div>🛍️ <a href="{site}" target="_blank" rel="noopener" style="color:#875A7B;text-decoration:none;">www.ccbmshop.sn</a></div>
            </td>
          </tr>
        </table>
        """

    def _wrap_outer(self, inner_html, title):
        # réutilise ton _wrap_email si présent
        f = getattr(self, "_wrap_email", None)
        if callable(f):
            return f(inner_html, title)
        return f"""
        <table border="0" cellpadding="0" cellspacing="0"
               style="padding-top:16px;background:#FFFFFF;font-family:Verdana,Arial,sans-serif;color:#454748;width:100%;border-collapse:separate;">
          <tr><td align="center">
            <table border="0" cellpadding="0" cellspacing="0" width="590"
                   style="padding:16px;background:#FFFFFF;color:#454748;border-collapse:separate;">
              <tbody>
                <tr><td align="center" style="min-width:590px;">{self._wrap_header(_('Commande à crédit'))}</td></tr>
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
            {self._wrap_footer()}
          </td></tr>
        </table>
        """

    # ------------------------------ Core logique ------------------------------
    def _fetch_payment_lines(self):
        """
        Utilise ta méthode existante `get_sale_order_credit_payment` (dicts) si dispo.
        Retour: liste de dicts normés: {sequence, amount, state, rate, due_date(date)}
        """
        lines = []
        getter = getattr(self, "get_sale_order_credit_payment", None)
        raw = getter() if callable(getter) else []
        for l in raw or []:
            due = _safe_date(l.get("due_date"))
            lines.append({
                "sequence": int(l.get("sequence") or 0),
                "amount": float(l.get("amount") or 0.0),
                "state": bool(l.get("state")),
                "rate": l.get("rate"),
                "due_date": due,
            })
        # tri par séquence
        lines.sort(key=lambda x: x["sequence"])
        return lines

    def _iter_overdue_lines(self, today=None):
        today = today or datetime.now().date()
        for l in self._fetch_payment_lines():
            if not l["state"] and l["due_date"] and l["due_date"] < today and l["amount"] > 0:
                yield l

    def _iter_due_soon_lines(self, today=None, horizon_days=3):
        """
        Optionnel: relances J-3 (ou horizon paramétrable).
        """
        today = today or datetime.now().date()
        limit = today + timedelta(days=horizon_days)
        for l in self._fetch_payment_lines():
            if not l["state"] and l["due_date"] and today <= l["due_date"] <= limit and l["amount"] > 0:
                yield l

    # ------------------------------ Gabarits mails ------------------------------
    def _email_body_payment_reminder(self, partner, payment, kind="overdue"):
        """
        kind: 'overdue' (retard), 'due_soon' (échéance proche), 'due_today'
        """
        pname = self._p_display_name(partner)
        due_s = payment["due_date"].strftime('%d/%m/%Y') if payment["due_date"] else "—"
        amount_s = self._fmt_money(payment["amount"])

        if kind == "due_today":
            title = _("Rappel: échéance aujourd'hui")
            intro = _("Bonjour %(name)s, l'échéance de %(amount)s prévue aujourd'hui (%(date)s) arrive à son terme.",
                      name=pname, amount=amount_s, date=due_s)
            cta = _("Régler maintenant")
        elif kind == "due_soon":
            title = _("Rappel: échéance à venir")
            intro = _("Bonjour %(name)s, l'échéance de %(amount)s prévue le %(date)s approche.",
                      name=pname, amount=amount_s, date=due_s)
            cta = _("Régler maintenant")
        else:
            title = _("Rappel de paiement échu")
            intro = _("Bonjour %(name)s, le paiement de %(amount)s prévu le %(date)s est en retard.",
                      name=pname, amount=amount_s, date=due_s)
            cta = _("Se connecter")

        body = f"""
        <tr>
          <td align="center" style="font-size:22px;font-weight:bold;padding-bottom:20px;color:{'#dc3545' if kind=='overdue' else '#333'};">
            {'⚠️ ' if kind=='overdue' else ''}{title}
          </td>
        </tr>
        <tr>
          <td style="font-size:15px;color:#333;line-height:1.6;padding-bottom:12px;">
            {intro}
          </td>
        </tr>
        <tr>
          <td style="font-size:15px;color:#333;line-height:1.6;padding-bottom:10px;">
            {_('Détails de la commande')} :
            <ul style="margin:10px 0;padding-left:20px;color:#444;">
              <li><strong>{_('Référence')}</strong> : {self.name}</li>
              <li><strong>{_('Date de commande')}</strong> : {(self.date_order and _safe_date(self.date_order).strftime('%d/%m/%Y')) if self.date_order else '—'}</li>
              <li><strong>{_('Montant total')}</strong> : {self._fmt_money(self.amount_total)}</li>
            </ul>
          </td>
        </tr>
        <tr>
          <td align="center" style="padding:20px 0 8px 0;">
            <a href="{self._brand_site().rstrip('/')}/login"
               style="display:inline-block;background:#007bff;color:#fff;text-decoration:none;padding:12px 24px;font-size:15px;border-radius:6px;">
               {cta}
            </a>
          </td>
        </tr>
        """
        return self._wrap_outer(body, _("Commande à crédit"))

    def _sms_text_payment_reminder(self, partner, payment, kind="overdue"):
        due_s = payment["due_date"].strftime('%d/%m/%Y') if payment["due_date"] else "—"
        amount_s = self._fmt_money(payment["amount"])
        if kind == "due_today":
            txt = _("Bonjour %(name)s, échéance %(amount)s aujourd'hui (%(date)s) pour la commande %(order)s. Merci de régler.",
                    name=self._p_display_name(partner), amount=amount_s, date=due_s, order=self.name)
        elif kind == "due_soon":
            txt = _("Bonjour %(name)s, échéance %(amount)s le %(date)s (commande %(order)s). Pensez au règlement.",
                    name=self._p_display_name(partner), amount=amount_s, date=due_s, order=self.name)
        else:
            txt = _("Bonjour %(name)s, paiement %(amount)s (commande %(order)s, échéance %(date)s) en retard. Merci de régulariser.",
                    name=self._p_display_name(partner), amount=amount_s, order=self.name, date=due_s)
        return txt

    # ------------------------------ Envoi mails/SMS ------------------------------
    def _send_email_sms_reminder(self, partner, payment, kind="overdue"):
        # Appuie sur ton _send_mail_common si disponible (hérité)
        subject_map = {
            "overdue": _("🔔 Rappel : Paiement en retard - %(label)s", label=("Premier Paiement (Acompte)" if payment.get("sequence")==1 else _("Échéance %(n)s", n=payment.get("sequence")))),
            "due_today": _("Rappel : échéance aujourd'hui - %(label)s", label=("Premier Paiement (Acompte)" if payment.get("sequence")==1 else _("Échéance %(n)s", n=payment.get("sequence")))),
            "due_soon": _("Rappel : échéance à venir - %(label)s", label=("Premier Paiement (Acompte)" if payment.get("sequence")==1 else _("Échéance %(n)s", n=payment.get("sequence")))),
        }
        subject = subject_map.get(kind, _("Rappel de paiement"))

        try:
            # Email
            send_common = getattr(self, "_send_mail_common", None)
            if callable(send_common):
                html = self._email_body_payment_reminder(partner, payment, kind=kind)
                send_common(
                    partner=partner,
                    subject=subject,
                    body_html=html,
                    sms_type=None,  # SMS envoyé juste après
                    extra_recipients=['shop@ccbm.sn'],
                )
            else:
                # Fallback si _send_mail_common n'existe pas (théoriquement il existe chez toi)
                mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                if not mail_server or not self._p_email(partner):
                    _logger.warning("Pas d'email ou pas de serveur mail — mail non envoyé (rappel)")
                else:
                    email_from = mail_server.smtp_user or 'noreply@ccbmshop.sn'
                    email_to = ', '.join([self._p_email(partner), 'shop@ccbm.sn'])
                    self.env['mail.mail'].sudo().create({
                        'email_from': email_from,
                        'email_to': email_to,
                        'subject': subject,
                        'body_html': self._email_body_payment_reminder(partner, payment, kind=kind),
                        'state': 'outgoing',
                        'auto_delete': False,
                    }).send()

            # SMS
            phone = self._p_phone(partner)
            if phone:
                Sms = self.env.get('send.sms')
                if Sms:
                    Sms.create({
                        'recipient': phone,
                        'message': self._sms_text_payment_reminder(partner, payment, kind=kind),
                    }).send_sms()
                else:
                    _logger.warning("Module send.sms indisponible — SMS non envoyé (rappel)")
            else:
                _logger.warning("Numéro manquant — SMS non envoyé (rappel)")

        except Exception as e:
            _logger.error("Erreur envoi rappel %s (%s): %s", self.name, kind, e, exc_info=True)

    # ------------------------------ API publiques ------------------------------
    def send_payment_reminder(self, include_due_soon=False, soon_horizon_days=3):
        """
        Envoie les rappels:
          - paiements en retard (toujours)
          - en option: échéances à venir (J+0/J+N)
        """
        today = datetime.now().date()

        # Overdue
        for p in self._iter_overdue_lines(today=today):
            self._send_email_sms_reminder(self.partner_id, p, kind="overdue")

        if include_due_soon:
            # J0
            for p in self._fetch_payment_lines():
                if not p["state"] and p["due_date"] == today and p["amount"] > 0:
                    self._send_email_sms_reminder(self.partner_id, p, kind="due_today")
            # J..J+N
            for p in self._iter_due_soon_lines(today=today, horizon_days=soon_horizon_days):
                # éviter doublons avec J0
                if p["due_date"] > today:
                    self._send_email_sms_reminder(self.partner_id, p, kind="due_soon")

    # ------------------------------ CRON ------------------------------
    def check_overdue_payments_cron(self):
        """
        Cron: vérifie toutes les commandes à crédit actives et envoie les rappels.
        - Envoie toujours les 'overdue'
        - Envoie aussi les 'due_soon' (J-3 par défaut) pour prévenir
        """
        _logger.info("[CRON] Relances paiements (creditorder) — start")
        domain_orders = [
            ('type_sale', '=', 'creditorder'),
            ('state', 'in', ['sale', 'to_delivered', 'delivered']),
        ]
        orders = self.search(domain_orders)
        _logger.info("[CRON] Commandes à traiter: %s", len(orders))
        for order in orders:
            try:
                order.send_payment_reminder(include_due_soon=True, soon_horizon_days=3)
            except Exception as e:
                _logger.error("[CRON] Erreur sur %s: %s", order.name, e, exc_info=True)
        _logger.info("[CRON] Relances paiements — end")

    def check_and_send_overdue_payments(self):
        """
        Appel manuel (ex: bouton serveur) si tu veux tout relancer à la main.
        """
        for order in self.search([('type_sale', '=', 'creditorder')]):
            order.send_payment_reminder(include_due_soon=True, soon_horizon_days=3)
