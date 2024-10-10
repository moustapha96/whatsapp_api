from odoo import models, fields, api


class WhatsAppTemplate(models.Model):
    _name = 'whatsapp.template'
    _description = 'WhatsApp Message Template'

    name = fields.Char(string='Name', required=True)
    template_name = fields.Char(string='Template Name', required=True)
    language_code = fields.Char(string='Language Code', required=True, default='en_US')
    content = fields.Text(string='Content', required=True)