# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrContract(models.TransientModel):
    _name = 'report.payroll_mexico.contract_type_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': self.env['hr.contract'].search([('id','in',data['context']['active_ids'])]),
            'data': data,
        }


class reportHrPayroll(models.TransientModel):
    _name = 'report.payroll_mexico.action_payroll_deposit_report'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip.run',
            'docs': self.env['hr.payslip.run'].search([('id','in',data['context']['active_ids'])]),
            'data': data,
        }


class reportHrFault(models.TransientModel):
    _name = 'report.payroll_mexico.fault_report_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip.run',
            'docs': self.env['hr.payslip.run'].search([('id','in',data['context']['active_ids'])]),
            'data': data,
        }
        
