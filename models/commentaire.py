# my_module/models/comment.py
from odoo import models, fields

class Comment(models.Model):
    _name = 'web.commentaire'
    _description = 'Commentaire'

    author = fields.Char(string='Author')
    text = fields.Text(string='Text')
    date = fields.Datetime(string="Date d'envoie", default=fields.Datetime.now)
    