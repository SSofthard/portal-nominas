# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrIncidentsWizard(models.TransientModel):
    _name = 'report.payroll_mexico.template_expired_contracts'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        print ('data')
        print (data)
        return {
            'doc_ids': '',
            'doc_model': 'hr.contract',
            'docs': '',
            'data': data,
        }

