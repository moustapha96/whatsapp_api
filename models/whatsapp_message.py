from odoo import models, fields, api

class WhatsAppMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message'
    _order = 'create_date desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    recipient_number = fields.Char(string='Recipient Number', required=True)
    message_type = fields.Selection([
        ('text', 'Text'),
        ('image', 'Image'),
        ('document', 'Document'),
        ('interactive', 'Interactive')
    ], string='Message Type', default='text', required=True)
    message_content = fields.Text(string='Message Content', required=True)
    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char(string='Attachment Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('error', 'Error')
    ], string='State', default='draft')
    error_message = fields.Text(string='Error Message')

    @api.depends('recipient_number', 'create_date')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.recipient_number} - {record.create_date.strftime('%Y-%m-%d %H:%M:%S')}"

    def action_send_message(self):
        self.ensure_one()
        whatsapp_api = self.env['whatsapp.api'].search([], limit=1)
        if not whatsapp_api:
            self.write({'state': 'error', 'error_message': 'WhatsApp API not configured'})
            return

        try:
            result = whatsapp_api.send_message(
                self.recipient_number,
                self.message_type,
                self.message_content,
                attachment=self.attachment,
                attachment_name=self.attachment_name
            )
            if result.get('messages'):
                self.write({'state': 'sent'})
            else:
                self.write({'state': 'error', 'error_message': 'Failed to send message'})
        except Exception as e:
            self.write({'state': 'error', 'error_message': str(e)})

        return True