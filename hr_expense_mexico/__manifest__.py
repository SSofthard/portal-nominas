# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Customization of the expenses request process for Mexico.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module that adapts Mexico's own characteristics of the expenses process.",
    'summary': "Module that adapts Mexico's own characteristics of the human resources process.",
    "depends": ['base','hr_expense','employee_documents_expiry'],
    "data": [
        'security/ir.model.access.csv',
        'wizards/wizard_add_tag_documents.xml',
        'wizards/refused_expense_wizard.xml',
        'wizards/hr_expense_sheet_register_payment.xml',
        'data/ir_sequence_data.xml',
        'report/hr_expense_report.xml',
        'views/hr_expenses_payment.xml',
        'views/hr_expenses.xml',
        # 'security/ir.model.access.csv'
    ],
    "active": True,
    "installable": True,
}

