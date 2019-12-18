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
        docs = self.env['hr.payslip.run'].search([('id','in',docids)])
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': docs,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,

        }
        
