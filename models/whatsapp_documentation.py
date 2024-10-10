from odoo import models, fields # type: ignore

class WhatsAppDocumentation(models.Model):
    _name = 'whatsapp.documentation'
    _description = 'WhatsApp Integration Documentation'

    name = fields.Char(string='Title', required=True)
    content = fields.Html(string='Content', required=True)