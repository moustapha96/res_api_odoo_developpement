from odoo import  fields, models, _

class Company(models.Model):
    
    _inherit = 'res.company'

    entreprise_code = fields.Char(string='Code Entreprise',  required=False)
    hr_email = fields.Char(string="Email RH")