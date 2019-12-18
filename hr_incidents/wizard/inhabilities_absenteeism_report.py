# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import datetime
import calendar
import pytz
import dateutil
import base64


from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo.tools.mimetypes import guess_mimetype
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, pycompat
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY


class InhabilityAbsenteeismReport(models.TransientModel):
    _name = "hr.leave.inhability.absenteeism.wizard"
    _description = "Inabilities & Absenteeism"

    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id)
    group_id = fields.Many2one('hr.group', "Group", required=True)
    employer_register_id = fields.Many2one('res.employer.register', "Employer Register", required=False)
    department_ids = fields.Many2many('hr.department', 'hr_leave_inhability_dept_rel', 'inhability_id', 'dept_id', string='Department(s)')
    job_ids = fields.Many2many('hr.job', 'hr_leave_inhability_job_rel', 'inhability_id', 'job_id', string='Job Position')
    date_from = fields.Date(
        'Start Date', index=True, copy=False, required=True,
        default=date.today())
    date_to = fields.Date(
        'End Date', index=True, copy=False, required=True,
        default=date.today())

    @api.multi
    def report_print(self, data):
        leaves = {}
        employee_data = {}
        
        self.ensure_one()
        domain = [('employee_id.group_id','=',self.group_id.id),('request_date_from','>=',self.date_from),('request_date_to','<=',self.date_to)]
        if self.department_ids:
            domain += [('employee_id.department_id','in',self.department_ids.ids)]
        if self.job_ids:
            domain += [('employee_id.department_id','in',self.job_ids.ids)]
            domain += [('employee_id.employer_register_id','=',self.employer_register_id.id)]
        leaves_ids = self.env['hr.leave'].search(domain)
        if not leaves_ids:
            raise ValidationError(_('No se encontraron resultados, para los parámetros.'))
        employees_ids = leaves_ids.mapped('employee_id')
        for employee in employees_ids:
            leaves_data = []
            for leave in leaves_ids:
                if employee.id == leave.employee_id.id:
                    leaves_data.append({
                        'type_inhability': leave.type_inhability_id.code,
                        'folio': leave.folio,
                        'duration': leave.number_of_days,
                        'request_date_from': leave.request_date_from,
                        'request_date_to': leave.request_date_to,
                        'holiday_status_id': dict(leave._fields['time_type']._description_selection(self.env)).get(leave.holiday_status_id.time_type),
                        'type_inhability_id': leave.type_inhability_id.name or '',
                        'inhability_classification_id': leave.inhability_classification_id.name or '',
                        'inhability_category_id': leave.inhability_category_id.name or '',
                        'inhability_subcategory_id': leave.inhability_subcategory_id.name or '',
                    })
            employee_data[employee.id] = {
                'enrollment': employee.enrollment,
                'ssnid': employee.ssnid,
                'name': employee.name_get()[0][1],
                'rfc': employee.rfc,
                'curp': employee.curp,
                'date_admission': self.env['hr.contract'].search([('employee_id','=',employee.id),('contracting_regime','=','2')], limit=1).date_start or '',
                'leave': leaves_data,
            }
        
        leaves['date_from'] = self.date_from
        leaves['date_to'] = self.date_to
        leaves['employer_register_id'] = self.employer_register_id.employer_registry.upper() if self.employer_register_id else ''
        leaves['company'] = self.employer_register_id.company_id.business_name
        leaves['rfc'] = self.employer_register_id.company_id.rfc
        leaves['total_employees'] = len(employees_ids)
        leaves['employee_data'] = employee_data
        data={
            'leaves_data':leaves
        }
        return self.env.ref('hr_incidents.action_report_inhability_absenteeism').with_context(from_transient_model=True).report_action(self, data=data)
