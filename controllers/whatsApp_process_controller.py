from odoo import http # type: ignore
from odoo.http import request # type: ignore
import json
import logging

_logger = logging.getLogger(__name__)
class WhatsAppProcessController(http.Controller):
    
    def process_webhook(self, webhook_data):
        if webhook_data.get('object') == 'whatsapp_business_account':
            for entry in webhook_data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        messages = change.get('value', {}).get('messages', [])
                        for message in messages:
                            if message.get('type') == 'text':
                                self._process_text_message(message)
        return {'status': 'success'}

    def _process_text_message(self, message):
        from_number = message.get('from')
        text = message.get('text', {}).get('body')
        
        # Créer un enregistrement du message
        self.env['whatsapp.message'].create({
            'phone_number': from_number,
            'message_type': 'text',
            'content': text,
        })
        
        # Exemple de logique de traitement
        if "commande" in text.lower():
            self._handle_order_inquiry(from_number, text)
        elif "support" in text.lower():
            self._handle_support_request(from_number, text)
        
        # Marquer le message comme lu
        self.mark_message_as_read(message.get('id'))



    def _process_interactive_message(self, message):
        from_number = message.get('from')
        interactive = message.get('interactive', {})
        
        if interactive.get('type') == 'button_reply':
            button_reply = interactive.get('button_reply', {})
            button_id = button_reply.get('id')
            button_text = button_reply.get('title')
            
            # Créer un enregistrement du message
            self.env['whatsapp.message'].create({
                'phone_number': from_number,
                'message_type': 'interactive',
                'content': f"Button: {button_text} (ID: {button_id})",
            })
            
            # Exemple de logique de traitement basée sur l'ID du bouton
            if button_id == 'confirm_order':
                self._process_order_confirmation(from_number)
            elif button_id == 'cancel_order':
                self._process_order_cancellation(from_number)
        
        # Marquer le message comme lu
        self.mark_message_as_read(message.get('id'))



  

    def _process_image_message(self, message):
        from_number = message.get('from')
        image = message.get('image', {})
        image_id = image.get('id')
        mime_type = image.get('mime_type')
        
        # Créer un enregistrement du message
        self.env['whatsapp.message'].create({
            'phone_number': from_number,
            'message_type': 'image',
            'content': f"Image received (ID: {image_id}, Type: {mime_type})",
        })
        
        # Exemple de logique de traitement
        self._download_and_process_image(image_id, from_number)
        
        # Marquer le message comme lu
        self.mark_message_as_read(message.get('id'))

    
   

    def _process_document_message(self, message):
        from_number = message.get('from')
        document = message.get('document', {})
        document_id = document.get('id')
        filename = document.get('filename')
        mime_type = document.get('mime_type')
        
        # Créer un enregistrement du message
        self.env['whatsapp.message'].create({
            'phone_number': from_number,
            'message_type': 'document',
            'content': f"Document received (ID: {document_id}, Filename: {filename}, Type: {mime_type})",
        })
        self._download_and_process_document(document_id, filename, from_number)
        self.mark_message_as_read(message.get('id'))