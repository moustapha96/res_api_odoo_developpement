
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
        string="Prix à crédit saisi manuellement",
        default=False,
        help="Si coché, la valeur saisie ne sera pas écrasée par le calcul automatique."
    )

    creditorder_price = fields.Float(
        'Prix commande à crédit',
        digits='Product Price',
        compute='_compute_creditorder_price',
        store=True,
        readonly=False,                         # ⬅️ autorise la saisie dans l'UI
        help="Par défaut: standard_price × 1.40 (coût + 40%). "
             "Si standard_price < 100000: standard_price × 1.50 (coût + 50%). "
             "Si vous modifiez la valeur, elle sera conservée (mode manuel)."
    )

    @api.depends('standard_price', 'creditorder_manual')
    def _compute_creditorder_price(self):
        """
        Méthode de calcul automatique du prix à crédit pour un produit.
        Cette méthode est appelée automatiquement par Odoo lorsque l'un des champs
        'standard_price' ou 'creditorder_manual' est modifié.
        
        Règles de calcul :
        - Par défaut : standard_price × 1.40 (coût + 40% de marge)
        - Si standard_price < 100000 : standard_price × 1.50 (coût + 50% de marge)
        """
        for prod in self:
            # Vérifie si le prix à crédit n'est pas en mode manuel
            if not prod.creditorder_manual:
                # Récupère le coût du produit (standard_price), ou 0.0 si non défini
                cost = prod.standard_price or 0.0
                
                # Si le coût (standard_price) est inférieur à 100 000
                if cost < 100000:
                    # Calcule le prix à crédit comme 150% du coût (50% de marge)
                    prod.creditorder_price = cost * 1.50
                else:
                    # Calcule le prix à crédit comme 140% du coût (40% de marge)
                    prod.creditorder_price = cost * 1.40



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
        # to_auto = self.filtered(lambda p: not p.creditorder_manual)
        to_auto = self
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
        """Active le mode automatique et affiche le nouveau montant calculé."""
        if not self:
            raise UserError(_("Aucun produit sélectionné."))
        
        # Désactiver le mode manuel pour tous les produits
        for p in self:
            p.creditorder_manual = False
        
        # Recalculer le prix à crédit
        self._compute_creditorder_price()
        
        # Si un seul produit, afficher le montant détaillé
        if len(self) == 1:
            currency = self.currency_id or self.env.company.currency_id
            new_amount = self.creditorder_price or 0.0
            amount_formatted = f"{new_amount:,.0f} {currency.name}"
            message = _('Prix recalculé. Nouveau montant : %s') % amount_formatted
        else:
            # Si plusieurs produits, afficher le nombre
            message = _('Prix recalculé pour %s produit(s).') % len(self)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Mode automatique'),
                'message': message,
                'type': 'success',
                'sticky': False
            }
        }
    
