# crm.lead
from odoo import api, fields, models, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'


    # date_maj = fields.Datetime(string="Date Mise à jour", default=fields.Datetime.now, copy=False, readonly=False)

    date_maj = fields.Datetime(string="Date de mise à jour", default=fields.Datetime.now, help="La date de dernière mise à jour")
    
    # @api.model
    # def write(self, vals):
    #     vals['date_maj'] = fields.Datetime.now()
    #     return super(CrmLead, self).write(vals)
