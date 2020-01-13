# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrInfonavitEmployeeAmount(models.TransientModel):
    _name = 'report.payroll_mexico.template_infonavit_employee_amount'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.employee'].browse(data['docs_ids'])
        return {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'data': data,
        }

