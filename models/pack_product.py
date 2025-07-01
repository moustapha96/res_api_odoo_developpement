
from odoo import models, fields, api, _

import random
import string

import logging


_logger = logging.getLogger(__name__)

class PackProduit(models.Model):
    _name = 'pack.produit'
    _description = 'Pack de Produits'

    name = fields.Char(string='Nom', required=True)
    start_date = fields.Date(string='Date de commencement')
    end_date = fields.Date(string='Date de fin')
    code = fields.Char(string='Code du Pack', required=True, copy=False, readonly=True, index=True, default=lambda self: _('Nouveau'))
    product_line_ids = fields.One2many('pack.produit.line', 'pack_id', string='Produits')
    image = fields.Binary(string='Image', attachment=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('actif', 'Actif'),
        ('expire', 'Expire'),
    ], default='draft', string='Etat')

    @api.model
    def create(self, vals):
        """ Génère automatiquement un code unique basé sur le nom + chiffres aléatoires. """
        if vals.get('code', _('Nouveau')) == _('Nouveau'):
            name = vals.get('name', 'PACK')
            prefix = ''.join(e for e in name[:4].upper() if e.isalnum())  # Récupère les 4 premiers caractères valides
            random_number = ''.join(random.choices(string.digits, k=4))  # 4 chiffres aléatoires
            vals['code'] = f"{prefix}{random_number}"

        return super(PackProduit, self).create(vals)

    def action_activate(self):
        """ Active le pack produit. """
        self.write({'state': 'actif'})

    def action_expire(self):
        """ Expire le pack produit manuellement. """
        self.write({'state': 'expire'})

    @api.model
    def cron_check_expired_packs(self):
        """ Cron Job pour vérifier et expirer les packs périmés chaque jour. """
        expired_packs = self.search([('end_date', '<', fields.Date.today()), ('state', '!=', 'expire')])
        expired_packs.write({'state': 'expire'})
        _logger.info(f"Expiré {len(expired_packs)} packs périmés automatiquement.")


class PackProduitLine(models.Model):
    _name = 'pack.produit.line'
    _description = 'Ligne de Pack'

    pack_id = fields.Many2one('pack.produit', string='Pack', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Produit', required=True)
    quantity = fields.Float(string='Quantité', default=1)
    price_unit = fields.Float(string='Prix Unitaire', store=True)
    image = fields.Binary(string='Image', attachment=True)
    category = fields.Many2one('product.category', string='Categorie')


    @api.onchange('product_id')
    def _onchange_product_id(self):
        """ Met à jour le prix unitaire en fonction du produit sélectionné. """

        if self.product_id:
            self.price_unit = self.product_id.list_price
            self.image = self.product_id.image_1920
            self.category = self.product_id.categ_id