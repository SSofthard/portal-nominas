# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrPayslipRun(models.TransientModel):
    _name = 'report.payroll_mexico.payslip_run_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.payslip.run'].browse(data['context'].get('active_ids'))
        slips = self.env['hr.payslip'].browse(data.get('slip_ids'))
        return {
            'doc_ids': docs._ids,
            'doc_model': 'hr.payslip.run',
            'docs': docs,
            'slip_ids': slips,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,
        }
        
