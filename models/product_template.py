
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_1 = fields.Binary(string='Image 1', attachment=True)
    image_2 = fields.Binary(string='Image 2', attachment=True)
    image_3 = fields.Binary(string='Image 3', attachment=True)
    image_4 = fields.Binary(string='Image 4', attachment=True)
    rang = fields.Char(string='Numero de rang', required=False)
    comment_ids = fields.One2many('web.commentaire', 'product_id', string='Commentaires')

    # ➕ indicateur "manuel"
    creditorder_manual = fields.Boolean(
        string="Prix à crédit manuellement",
        default=False,
        help="Si coché, la valeur saisie ne sera pas écrasée par le calcul automatique."
    )

    creditorder_price = fields.Float(
        'Prix commande à crédit',
        digits='Product Price',
        compute='_compute_creditorder_price',
        # inverse='_inverse_creditorder_price',
        store=True,
        readonly=False,                         # ⬅️ autorise la saisie dans l'UI
        help="Par défaut: standard_price × 1.40 (coût + 40%). "
             "Si vous modifiez la valeur, elle sera conservée (mode manuel)."
    )

    @api.depends('standard_price', 'list_price', 'creditorder_manual')
    def _compute_creditorder_price(self):
        """
        Méthode de calcul automatique du prix à crédit pour un produit.
        Cette méthode est appelée automatiquement par Odoo lorsque l'un des champs
        'standard_price', 'list_price' ou 'creditorder_manual' est modifié.
        """
        for prod in self:
            # Vérifie si le prix à crédit n'est pas en mode manuel
            if not prod.creditorder_manual:
                # Si le prix de vente (list_price) est inférieur à 100 000
                if prod.list_price < 100000:
                    # Récupère le coût du produit (standard_price), ou 0.0 si non défini
                    cost = prod.standard_price or 0.0
                    # Calcule le prix à crédit comme 150% du coût (50% de marge)
                    prod.creditorder_price = cost * 1.50
                else:
                    # Récupère le coût du produit (standard_price), ou 0.0 si non défini
                    cost = prod.standard_price or 0.0
                    # Calcule le prix à crédit comme 120% du coût (20% de marge)
                    prod.creditorder_price = cost * 1.20



    @api.onchange('is_creditorder')
    def _onchange_is_credit_available(self):
        """Applique automatiquement la TVA de 18% si le produit est disponible à crédit."""
        if self.is_creditorder:
            # Récupérer le groupe fiscal de 18% (à adapter selon votre configuration)
            tva_18 = self.env['account.tax'].search([
                ('type_tax_use', '=', 'sale'),
                ('amount', '=', 18.0),
            ], limit=1)
            if tva_18:
                self.taxes_id = [(6, 0, [tva_18.id])]
    
    @api.model
    def create(self, vals):
        """Applique la TVA de 18% si le produit est disponible à crédit."""
        res = super(ProductTemplate, self).create(vals)
        if res.is_creditorder:
            tva_18 = self.env['account.tax'].search([
                ('type_tax_use', '=', 'sale'),
                ('amount', '=', 18.0),
            ], limit=1)
            if tva_18:
                res.taxes_id = [(6, 0, [tva_18.id])]
        return res


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
        # products = self.search([('creditorder_manual', '=', False)])
        products = self.search([])
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
        # for p in self:
        #     p.creditorder_manual = False
        self._compute_creditorder_price()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Mode automatique'), 'message': _('Prix recalculé.'), 'type': 'success'}
        }
    
