# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name" : "Customization of the human resources process for Mexico.",
    "author": "OSITECH",
    "category": "Human Resources",
    "website" : "",
    "description": "Module that adapts Mexico's own characteristics of the human resources process.",
    'summary': "Module that adapts Mexico's own characteristics of the human resources process.",
    "depends": ['base','account','hr_attendance','hr_payroll','hr_holidays','hr','employee_documents_expiry','web'],
    "data": [
        'wizard/payroll_report_excel_view.xml',
        'wizard/report_payslip_line_details_view.xml',
        'wizard/report_payslip_run_rule_details_view.xml',
        'wizard/hr_update_fonacot_wizard.xml',
        'wizard/hr_employee_contract_wizard.xml',
        'wizard/wizard_expired_contracts.xml',
        'wizard/wizard_employee_catalogs.xml',
        'wizard/infonavit_view.xml',
        'wizard/fees_settlement_report_txt_view.xml',
        'wizard/hr_payroll_payslips_by_employees.xml',
        'views/res_country_view.xml',
        'views/hr_employee_view.xml',
        'wizard/wizard_affiliate_move_view.xml',
        'wizard/employee_change_view.xml',
        'views/hr_employe_history_view.xml',
        'views/hr_contract.xml',
        'views/hr_contract_type.xml',
        'views/structure_type_views.xml',
        'views/hr_payslip.xml',
        'wizard/wizard_infonavit_employee.xml',
        'wizard/report_payroll_summary_view.xml',
        'wizard/wizard_compute_sdi_vars.xml',
        'views/res_company_view.xml',
        'views/table_settings.xml',
        'views/res_config_settings_views.xml',
        'views/hr_holidays.xml',
        'views/hr_isn_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/payroll_report_excel_view.xml',
        'views/hr_settlement.xml',
        'views/table_antiguedades_view.xml',
        'views/hr_fees_settlement_view.xml',
        'views/hr_table_index_consume_price_view.xml',
        'security/ir.model.access.csv',
        #Reports
        
        'report/base_layout.xml',
        'report/report_payslip_line_template.xml',
        'report/indeterminate_contract_without_seniority.xml',
        'report/determinate_contract_without_seniority.xml',
        'report/indeterminate_contract_with_seniority.xml',
        'report/determinate_contract_with_seniority.xml',
        'report/independent_services_provision_agreement.xml',
        'report/payslip_run_report.xml',
        'report/payroll_deposit_report_template.xml',
        'report/fault_report_template.xml',
        'report/report_rule_details_template.xml',
        'report/expired_contracts_report.xml',
        'report/report_settlement_template.xml',
        'report/employee_catalogs.xml',
        'report/infonavit_employee_report.xml',
        'report/report_employee.xml',
        'report/employee_history_report.xml',
        'report/infonavit_employee_amount_report.xml',
        'report/fee_settlement_report.xml',
        'report/report_employee_catalogs.xml',
        'report/report_payroll_summary_template.xml',
        'report/report_affiliate_movements_template.xml',
        'report/report_payroll_receipt_template.xml',
        'report/report_payroll_receipt_timbrado_template.xml',
        'report/fee_imss_employee_report.xml',
        'report/report_payroll_cfdi.xml',
        'report/report_template.xml',
        'data/data.xml',
        'data/sequence_data.xml',
        # 'data/data_table_cfdi.xml',
        'data/data_table_setting.xml',
        'data/res.bank.csv',
        # ~ 'data/payroll_data.xml',
        'data/data_rule_salary.xml',
        'data/data_isn.xml',
        'data/data_ir_export_employee.xml',
        'data/res.country.state.municipality.csv',
        'data/res.municipality.zone.csv',
        'data/data_delegacion.xml',
        'data/data_inpc.xml',
        'data/data_sector_economico.xml',
        # ~ 'data/data_hr_perceptions.xml',
        
    ],
    "active": True,
    "installable": True,
}
