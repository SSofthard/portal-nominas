# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrExpiredContracts(models.TransientModel):
    _name = 'report.payroll_mexico.template_employee_history'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.job'].search([('id', 'in', data['job_ids'])])
        change_ids = self.env['hr.change.job'].search([('id', 'in', data['change_ids'])])
        start_ids = self.env['hr.change.job'].search([('id', 'in', data['start_ids'])])
        end_ids = self.env['hr.change.job'].search([('id', 'in', data['end_ids'])])
        low_ids = self.env['hr.change.job'].search([('id', 'in', data['low_ids'])])
        return {
            'doc_ids': docs._ids,
            'doc_model': 'hr.job',
            'docs': docs,
            'change_ids': change_ids,
            'start_ids': start_ids,
            'end_ids': end_ids,
            'low_ids': low_ids,
            'data': data,
        }
