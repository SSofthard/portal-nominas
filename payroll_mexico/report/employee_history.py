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
        docs = self.env['hr.change.job'].search([('id', 'in', data['history_ids'])])
        print ('data')
        print (data)
        return {
            'doc_ids': docs._ids,
            'doc_model': 'hr.change.job',
            'docs': docs,
            'data': data,
        }
