from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    def send_welcome_email(self):
        mail_template = self.env['mail.template'].sudo().search([('id', '=', 4)], limit=1)
        if not mail_template:
            raise ValueError("Mail template not found")

        for user in self:
            email_values = mail_template.generate_email([user.id], fields=['email_from', 'email_to', 'subject', 'body_html'])
            mail_mail = self.env['mail.mail'].sudo().create(email_values[user.id])
            mail_mail.send()

    @api.model
    def create(self, vals):
        user = super(ResUsers, self).create(vals)
        user.send_welcome_email()
        return user
