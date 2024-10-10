from odoo import models, fields, api

class SatisfactionSurvey(models.Model):
    _name = 'satisfaction.survey'
    _description = 'Satisfaction Survey'

    name = fields.Char(string='Survey Name', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    phone_number = fields.Char(related='customer_id.phone', string='Phone Number')
    rating = fields.Selection([
        ('1', 'Very Unsatisfied'),
        ('2', 'Unsatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied')
    ], string='Rating')

    def send_survey(self):
        whatsapp_api = self.env['whatsapp.api'].search([], limit=1)
        if not whatsapp_api:
            return {'error': 'WhatsApp API not configured'}

        buttons = [
            {"type": "reply", "reply": {"id": f"rating_{i}", "title": str(i)}}
            for i in range(1, 6)
        ]

        content = f"Dear {self.customer_id.name},\n\nPlease rate your satisfaction from 1 to 5:"
        result = whatsapp_api.send_message(
            self.phone_number,
            'interactive',
            content,
            buttons=buttons
        )
        return result

    def process_survey_response(self, customer_phone, rating_id, rating_title):
        survey = self.search([('phone_number', '=', customer_phone)], limit=1)
        if not survey:
            return {'error': 'Survey not found'}

        survey.rating = rating_title
        return {'status': 'success', 'message': 'Survey response recorded'}