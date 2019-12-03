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
        'wizard/hr_employee_contract_wizard.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract.xml',
        'views/hr_contract_type.xml',
        'views/hr_payslip.xml',
        'views/res_company_view.xml',
        'views/table_cfdi_view.xml',
        'views/res_config_settings_views.xml',
        'views/hr_holidays.xml',
        'security/ir.model.access.csv',
        #Reports
        'report/base_layout.xml',
        'report/indeterminate_contract_without_seniority.xml',
        'report/determinate_contract_without_seniority.xml',
        'report/indeterminate_contract_with_seniority.xml',
        'report/determinate_contract_with_seniority.xml',
        'report/independent_services_provision_agreement.xml',
        'data/data.xml',
        'data/sequence_data.xml',
        'data/data_table_cfdi.xml',
        'data/res.bank.csv',
        'data/payroll_data.xml',
        # ~ 'data/data_hr_perceptions.xml',
        
    ],
    "active": True,
    "installable": True,
}