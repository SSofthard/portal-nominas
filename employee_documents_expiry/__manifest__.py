# -*- coding: utf-8 -*-

{
    'name': 'Employee Documents',
    'version': '12.0.1.0.0',
    'summary': "Management of employee documents and notification when it expires..",
    'description': "Management of employee documents and notification when it expires.",
    'category': 'Human Resources',
    'author': '',
    'license': '',
    'website': "",
    'depends': ['base', 'hr','hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_document_view.xml',
        'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
