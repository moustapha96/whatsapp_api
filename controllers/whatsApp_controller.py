
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppController(http.Controller):

    @http.route('/whatsapp/test', type='json', auth='public', csrf=False)
    def test_whatsapp_controller(self, **post):
        return {'status': 'success', 'message': 'WhatsApp controller is working'}

    @http.route('/whatsapp/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def whatsapp_webhook(self, **post):
        data = json.loads(request.httprequest.data)
        return request.env['whatsapp.api'].sudo().process_webhook(data)
    
    
    # @http.route('/whatsapp/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    # def whatsapp_webhook(self, **post):

    #     user = request.env['res.users'].sudo().browse(request.env.uid)
    #     if not user or user._is_public():
    #         admin_user = request.env.ref('base.user_admin')
    #         request.env = request.env(user=admin_user.id)

    #     try:
    #         data = json.loads(request.httprequest.data)
    #         whatsapp_api = request.env['whatsapp.api'].sudo().search([('is_active', '=', True)], limit=1)
    #         _logger.exception(f"arrive ", )
    #         if whatsapp_api:
    #             return whatsapp_api.process_webhook(data)
    #         return {'status': 'error', 'message': 'WhatsApp API not configured'}
    #     except Exception as e:
    #         _logger.exception("Error processing webhook: %s", str(e))
    #         return {'status': 'error', 'message': str(e)}
        

    @http.route('/whatsapp/send_message', type='json', auth='none', methods=['POST'], csrf=False)
    def send_whatsapp_message(self, **post):
        user = request.env['res.users'].sudo().browse(request.env.uid)
        if not user or user._is_public():
            admin_user = request.env.ref('base.user_admin')
            request.env = request.env(user=admin_user.id)
        try:
            whatsapp_api = request.env['whatsapp.api'].search([('is_active', '=', True)], limit=1)
            if not whatsapp_api:
                return {'error': 'WhatsApp API configuration not found'}
            
            data = json.loads(request.httprequest.data)
            to = data.get('to')
            message_type = data.get('type', 'text')
            content = data.get('content')
            
            if not to or not content:
                return {'error': 'Missing required parameters'}
            
            result = whatsapp_api.send_message(to, message_type, content, **post)
            return result
        except Exception as e:
            _logger.exception("Error sending WhatsApp message: %s", str(e))
            return {'error': str(e)}
        

    @http.route('/whatsapp/test_webhook', type='http', auth='none',methods=['GET'])
    def test_webhook(self, **kwargs):
        test_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "419455691258644",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "PHONE_NUMBER",
                            "phone_number_id": "PHONE_NUMBER_ID"
                        },
                        "contacts": [{
                            "profile": {
                            "name": "TEST USER"
                            },
                            "wa_id": "WHATSAPP_ID"
                        }],
                        "messages": [{
                            "from": "WHATSAPP_ID",
                            "id": "wamid.ID",
                            "timestamp": "1676056838",
                            "text": {
                            "body": "Hello, this is a test message"
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        result = self.whatsapp_webhook(**test_data)
        return json.dumps(result)
    

    @http.route('/whatsapp/send_template', type='json', auth='user')
    def send_whatsapp_template(self, **post):
        try:
            whatsapp_api = request.env['whatsapp.api'].search([('is_active', '=', True)], limit=1)
            if not whatsapp_api:
                return {'error': 'WhatsApp API configuration not found'}
            
            data = json.loads(request.httprequest.data)
            to = data.get('to')
            template_name = data.get('template_name')
            language_code = data.get('language_code', 'en_US')
            components = data.get('components', [])
            
            if not to or not template_name:
                return {'error': 'Missing required parameters'}
            
            result  = whatsapp_api.send_template_message(to, template_name, language_code, components)
            return result
        except Exception as e:
            _logger.exception("Error sending WhatsApp template message: %s", str(e))
            return {'error': str(e)}