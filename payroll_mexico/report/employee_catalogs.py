# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportEmployeecatalogs(models.TransientModel):
    _name = 'report.payroll_mexico.template_employee_catalogs'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': '',
            'doc_model': 'hr.contract',
            'docs': '',
            'data': data,
        }

