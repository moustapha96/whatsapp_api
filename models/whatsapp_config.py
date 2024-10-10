from odoo import models, fields, api
import requests
import base64
import logging

_logger = logging.getLogger(__name__)

class WhatsAppConfig(models.Model):
    _name = 'whatsapp.api'
    _description = 'WhatsApp API Configuration'

    name = fields.Char(string='Name', required=True)
    phone_number_id = fields.Char(string='Phone Number ID', required=True)
    access_token = fields.Char(string='Access Token', required=True)
    base_url = fields.Char(string='Base URL', default='https://graph.facebook.com/v20.0/', required=True)

    def send_message(self, to, message_type, content, attachment=None, attachment_name=None):
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
        elif message_type in ["image", "document"]:
            if not attachment:
                raise ValueError("Attachment is required for image or document messages")
            
            # Upload the attachment to Facebook's servers
            upload_response = self._upload_attachment(attachment, attachment_name, message_type)
            if not upload_response.get('id'):
                raise ValueError("Failed to upload attachment")
            
            data[message_type] = {"id": upload_response['id']}
            if message_type == "document" and attachment_name:
                data[message_type]["filename"] = attachment_name

        try:
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error in WhatsApp API request: {str(e)}")
            raise

    def _upload_attachment(self, attachment, attachment_name, message_type):
        endpoint = f"{self.base_url}{self.phone_number_id}/media"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        files = {
            'file': (attachment_name, base64.b64decode(attachment), 'application/octet-stream')
        }
        data = {
            'messaging_product': 'whatsapp',
            'type': message_type
        }

        try:
            response = requests.post(endpoint, headers=headers, data=data, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Error uploading attachment: {str(e)}")
            raise

    def process_webhook(self, webhook_data):
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