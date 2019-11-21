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
        if not report:
            msg="The type of contract does not have an assigned report"
            raise  UserError(_(msg))
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
        domain=[
                ('employee_id','=',employee.id),
                ('state','in',['cloese'])
                ]
        date_start=self.date_start
        record=self.search_read(domain,['date_start'],limit=1,order="id asc")
        if record:
            date_start=record[0]['date_start']
        data={
            'type':self.type_id.name.upper(),
            'company_name':"por bucar",
            'company_addres':"por bucar",
            'company_public': "por buscar",
            'public_notary':"por buscar",
            'representative_public_notary':"por buscar",
            'number_public_notary':"por buscar",
            'city_public_notary':"por buscar",
            'patron':"por bucar",
            'mr_patron':"por buscar",
            'mr_employee':mr_employee[employee.gender],
            'employee':employee.name.upper(),
            'job_position':employee.job_id.name or " ",
            'nationality':employee.country_id.name,
            'old':"por buscar",
            'gender':employee.gender,
            'marital':employee.marital,
            'originative':"por buscar",
            'employee_birthday':empl_birthday,
            'employee_address_home':"Por buscar",
            'employee_curp':employee.curp,
            'patron_rfc':employee.rfc,
            'employee_nss':employee.social_security_number,
            'employee_dress':employee.address_home_id.contact_address,
            'job_dress':"por buscar",
            'date_first_contract':date_start.strftime('día %d del mes de %B de %Y'),
            'date_contract':self.date_start.strftime('%d dias del mes de %B de %Y')
            }
        return report.report_action(self.ids, data=data)

