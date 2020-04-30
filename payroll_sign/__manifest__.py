# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Integration of the sign module with payroll.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module that adapts sign process for payroll documents.",
    'summary': "Module that adapts sign process for payroll documents.",
    "depends": ['base','payroll_mexico','sign','website'],
    "data": [
    'views/hr_payslip.xml',
    'templates/payslip_sign_templates.xml'
    ],
    "active": True,
    "installable": True,
}
