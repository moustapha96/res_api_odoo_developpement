# from odoo import models, fields, api

# from odoo.http import request
# import logging
# from datetime import datetime, timedelta
# import base64

# _logger = logging.getLogger(__name__)

# class SaleCreditOrderMail(models.Model):
#     _inherit = 'sale.order'


#     from odoo import models, fields, api
# from odoo.http import request
# import logging
# from datetime import datetime, timedelta

# _logger = logging.getLogger(__name__)

# class SaleCreditOrderMail(models.Model):
#     _inherit = 'sale.order'


#     def send_credit_order_validation_mail(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Validation de votre précommande à crédit'
        
#         today = datetime.now().date()
#         payment_dates = [today + timedelta(days=30*i) for i in range(1, 5)]
        
#         total_amount = self.amount_total
#         first_payment = total_amount * 0.5
#         second_payment = total_amount * 0.15
#         third_payment = total_amount * 0.15
#         fourth_payment = total_amount * 0.20

#         payment_info = f'''
#         <h3>Informations de paiement</h3>
#         <p>Veuillez noter que le paiement initial de 50% validera complètement votre commande à crédit.</p>
#         <table border='1' cellpadding='5' cellspacing='0' width='590' style='min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;'>
#             <tr>
#                 <th>Échéance</th>
#                 <th>Montant</th>
#                 <th>Pourcentage</th>
#                 <th>Date d'échéance</th>
#             </tr>
#             <tr>
#                 <td>Paiement initial</td>
#                 <td>{first_payment:.2f}</td>
#                 <td>50%</td>
#                 <td>{payment_dates[0].strftime('%d/%m/%Y')}</td>
#             </tr>
#             <tr>
#                 <td>Deuxième paiement</td>
#                 <td>{second_payment:.2f}</td>
#                 <td>15%</td>
#                 <td>{payment_dates[1].strftime('%d/%m/%Y')}</td>
#             </tr>
#             <tr>
#                 <td>Troisième paiement</td>
#                 <td>{third_payment:.2f}</td>
#                 <td>15%</td>
#                 <td>{payment_dates[2].strftime('%d/%m/%Y')}</td>
#             </tr>
#             <tr>
#                 <td>Quatrième paiement</td>
#                 <td>{fourth_payment:.2f}</td>
#                 <td>20%</td>
#                 <td>{payment_dates[3].strftime('%d/%m/%Y')}</td>
#             </tr>
#         </table>
#         '''
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Validation de votre précommande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Félicitations {partner.name},</p>
#                                                 <p>Votre précommande à crédit numéro {self.name} a été validée.</p>
#                                                 <p><strong>Important :</strong> Le paiement initial de 50% validera complètement votre commande à crédit.</p>
#                                                 <p>Détails de la commande :</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="1" cellpadding="5" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;">
#                                         <tr>
#                                             <th>Produit</th>
#                                             <th>Quantité</th>
#                                             <th>Prix unitaire</th>
#                                             <th>Total</th>
#                                         </tr>
#                                         {"".join([f"<tr><td>{line.product_id.name}</td><td>{line.product_uom_qty}</td><td>{line.price_unit}</td><td>{line.price_total}</td></tr>" for line in self.order_line])}
#                                         <tr>
#                                             <td colspan="3" style="text-align:right; font-weight:bold;">Total du panier :</td>
#                                             <td style="font-weight:bold;">{self.amount_total}</td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     {payment_info}
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td align="center" style="min-width: 590px;">
#                                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
#                                         <tr>
#                                             <td>
#                                                 <p>Nous vous remercions pour votre confiance.</p>
#                                                 <p>Pour toute question concernant votre commande, n'hésitez pas à nous contacter.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''


#         self.send_mail(mail_server, partner, subject, body_html)

#     def send_credit_order_rejection_mail(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Rejet de votre commande à crédit'
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Rejet de votre commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Cher(e) {partner.name},</p>
#                                                 <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.</p>
#                                                 <p>Si vous avez des questions concernant cette décision, n'hésitez pas à nous contacter pour plus d'informations.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         self.send_mail(mail_server, partner, subject, body_html)

#     def send_credit_order_rh_rejected(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Rejet de votre commande à crédit par le service RH'
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Rejet de votre commande à crédit par le service RH</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Cher(e) {partner.name},</p>
#                                                 <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre service des Ressources Humaines.</p>
#                                                 <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         self.send_mail(mail_server, partner, subject, body_html)

#     def send_credit_order_admin_rejected(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Rejet de votre commande à crédit par l\'administration'
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Rejet de votre commande à crédit par l'administration</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Cher(e) {partner.name},</p>
#                                                 <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre administration.</p>
#                                                 <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         self.send_mail(mail_server, partner, subject, body_html)

#     def send_credit_order_admin_validation(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Validation administrative de votre commande à crédit'
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Validation administrative de votre commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Cher(e) {partner.name},</p>
#                                                 <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre administration.</p>
#                                                 <p>Cette étape marque une avancée importante dans le processus de validation de votre commande.</p>
#                                                 <p>Nous vous tiendrons informé des prochaines étapes.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         self.send_mail(mail_server, partner, subject, body_html)

#     def send_credit_order_rh_validation(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Validation RH de votre commande à crédit'
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Validation RH de votre commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Cher(e) {partner.name},</p>
#                                                 <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre service des Ressources Humaines.</p>
#                                                 <p>Cette étape marque une avancée importante dans le processus de validation de votre commande.</p>
#                                                 <p>Nous vous tiendrons informé des prochaines étapes.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         self.send_mail(mail_server, partner, subject, body_html)


#     def send_credit_order_request_mail(self):
#         mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
#         partner = self.partner_id
#         if not partner:
#             return {'status': 'error', 'message': 'Partner not found for the given order'}
        
#         subject = 'Demande de commande à crédit en cours'
        
#         create_account_section = ""
#         if not partner.password:
#             create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
#             create_account_section = f'''
#                 <tr>
#                     <td align="center" style="min-width: 590px; padding-top: 20px;">
#                         <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre commande à crédit :</span><br/>
#                         <a href="{create_account_link}" style="font-size: 16px; font-weight: bold;">Créer un compte</a>
#                     </td>
#                 </tr>
#             '''
        
#         body_html = f'''
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
#                                                 <span style="font-size: 10px;">Votre demande de commande à crédit</span><br/>
#                                                 <span style="font-size: 20px; font-weight: bold;">
#                                                     {self.name}
#                                                 </span>
#                                             </td>
#                                             <td valign="middle" align="right">
#                                                 <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
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
#                                                 <p>Bonjour {partner.name},</p>
#                                                 <p>Nous avons bien reçu votre demande de commande à crédit numéro {self.name}.</p>
#                                                 <p>Elle est actuellement en cours de validation par nos services.</p>
#                                                 <p>Nous vous tiendrons informé de l'avancement de votre demande.</p>
#                                             </td>
#                                         </tr>
#                                     </table>
#                                 </td>
#                             </tr>
#                             {create_account_section}
#                         </tbody>
#                     </table>
#                 </td>
#             </tr>
#             <tr>
#                 <td align="center" style="min-width: 590px;">
#                     <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
#                         <tr>
#                             <td style="text-align: center; font-size: 13px;">
#                                 Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
#                             </td>
#                         </tr>
#                     </table>
#                 </td>
#             </tr>
#         </table>
#         '''

#         email_from = mail_server.smtp_user
#         additional_email = 'shop@ccbm.sn'
#         email_to = f'{partner.email}, {additional_email}'

#         email_values = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'subject': subject,
#             'body_html': body_html,
#             'state': 'outgoing',
#         }

#         mail_mail = request.env['mail.mail'].sudo().create(email_values)
#         try:
#             mail_mail.send()
#             return {'status': 'success', 'message': 'Mail envoyé avec succès'}
#         except Exception as e:
#             _logger.error(f'Error sending email: {str(e)}')
#             return {'status': 'error', 'message': str(e)}


#     def action_confirm(self):
#         res = super(SaleCreditOrderMail, self).action_confirm()
#         if self.type_order == 'creditorder':
#             if self.validation_state == 'validated' and self.validation_rh == 'validated' and self.validation_admin == 'validated':
#                 self.send_credit_order_validation_mail()
#             elif self.validation_state == 'rejected' or self.validation_rh == 'rejected' or self.validation_admin == 'rejected':
#                 self.send_credit_order_rejection_mail()
#         return res

#     def send_mail(self, mail_server, partner, subject, body_html):
#         email_from = mail_server.smtp_user
#         additional_email = 'shop@ccbm.sn'
#         email_to = f'{partner.email}, {additional_email}'

#         email_values = {
#             'email_from': email_from,
#             'email_to': email_to,
#             'subject': subject,
#             'body_html': body_html,
#             'state': 'outgoing',
#         }

#         mail_mail = self.env['mail.mail'].sudo().create(email_values)
#         try:
#             mail_mail.send()
#             return {'status': 'success', 'message': 'Mail envoyé avec succès'}
#         except Exception as e:
#             _logger.error(f'Error sending email: {str(e)}')
#             return {'status': 'error', 'message': str(e)}
        
#     def action_validate_credit_order(self):
#         self.validation_state = 'validated'
#         self.validation_rh = 'validated'
#         self.validation_admin = 'validated'
#         self.send_credit_order_validation_mail()

#     def action_reject_credit_order(self):
#         self.validation_state = 'rejected'
#         self.send_credit_order_rejection_mail()

#     def action_reject_credit_rh(self):
#         self.validation_rh = 'rejected'
#         self.send_credit_order_rh_rejected()

#     def action_reject_credit_admin(self):
#         self.validation_admin = 'rejected'
#         self.send_credit_order_admin_rejected()

#     def action_validate_credit_admin(self):
#         self.validation_admin = 'validated'
#         self.send_credit_order_admin_validation()

#     def action_validate_credit_rh(self):
#         self.validation_rh = 'validated'
#         self.send_credit_order_rh_validation()



#     @api.model
#     def create(self):
#         res = super(SaleCreditOrderMail, self).create()
#         if res.type_order == 'creditorder':
#             self.send_credit_order_request_mail(self)
#         return res
        
#     @api.model
#     def create_credit_order(self):
#         res = super(SaleCreditOrderMail, self).create_credit_order()
#         if self.type_sale == 'creditorder':
#             if self.validation_admin == "validated":
#                 self.send_credit_order_admin_validation()
#             elif self.validation_admin == "rejected":
#                 self.send_credit_order_admin_rejected()
#             elif self.validation_rh == "validated":
#                 self.send_credit_order_rh_validation()
#             elif self.validation_rh == "rejected":
#                 self.send_credit_order_rh_rejected()
#         return res
from odoo import models, fields, api
from odoo.http import request
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class SaleCreditOrderMail(models.Model):
    _inherit = 'sale.order'

    def send_credit_order_validation_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Validation de votre précommande à crédit'
        
        today = datetime.now().date()
        payment_dates = [today + timedelta(days=30*i) for i in range(1, 5)]
        
        total_amount = self.amount_total
        payments = [
            ('Paiement initial', total_amount * 0.5, '50%', payment_dates[0]),
            ('Deuxième paiement', total_amount * 0.15, '15%', payment_dates[1]),
            ('Troisième paiement', total_amount * 0.15, '15%', payment_dates[2]),
            ('Quatrième paiement', total_amount * 0.20, '20%', payment_dates[3])
        ]

        payment_info = self._generate_payment_info_html(payments)
        body_html = self._generate_email_body_html(partner, 'validation', payment_info)

        self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_rejection_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Rejet de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'rejection')

        self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_rh_rejected(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Rejet de votre commande à crédit par le service RH'
        body_html = self._generate_email_body_html(partner, 'rh_rejection')

        self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_admin_rejected(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Rejet de votre commande à crédit par l\'administration'
        body_html = self._generate_email_body_html(partner, 'admin_rejection')

        self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_admin_validation(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Validation administrative de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'admin_validation')

        self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_rh_validation(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Validation RH de votre commande à crédit'
        body_html = self._generate_email_body_html(partner, 'rh_validation')

        self.send_mail(mail_server, partner, subject, body_html)

    def send_credit_order_request_mail(self):
        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        
        partner = self.partner_id
        if not partner:
            return {'status': 'error', 'message': 'Partner not found for the given order'}
        
        subject = 'Demande de commande à crédit en cours'
        
        create_account_section = ""
        if not partner.password:
            create_account_link = f"https://ccbme.sn/create-compte?mail={partner.email}"
            create_account_section = self._generate_create_account_section(create_account_link)
        
        body_html = self._generate_email_body_html(partner, 'request', create_account_section)

        self.send_mail(mail_server, partner, subject, body_html)

    def _generate_payment_info_html(self, payments):
        payment_rows = "".join([
            f"""
            <tr>
                <td>{payment[0]}</td>
                <td>{payment[1]:.2f}</td>
                <td>{payment[2]}</td>
                <td>{payment[3].strftime('%d/%m/%Y')}</td>
            </tr>
            """ for payment in payments
        ])

        return f"""
        <h3>Informations de paiement</h3>
        <p>Veuillez noter que le paiement initial de 50% validera complètement votre commande à crédit.</p>
        <table border='1' cellpadding='5' cellspacing='0' width='590' style='min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:collapse;'>
            <tr>
                <th>Échéance</th>
                <th>Montant</th>
                <th>Pourcentage</th>
                <th>Date d'échéance</th>
            </tr>
            {payment_rows}
        </table>
        """

    def _generate_create_account_section(self, create_account_link):
        return f"""
        <tr>
            <td align="center" style="min-width: 590px; padding-top: 20px;">
                <span style="font-size: 14px;">Cliquez sur le lien suivant pour créer un compte et suivre votre commande à crédit :</span><br/>
                <a href="{create_account_link}" style="font-size: 16px; font-weight: bold;">Créer un compte</a>
            </td>
        </tr>
        """

    def _generate_email_body_html(self, partner, email_type, additional_content=""):
        email_content = {
            'validation': {
                'title': 'Validation de votre précommande à crédit',
                'content': f"""
                    <p>Félicitations {partner.name},</p>
                    <p>Votre précommande à crédit numéro {self.name} a été validée.</p>
                    <p><strong>Important :</strong> Le paiement initial de 50% validera complètement votre commande à crédit.</p>
                    <p>Détails de la commande :</p>
                """
            },
            'rejection': {
                'title': 'Rejet de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée.</p>
                    <p>Si vous avez des questions concernant cette décision, n'hésitez pas à nous contacter pour plus d'informations.</p>
                """
            },
            'rh_rejection': {
                'title': 'Rejet de votre commande à crédit par le service RH',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre service des Ressources Humaines.</p>
                    <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
                """
            },
            'admin_rejection': {
                'title': 'Rejet de votre commande à crédit par l\'administration',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous regrettons de vous informer que votre commande à crédit numéro {self.name} a été rejetée par notre administration.</p>
                    <p>Si vous avez des questions concernant cette décision, n'hésitez pas à contacter notre service client pour plus d'informations.</p>
                """
            },
            'admin_validation': {
                'title': 'Validation administrative de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre administration.</p>
                    <p>Cette étape marque une avancée importante dans le processus de validation de votre commande.</p>
                    <p>Nous vous tiendrons informé des prochaines étapes.</p>
                """
            },
            'rh_validation': {
                'title': 'Validation RH de votre commande à crédit',
                'content': f"""
                    <p>Cher(e) {partner.name},</p>
                    <p>Nous avons le plaisir de vous informer que votre commande à crédit numéro {self.name} a été validée par notre service des Ressources Humaines.</p>
                    <p>Cette étape marque une avancée importante dans le processus de validation de votre commande.</p>
                    <p>Nous vous tiendrons informé des prochaines étapes.</p>
                """
            },
            'request': {
                'title': 'Votre demande de commande à crédit',
                'content': f"""
                    <p>Bonjour {partner.name},</p>
                    <p>Nous avons bien reçu votre demande de commande à crédit numéro {self.name}.</p>
                    <p>Elle est actuellement en cours de validation par nos services.</p>
                    <p>Nous vous tiendrons informé de l'avancement de votre demande.</p>
                """
            }
        }

        return f"""
        <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #FFFFFF; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">
            <tr>
                <td align="center">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: #FFFFFF; color: #454748; border-collapse:separate;">
                        <tbody>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td valign="middle">
                                                <span style="font-size: 10px;">{email_content[email_type]['title']}</span><br/>
                                                <span style="font-size: 20px; font-weight: bold;">
                                                    {self.name}
                                                </span>
                                            </td>
                                            <td valign="middle" align="right">
                                                <img style="padding: 0px; margin: 0px; height: auto; width: 120px;" src="https://ccbme.sn/logo.png" alt="logo CCBM SHOP"/>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td colspan="2" style="text-align:center;">
                                                <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="min-width: 590px;">
                                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                                        <tr>
                                            <td>
                                                {email_content[email_type]['content']}
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            {additional_content}
                        </tbody>
                    </table>
                </td>
            </tr>
            <tr>
                <td align="center" style="min-width: 590px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">
                        <tr>
                            <td style="text-align: center; font-size: 13px;">
                                Généré par <a target="_blank" href="https://ccbme.sn" style="color: #875A7B;">CCBM SHOP</a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

    def send_mail(self, mail_server, partner, subject, body_html):
        email_from = mail_server.smtp_user
        additional_email = 'shop@ccbm.sn'
        email_to = f'{partner.email}, {additional_email}'

        email_values = {
            'email_from': email_from,
            'email_to': email_to,
            'subject': subject,
            'body_html': body_html,
            'state': 'outgoing',
        }

        mail_mail = self.env['mail.mail'].sudo().create(email_values)
        try:
            mail_mail.send()
            return {'status': 'success', 'message': 'Mail envoyé avec succès'}
        except Exception as e:
            _logger.error(f'Error sending email: {str(e)}')
            return {'status': 'error', 'message': str(e)}

   

   
    def action_validate_credit_order(self):
        self.validation_state = 'validated'
        self.validation_rh = 'validated'
        self.validation_admin = 'validated'
        self.send_credit_order_validation_mail()

    def action_reject_credit_order(self):
        self.validation_state = 'rejected'
        self.send_credit_order_rejection_mail()

    def action_reject_credit_rh(self):
        self.validation_rh = 'rejected'
        self.send_credit_order_rh_rejected()

    def action_reject_credit_admin(self):
        self.validation_admin = 'rejected'
        self.send_credit_order_admin_rejected()

    def action_validate_credit_admin(self):
        self.validation_admin = 'validated'
        self.send_credit_order_admin_validation()

    def action_validate_credit_rh(self):
        self.validation_rh = 'validated'
        self.send_credit_order_rh_validation()

    @api.model
    def create(self, vals):
        res = super(SaleCreditOrderMail, self).create(vals)
        if self.type_order == 'creditorder':
            self.send_credit_order_request_mail()
        return res
        
    @api.model
    def create_credit_order(self):
        res = super(SaleCreditOrderMail, self).create_credit_order()
        if self.type_sale == 'creditorder':
            if self.validation_admin == "validated":
                self.send_credit_order_admin_validation()
            elif self.validation_admin == "rejected":
                self.send_credit_order_admin_rejected()
            elif self.validation_rh == "validated":
                self.send_credit_order_rh_validation()
            elif self.validation_rh == "rejected":
                self.send_credit_order_rh_rejected()
        return res
    
    @api.model
    def action_confirm(self):
        res = super(SaleCreditOrderMail, self).action_confirm()
        if self.type_order == 'creditorder':
            if self.validation_state == 'validated' and self.validation_rh == 'validated' and self.validation_admin == 'validated':
                self.send_credit_order_validation_mail()
            elif self.validation_state == 'rejected' or self.validation_rh == 'rejected' or self.validation_admin == 'rejected':
                self.send_credit_order_rejection_mail()
        return res