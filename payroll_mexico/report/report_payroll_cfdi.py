# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportPayrollCfdi(models.TransientModel):
    _name = 'report.payroll_mexico.payroll_cfdi_report_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.payslip'].browse(data['docs_ids'])
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'data': data,
        }

