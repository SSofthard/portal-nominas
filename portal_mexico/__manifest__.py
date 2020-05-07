# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    # Theme information
    'name': 'Portal Mexico Module',
    'description': 'Custom module for Mexico Payroll Portal',
    'category': 'website',
    'summary': 'Module Ositech Payroll themes.',
    'version': '12.0.0.1',
    'license': 'OPL-1',	
    'depends': ['portal'],
    'data': [
        'views/assets.xml',
        'views/website_portal_templates.xml',
    ],
    'qweb': [
        # ~ 'views/menu.xml',
    ],
    #Odoo Store Specific
    'images': [
        'static/description/bootswatch.png',
    ],
    # Technical
    'installable': True,
    'auto_install': False,
}
