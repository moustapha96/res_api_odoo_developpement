# from odoo import api, fields, models , _
# from odoo.exceptions import UserError


# class ProductTemplate(models.Model):
#     _inherit = 'product.template'

#     image_1 = fields.Binary(string='Image 1', attachment=True)
#     image_2 = fields.Binary(string='Image 2', attachment=True)
#     image_3 = fields.Binary(string='Image 3', attachment=True)
#     image_4 = fields.Binary(string='Image 4', attachment=True)

#     comment_ids = fields.One2many('web.commentaire', 'product_id', string='Commentaires')

#     creditorder_price = fields.Float(
#         'Prix commande à crédit',
#         digits='Product Price',
#         compute='_compute_creditorder_price',
#         store=True,
#         help="Toujours 40% du coût standard (standard_price)."
#     )

#     @api.depends('standard_price')
#     def _compute_creditorder_price(self):
#         for prod in self:
#             cost = prod.standard_price or 0.0
#             prod.creditorder_price = cost * 1.40


#     @api.model
#     def cron_force_recompute_creditorder_price(self):
#         recs = self.search([])
#         recs._compute_creditorder_price()
#         return len(recs)



#     def action_recompute_creditorder_price(self):
#         """
#         Bouton 'Recalculer prix crédit' sur la fiche produit.
#         - Si appelé depuis la fiche : agit sur ce produit.
#         - Si appelé depuis la liste (action contextuelle) : agit sur tous les produits sélectionnés.
#         """
#         # self = recordset des templates sélectionnés
#         if not self:
#             raise UserError(_("Aucun produit sélectionné."))

#         # Force le compute
#         # (comme le champ est compute+store, on appelle directement le compute)
#         self._compute_creditorder_price()

#         # Notification UI
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': _('Prix crédit mis à jour'),
#                 'message': _('Recalcul effectué pour %s produit(s).') % len(self),
#                 'type': 'success',
#                 'sticky': False,
#             }
#         }

#     @api.model
#     def action_recompute_creditorder_price_all(self):
#         """
#         Variante : bouton/serveur pour TOUTES les fiches produits.
#         À lier à une action serveur ou un cron au besoin.
#         """
#         products = self.search([])
#         products._compute_creditorder_price()
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': _('Prix crédit mis à jour (global)'),
#                 'message': _('Recalcul effectué pour %s produit(s).') % len(products),
#                 'type': 'success',
#                 'sticky': False,
#             }
#         }


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_1 = fields.Binary(string='Image 1', attachment=True)
    image_2 = fields.Binary(string='Image 2', attachment=True)
    image_3 = fields.Binary(string='Image 3', attachment=True)
    image_4 = fields.Binary(string='Image 4', attachment=True)

    comment_ids = fields.One2many('web.commentaire', 'product_id', string='Commentaires')

    # ➕ indicateur "manuel"
    creditorder_manual = fields.Boolean(
        string="Prix à crédit saisi manuellement",
        default=False,
        help="Si coché, la valeur saisie ne sera pas écrasée par le calcul automatique."
    )

    creditorder_price = fields.Float(
        'Prix commande à crédit',
        digits='Product Price',
        compute='_compute_creditorder_price',
        inverse='_inverse_creditorder_price',   # ⬅️ rend le champ éditable
        store=True,
        readonly=False,                         # ⬅️ autorise la saisie dans l'UI
        help="Par défaut: standard_price × 1.40 (coût + 40%). "
             "Si vous modifiez la valeur, elle sera conservée (mode manuel)."
    )

    @api.depends('standard_price', 'creditorder_manual')
    def _compute_creditorder_price(self):
        for prod in self:
            # NE recalculer que si pas manuel
            if not prod.creditorder_manual:
                cost = prod.standard_price or 0.0
                prod.creditorder_price = cost * 1.40

    def _inverse_creditorder_price(self):
        """Quand l'utilisateur modifie la valeur dans l'UI, on bascule en mode manuel."""
        for prod in self:
            if not prod.creditorder_manual:
                prod.creditorder_manual = True

    @api.model
    def cron_force_recompute_creditorder_price(self):
        recs = self.search([])
        recs._compute_creditorder_price()
        return len(recs)

    def action_recompute_creditorder_price(self):
        """
        Bouton 'Recalculer prix crédit' sur la fiche produit.
        """
        if not self:
            raise UserError(_("Aucun produit sélectionné."))
        # Ne recalculer que ceux NON manuels
        to_auto = self.filtered(lambda p: not p.creditorder_manual)
        to_auto._compute_creditorder_price()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prix crédit mis à jour'),
                'message': _('Recalcul effectué pour %s produit(s) (non manuels).') % len(to_auto),
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def action_recompute_creditorder_price_all(self):
        """
        Variante : recalcul global (ne touche pas aux valeurs manuelles).
        """
        products = self.search([('creditorder_manual', '=', False)])
        products._compute_creditorder_price()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prix crédit mis à jour (global)'),
                'message': _('Recalcul effectué pour %s produit(s) (non manuels).') % len(products),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_set_creditorder_auto(self):
        for p in self:
            p.creditorder_manual = False
        self._compute_creditorder_price()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Mode automatique'), 'message': _('Prix recalculé.'), 'type': 'success'}
        }
