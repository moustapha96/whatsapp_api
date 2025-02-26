{
    'name': 'WhatsApp Integration fonctionnel',
    'version': '1.0',
    'category': 'Marketing',
    'summary': 'Integrate WhatsApp functionality in Odoo',
    'description': """
        This module integrates WhatsApp functionality in Odoo, including:
        - Sending and receiving WhatsApp messages
        - Customer satisfaction surveys
        - Restaurant order management
        - Appointment booking   
    """,
    'author': 'CCBM TECHNOLOGIES',
    'website': 'https://orbitcity.sn',
    'depends': ['base', 'mail', 'web'],
     'external_dependencies': {
        'python': ['simplejson'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_menu.xml',
        'views/whatsapp_documentation_views.xml',
        'data/whatsapp_documentation_data.xml',
        'views/whatsapp_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}