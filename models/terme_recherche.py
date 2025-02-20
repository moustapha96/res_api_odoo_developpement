
from odoo import models, fields

class TermeRecherche(models.Model):
    _name = 'web.terme_recherche'
    _description = 'Terme de recherche sur le web'

    text = fields.Text(string='Text')
    date = fields.Datetime(string="Date d'envoie", default=fields.Datetime.now)
    source = fields.Char(string='Source')
    