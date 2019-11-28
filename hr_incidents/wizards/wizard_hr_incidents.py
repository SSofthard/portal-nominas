import xlsxwriter
import base64
import logging
import psycopg2
import pandas as pd
import io
import pytz
import xlwt
import os

from xlrd import open_workbook
from datetime import datetime

from odoo import api, fields, models, _
from dateutil.parser import parse
from odoo.osv import expression
from odoo.tools import pycompat
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardImportIncidents(models.TransientModel):
    _name = "wizard.hr.incidents"

    date_from = fields.Datetime('Start Date', required=True)
    date_to = fields.Datetime('End Date', required=True)
    employee_ids = fields.Many2many('hr.employee', 'employee_incidents_rel','employee_id', 'hr_incidents_id',string='Employee')
    holiday_status_ids = fields.Many2many('hr.leave.type', 'holidar_incidents_rel', 'holiday_status_id', 'hr_incidents_id', string='Leave Type')
    
    @api.multi
    def report_print(self, data):
        date_from = self.date_from
        date_to = self.date_to
        domain = []
        domain_type = []
        list_type = []
        list_date_from = []
        list_date_to = []
        list_name = []
        list_duration = []
        leave=self.env['hr.leave']
        if self.employee_ids:
            domain = [('employee_id', 'in', self.employee_ids.ids)]
        if self.holiday_status_ids:
            domain_type = [('holiday_status_id', 'in', self.holiday_status_ids.ids)]
        leave_ids=leave.search([('date_from','>=',date_from),('date_to','<=',date_to)] + domain + domain_type)
        for i in leave_ids:
            type_leave = (i.holiday_status_id.name)
            date_from = (date_from)
            date_to = (date_to)
            name = (i.employee_id.name)
            duration=(i.number_of_days_display)
            list_type.append(type_leave)
            list_date_from.append(date_from)
            list_date_to.append(date_to)
            list_name.append(name)
            list_duration.append(duration)
        data['type_leave'] = list_type
        data['name'] = sorted(list_name)
        data['duration'] = list_duration
        data['date_from'] = date_from
        data['date_to'] = date_to
        return self.env.ref('hr_incidents.report_hr_leave_incidents').report_action(self, data=data)
        
        
        
    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))
