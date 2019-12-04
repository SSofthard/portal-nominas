# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Incidents",
    "author": "Soluciones SoftHard",
    "category": "Employees",
    "website" : "http://www.solucionesofthard.com",
    "depends": ['web','hr','hr_holidays','payroll_mexico'],
    "data": [ 
            'report/hr_incidents_report.xml',
            'wizard/wizard_hr_incidents.xml',
            'wizard/hr_incidents_import_view.xml',
            'views/hr_incidents.xml',
            'data/incidents_data.xml',
            
    ],
}

