# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Customization of the human resources process for Mexico.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module that adapts Mexico's own characteristics of the human resources process.",
    'summary': "Module that adapts Mexico's own characteristics of the human resources process.",
    "depends": ['base','hr_attendance','hr_payroll','resource','hr_holidays','hr','employee_documents_expiry'],
    "data": [
        'data/data.xml',
        'data/res.bank.csv',
        'views/hr_employee_view.xml',
        'views/hr_contract.xml',
        'views/hr_contract_type.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
        #Reports
        'report/internal_layout.xml',
        'report/contract_without_seniority.xml',
        'report/contract_with_seniority.xml',
        'report/independent_services_provision_agreement.xml'
        
    ],
    "active": True,
    "installable": True,
}
