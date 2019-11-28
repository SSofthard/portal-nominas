# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Incidents",
    "author": "Soluciones SoftHard",
    "category": "Hr",
    "website" : "http://www.solucionesofthard.com",
    "depends": ['web','hr','hr_holidays'],
    "data": [ 
            'report/hr_incidents_report.xml',
            'wizards/wizard_hr_incidents.xml',
            'views/hr_incidents.xml',
            
    ],
}

