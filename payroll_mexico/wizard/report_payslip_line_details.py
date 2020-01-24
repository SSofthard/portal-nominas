# -*- coding: utf-8 -*-

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

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class PayslipLineDetails(models.TransientModel):
    _name = 'hr.payslip.line.details'
    _description = 'Detalles de las reglas de negocio'

    #Columns
    date_from = fields.Date(
        'Start Date', index=True, copy=False, required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(
        'End Date', index=True, copy=False, required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    contracting_regime = fields.Selection([
        # ('01', 'Assimilated to wages'),
        ('02', 'Wages and salaries'),
        ('03', 'Senior citizens'),
        ('04', 'Pensioners'),
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
        ], string='Contracting Regime', default='02')
    rule_id = fields.Many2one('hr.salary.rule', index=True,  required=True, string='Regla de negocio')

    @api.multi
    def report_print(self, data):
        lines = {}
        line_data = {}
        
        self.ensure_one()
        domain = [('slip_id.date_from','>=',self.date_from),('slip_id.date_to','<=',self.date_to)]
        if self.employee_id:
            domain += [('employee_id','=',self.employee_id.id)]
        if self.contracting_regime:
            domain += [('slip_id.contract_id.contracting_regime','=',self.contracting_regime)]
        if self.rule_id:
            domain += [('salary_rule_id','=',self.rule_id.id)]
        line_ids = self.env['hr.payslip.line'].search(domain)
        if not line_ids:
            raise ValidationError(_('No se encontró información con los datos proporcionados.'))
        employees_ids = line_ids.mapped('employee_id')
        line_data = []
        total = 0
        for line in line_ids:
            total += line.total
            line_data.append({
                'enrollment': line.employee_id.enrollment,
                'employee_name': line.employee_id.name_get()[0][1],
                'contracting_regime': line.slip_id.contract_id.contracting_regime, #dict(line.slip_id.contract_id._fields['contracting_regime']._description_selection(line.slip_id.contract_id.env)).get(line.slip_id.contract_id.contracting_regime),
                'reference': line.slip_id.number,
                'linename': line.name,
                'date_from': line.slip_id.date_from,
                'date_to': line.slip_id.date_to,
                'total': line.total,
            })
        lines['employees'] = line_data
        lines['date_from'] = self.date_from
        lines['date_to'] = self.date_to
        lines['total'] = total
        data={
            'lines_data':lines
        }
        return self.env.ref('payroll_mexico.action_report_payslip_line').with_context(from_transient_model=True).report_action(self, data=data)
