# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportPayrollSettlement(models.TransientModel):
    _name = 'report.payroll_mexico.template_report_settlement_low'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'docs': '',
            'data': data,
            'company_id': self.env.user.company_id,
        }

