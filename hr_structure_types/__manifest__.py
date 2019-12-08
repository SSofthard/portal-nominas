# -*- coding: utf-8 -*-
{
    'name': "Multi Payroll Structure",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Soluciones Softhard C.A",
    'website': "http://www.solucionessofthard.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['base','hr_payroll','hr_contract', 'payroll_mexico'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/structure_type_views.xml',
        'views/hr_contract.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_payslip.xml',
        'wizard/hr_payroll_payslips_by_employees.xml',
        
    ],
    'demo': [
        'demo/demo.xml',
    ],
    "active": True,
    "installable": True,
}
