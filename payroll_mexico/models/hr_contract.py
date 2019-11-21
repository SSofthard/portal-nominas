# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Contract(models.Model):

    _inherit = 'hr.contract'

    code = fields.Char('Code', default="HOLA",required=True)
    type_id = fields.Many2one(string="Type Contract")
    productivity_bonus = fields.Float('Productivity bonus', required=False)
    attendance_bonus = fields.Float('Attendance bonus', required=False)
    punctuality_bonus = fields.Float('Punctuality Bonds', required=False)
    social_security = fields.Float('Social security', required=False)
    
    def print_contract(self):
        report=self.type_id.report_id
        employee=self.employee_id
        empl_birthday="Sin Fecha"
        if employee.birthday:
            format = ("%d/%m/%Y")
            empl_birthday = employee.birthday.strftime(format)
        mr_patron={
                'male':_('Mr'),
                'female':_('Mrs'),
                }
        mr_employee={
                'male':'EL SEÑOR',
                'female':'LA SEÑORA',
                }
        data={
            'type':self.type_id.name.upper(),
            'company_name':"por bucar",
            'company_addres':"por bucar",
            'patron':"por bucar",
            'mr_patron':"por buscar",
            'mr_employee':mr_employee[employee.gender],
            'employee':employee.name.upper(),
            'job_position':employee.job_id.name or " ",
            'nationality':employee.country_id.name,
            'old':"por buscar",
            'gender':employee.gender,
            'marital':employee.marital,
            'employee_crup':employee.curp,
            'patron_rfc':employee.rfc,
            'employee_nss':"por buscar",
            'employee_dress':"por buscar",
            'job_dress':"por buscar",
            'date_first_contract':"por buscar",
            'date_contract':"por buscar",
            'originative':"por buscar",
            'employee_birthday':empl_birthday,
            'employee_address_home':"Por buscar",
            }
        return report.report_action(self.ids, data=data)

