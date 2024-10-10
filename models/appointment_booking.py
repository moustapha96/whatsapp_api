from odoo import models, fields, api
from datetime import datetime, timedelta

class AppointmentBooking(models.Model):
    _name = 'appointment.booking'
    _description = 'Appointment Booking'

    name = fields.Char(string='Appointment Reference', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    phone_number = fields.Char(related='customer_id.phone', string='Phone Number')
    date = fields.Datetime(string='Appointment Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft')

    def send_appointment_options(self):
        whatsapp_api = self.env['whatsapp.api'].search([], limit=1)
        if not whatsapp_api:
            return {'error': 'WhatsApp API not configured'}

        today = datetime.now()
        options = [today + timedelta(days=i) for i in range(1, 4)]
        buttons = [
            {"type": "reply", "reply": {"id": f"date_{date.strftime('%Y-%m-%d')}", "title": date.strftime('%d/%m/%Y')}}
            for date in options
        ]

        content = "Please choose an appointment date:"
        result = whatsapp_api.send_message(
            self.phone_number,
            'interactive',
            content,
            buttons=buttons
        )
        return result

    def process_appointment_selection(self, customer_phone, appointment_id, appointment_date):
        appointment = self.search([('id', '=', appointment_id), ('phone_number', '=', customer_phone)], limit=1)
        if not appointment:
            return {'error': 'Appointment not found'}

        appointment.date = datetime.strptime(appointment_date, '%Y-%m-%d')
        appointment.state = 'confirmed'
        return {'status': 'success', 'message': 'Appointment confirmed'}

    def process_reminder_response(self, customer_phone, reminder_choice):
        appointment = self.search([('phone_number', '=', customer_phone), ('state', '=', 'confirmed')], limit=1)
        if not appointment:
            return {'error': 'No confirmed appointment found'}

        if reminder_choice == 'confirm':
            appointment.state = 'done'
            return {'status': 'success', 'message': 'Appointment confirmed'}
        elif reminder_choice == 'reschedule':
            return self.send_appointment_options()
        else:
            return {'error': 'Invalid choice'}