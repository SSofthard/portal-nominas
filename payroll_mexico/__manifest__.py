# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Customization of the human resources process for Mexico.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module that adapts Mexico's own characteristics of the human resources process.",
    'summary': "Module that adapts Mexico's own characteristics of the human resources process.",
    "depends": ['base','hr_attendance','hr_payroll','resource','hr_holidays','hr'],
    "data": [
        'views/hr_employee_view.xml',
        'views/hr_contract.xml',
        'views/res_company_view.xml',
        'data/data.xml',
        'data/res.bank.csv',
        'security/ir.model.access.csv',
    ],
    "active": True,
    "installable": True,
}
