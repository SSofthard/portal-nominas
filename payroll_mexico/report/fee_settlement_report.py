# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrFeeSettlement(models.TransientModel):
    _name = 'report.payroll_mexico.hr_fees_settlement_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.fees.settlement'].search([('id','in',docids)])
        print (docids)
        print (docids)
        print (docids)
        print (docs)
        print (docs)
        print (docs)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': docs,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,
        }
        
