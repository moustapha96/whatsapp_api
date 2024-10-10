from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppAPI(models.Model):
    _name = 'whatsapp.api'
    _description = 'WhatsApp API Configuration'

    name = fields.Char(string='Name', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    phone_number_id = fields.Char(string='Phone Number ID', required=True)
    access_token = fields.Char(string='Access Token', required=True)
    base_url = fields.Char(string='Base URL', default='https://graph.facebook.com/v20.0/', required=True)

    @api.model
    def create(self, vals):
        if vals.get('is_active'):
            self.search([]).write({'is_active': False})
        return super(WhatsAppAPI, self).create(vals)

    def write(self, vals):
        if vals.get('is_active'):
            self.search([('id', '!=', self.id)]).write({'is_active': False})
        return super(WhatsAppAPI, self).write(vals)

    def send_message(self, to, message_type, content, **kwargs):
        endpoint = f"{self.base_url}{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": message_type,
        }

        if message_type == "text":
            data["text"] = {"body": content}
        elif message_type == "image":
            data["image"] = {"link": content}
        elif message_type == "document":
            data["document"] = {"link": content, "caption": kwargs.get("caption")}
        elif message_type == "interactive":
            data["interactive"] = content

        try:
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error in WhatsApp API request: {str(e)}")
            return {"error": str(e)}

    @api.model
    def process_webhook(self, webhook_data):
        active_config = self.search([('is_active', '=', True)], limit=1)
        if not active_config:
            return {'status': 'error', 'message': 'No active WhatsApp API configuration'}

        return active_config._process_webhook(webhook_data)

    def _process_webhook(self, webhook_data):
        if webhook_data.get('object') == 'whatsapp_business_account':
            for entry in webhook_data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        messages = change.get('value', {}).get('messages', [])
                        for message in messages:
                            self._process_incoming_message(message)
        return {'status': 'success'}

    def _process_incoming_message(self, message):
        message_type = message.get('type')
        from_number = message.get('from')

        if message_type == 'text':
            text = message.get('text', {}).get('body')
            self.env['whatsapp.message'].create({
                'recipient_number': from_number,
                'message_type': 'text',
                'message_content': text,
                'state': 'received',
            })
        elif message_type == 'interactive':
            interactive_type = message.get('interactive', {}).get('type')
            if interactive_type == 'button_reply':
                button_reply = message.get('interactive', {}).get('button_reply', {})
                button_id = button_reply.get('id')
                button_text = button_reply.get('title')
                self.env['whatsapp.message'].create({
                    'recipient_number': from_number,
                    'message_type': 'interactive',
                    'message_content': f"Button: {button_text} (ID: {button_id})",
                    'state': 'received',
                })

        self.mark_message_as_read(message.get('id'))

    def mark_message_as_read(self, message_id):
        endpoint = f"{self.base_url}{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        try:
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error marking message as read: {str(e)}")
            return None