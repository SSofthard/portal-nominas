# -*- coding: utf-8 -*-

{
    "name": "Dropdown Menu Apps Enterprise",
    "summary": "Dropdown Menu Apps Enterprise",
    "version": "12.0.1.0.0",
    "category": "web",
    "website": "https://solucionesofthard.com/",
    "description": """Dropdown Menu Apps for Odoo 12.0 enterprise edition.""",
    'images': ['static/description/banner.jpg'],
    'author': 'Soluciones Softhard',
    'company': 'Soluciones Softhard',
    'maintainer': 'Soluciones Softhard',
    "installable": True,
    "depends": [
        'web',
        'web_enterprise',
    ],
    "data": [
        'views/assets.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
