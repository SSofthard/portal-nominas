# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Management of loans for employees.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module for the management and control of loans approved to employees of the company.",
    'summary': "Module for the management and control of loans approved to employees of the company.",
    "depends": ['base','hr','hr_payroll'],
    "data": [
        'views/hr_loan_employeee.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        #Reports
        'report/base_layout.xml',
        'report/hr_loan_application.xml',
    ],
    "active": True,
    "installable": True,
}
