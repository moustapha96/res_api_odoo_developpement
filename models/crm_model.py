# crm.lead
from odoo import api, fields, models, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    date_maj = fields.Datetime(string="Date de mise à jour", default=fields.Datetime.now, help="La date de dernière mise à jour")
    lead_line_ids = fields.One2many('crm.lead.line', 'lead_id', string='Lead Lines')
    



class CrmLeadLine(models.Model):
    _name = 'crm.lead.line'
    _description = 'CRM Lead Line'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    products = fields.Text(string='Products', required=False)
    date = fields.Datetime(string="Date du panier", default=fields.Datetime.now, help="La date de création du panier")
    amount = fields.Float(string='Amount', required=True)
    type = fields.Selection([
        ('commande', 'Commande'),
        ('precommande', 'Précommande'),
        ('acredit', 'A crédit'),
    ], string='Type', required=True , default='commande')
