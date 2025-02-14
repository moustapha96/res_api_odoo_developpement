
from odoo import models, fields

class Comment(models.Model):
    _name = 'web.commentaire'
    _description = 'Commentaire'

    author = fields.Char(string='Author')
    text = fields.Text(string='Text')
    date = fields.Datetime(string="Date d'envoie", default=fields.Datetime.now)
    product_id = fields.Many2one('product.template', string='Product')
    review = fields.Integer(string='Review' , default=0)

class CommentaireSimple(models.Model):
    _name = 'web.commentaire.simple'
    _description = 'Commentaire Simple'

    author = fields.Char(string='Author')
    email = fields.Char(string='Email')  # Champ ajouté
    text = fields.Text(string='Text')
    date = fields.Datetime(string="Date d'envoie", default=fields.Datetime.now)