# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hr Employees Import Attendance',
    'category': 'Employees',
    'version': '12.0.0.1',
    'summary': 'Hr Employees Import Attendance',
    'author': 'Soluciones Softhard, C.A.',
    'website': 'http://www.solucionesofthard.com',
    'price': 0.0,
    'currency': 'EUR',
    'description': """
        Hr Employees Import Attendance
        Import Attendance
        Load attendance data
    """,
    'depends': ['hr_attendance'],
    'data': [
        'wizard/wizard_hr_attendance_import.xml',
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/tree_view_buttons.xml'
    ],
    'images': [
        'images/main_screenshot.png',
    ],
    'license': "OPL-1",
    'live_test_url': 'http://demo12.solucionesofthard.com',
    'installable': True,
    'auto_install': False,
    'application': False,
}

