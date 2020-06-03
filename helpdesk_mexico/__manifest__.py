# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Helpdesk (Gestión de solicitudes)",
    "author": "Soluciones SoftHard",
    "category": "Helpdesk",
    "website" : "http://www.solucionesofthard.com",
    "depends": ['helpdesk','payroll_mexico','website_helpdesk','website_helpdesk_form'],
    "data": [ 
            'security/helpdesk_security.xml',
	    'views/assets.xml',
	    'views/helpdesk_menu.xml',
            'views/helpdesk_ticket.xml',
            'views/helpdesk_portal_templates.xml',
            'data/helpdesk_data.xml',
            'data/website_helpdesk.xml',
            'data/mail_data.xml',
            'data/ir_cron_data.xml',
    ],
    'qweb': [
        "static/src/xml/helpdesk_team_templates.xml",
    ],
}

