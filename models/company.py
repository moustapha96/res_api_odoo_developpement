from odoo import  fields, models, _

class Partner(models.Model):
    _inherit = 'res.company'

    entreprise_code = fields.Char(string='Code entreprise', required=False)
    # hr_email = fields.Char(string="Email RH")
