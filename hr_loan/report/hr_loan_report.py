# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrLoan(models.TransientModel):
    _name = 'report.hr_loan.loan_type_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hr.loan',
            'docs': self.env['hr.loan'].search([('id','in',data['context']['active_ids'])]),
            'data': data,
        }
        
