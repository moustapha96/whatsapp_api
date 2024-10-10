from odoo import models, fields, api

class RestaurantOrder(models.Model):
    _name = 'restaurant.order'
    _description = 'Restaurant Order'

    name = fields.Char(string='Order Reference', required=True)
    customer_id = fields.Many2one('res.partner', string='Customer')
    phone_number = fields.Char(related='customer_id.phone', string='Phone Number')
    order_items = fields.One2many('restaurant.order.item', 'order_id', string='Order Items')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft')

    def send_menu(self):
        whatsapp_api = self.env['whatsapp.api'].search([], limit=1)
        if not whatsapp_api:
            return {'error': 'WhatsApp API not configured'}

        menu_items = self.env['restaurant.menu.item'].search([])
        buttons = [
            {"type": "reply", "reply": {"id": f"item_{item.id}", "title": item.name}}
            for item in menu_items[:3]  # WhatsApp limits to 3 buttons
        ]

        content = "Here's our menu. Please choose an item:"
        result = whatsapp_api.send_message(
            self.phone_number,
            'interactive',
            content,
            buttons=buttons
        )
        return result

    def process_order(self, customer_phone, order_id, order_item):
        order = self.search([('id', '=', order_id), ('phone_number', '=', customer_phone)], limit=1)
        if not order:
            return {'error': 'Order not found'}

        menu_item = self.env['restaurant.menu.item'].search([('id', '=', int(order_item.split('_')[1]))], limit=1)
        if menu_item:
            self.env['restaurant.order.item'].create({
                'order_id': order.id,
                'menu_item_id': menu_item.id,
                'quantity': 1
            })
            return {'status': 'success', 'message': 'Order item added'}
        else:
            return {'error': 'Menu item not found'}

class RestaurantMenuItem(models.Model):
    _name = 'restaurant.menu.item'
    _description = 'Restaurant Menu Item'

    name = fields.Char(string='Item Name', required=True)
    price = fields.Float(string='Price')

class RestaurantOrderItem(models.Model):
    _name = 'restaurant.order.item'
    _description = 'Restaurant Order Item'

    order_id = fields.Many2one('restaurant.order', string='Order')
    menu_item_id = fields.Many2one('restaurant.menu.item', string='Menu Item')
    quantity = fields.Integer(string='Quantity', default=1)