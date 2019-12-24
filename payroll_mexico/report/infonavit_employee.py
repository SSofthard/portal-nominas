# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrInfonavitEmployee(models.TransientModel):
    _name = 'report.payroll_mexico.template_infonavit_employee'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        print (data)
        print (data)
        print (data)
        print (docids)
        print (docids)
        print (docids)
        docs = self.env['hr.employee'].browse(data['docs_ids'])
        print (docs)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'data': data,
        }

