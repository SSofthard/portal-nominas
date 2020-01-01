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
        history_id = self.env['hr.change.job'].search([('id', 'in', data['history_id'])])
        history_date = self.env['hr.change.job'].search([('id', 'in', data['history_ids_date_to'])])
        history_low = self.env['hr.change.job'].search([('id', 'in', data['history_ids_low'])])
        print ('docs')
        print (docs)
        return {
            'doc_ids': docs._ids,
            'doc_model': 'hr.change.job',
            'docs': docs,
            'history_id': history_id,
            'history_date': history_date,
            'history_low': history_low,
            'data': data,
        }
