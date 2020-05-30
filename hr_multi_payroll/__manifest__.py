# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Multi Payroll",
    "author": "JUVENTUD PRODUCTIVA VENEZOLANA",
    "category": "Human Resources",
    "website" : "https://www.youtube.com/channel/UCTj66IUz5M-QV15Mtbx_7yg",
    "description": "This module expands the functionalities of the payroll module to allow calculating different salary structures for an employee.",
    'summary': 'This module expands the functionalities of the payroll module to allow calculating different salary structures for an employee.',
    "depends": ['web','hr_payroll'],
    "data": [ 
        'wizard/hr_payroll_payslips_by_employees.xml',
        'views/payroll_structure_type_views.xml',
        'views/hr_contract.xml',
        'views/hr_payslip.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/images/attendance_screenshot.png'],
    "active": True,
    "installable": True,
    'currency': 'EUR',
    'price': 40.00,
}

