# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    # Theme information
    'name': 'Payroll Mexico Theme',
    'description': 'Custom Themes for Mexico Payroll Portal',
    'category': 'Theme',
    'summary': 'Module Ositech Payroll themes.',
    'version': '12.0.0.1',
    'license': 'OPL-1',	
    'depends': [
        'web',
        'website',
        'website_theme_install',
        'web_enterprise',
        'odoo_web_login',
    ],
    'data': [
        'views/menu.xml',
        'data/theme_data.xml',
        'views/assets.xml',
        'views/webclient_templates.xml',
        'views/website_templates.xml',
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
