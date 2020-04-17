# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Incidents",
    "author": "Soluciones SoftHard",
    "category": "Employees",
    "website" : "http://www.solucionesofthard.com",
    "depends": ['web','hr','hr_holidays','payroll_mexico','hr_public_holiday'],
    "data": [ 
			'security/hr_holidays_security.xml',
            'security/ir.model.access.csv',
            'report/hr_incidents_report.xml',
            'report/report_inhability_absenteeism_template.xml',
            'wizard/wizard_hr_incidents.xml',
            'wizard/hr_incidents_import_view.xml',
            'wizard/inhabilities_absenteeism_report_view.xml',
            'views/laboral_inhability_view.xml',
            'views/hr_incidents.xml',
            'data/incidents_data.xml',
            'data/inhability_data.xml',
            
    ],
}

