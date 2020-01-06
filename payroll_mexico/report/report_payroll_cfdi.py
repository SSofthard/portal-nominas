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
        # ~ return {
            # ~ 'doc_ids': docids,
            # ~ 'doc_model': 'hr.payslip',
            # ~ 'docs': self.env['hr.payslip'].search([('id','in',data['context']['active_ids'])]),
            # ~ 'data': data,
        # ~ }
        
        doc_ids = docids or data['docids']
        docs = self.env['hr.payslip'].search([('id', 'in', doc_ids)])
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'data': data,
        }
        
class reportPayroll(models.TransientModel):
    _name = 'report.payroll_mexico.payroll_receipt_report_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.payslip'].browse(data['docids'])
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'data': data,
        }

