from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_1 = fields.Binary(string='Image 1', attachment=True)
    image_2 = fields.Binary(string='Image 2', attachment=True)
    image_3 = fields.Binary(string='Image 3', attachment=True)