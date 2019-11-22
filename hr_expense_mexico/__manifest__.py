# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Customization of the expenses request process for Mexico.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module that adapts Mexico's own characteristics of the expenses process.",
    'summary': "Module that adapts Mexico's own characteristics of the human resources process.",
    "depends": ['base','hr_attendance','hr_payroll','resource','hr_holidays','hr','employee_documents_expiry'],
    "data": [
        'wizards/amount_approve_expense_sheet.xml',
        'wizards/wizard_add_tag_documents.xml',
        'views/hr_expenses.xml',
        # 'security/ir.model.access.csv'
    ],
    "active": True,
    "installable": True,
}

