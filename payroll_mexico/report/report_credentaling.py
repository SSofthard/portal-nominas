# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHr(models.TransientModel):
    _name = 'report.payroll_mexico.report_credentaling'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.employee'].browse(data['doc_ids'])
        print ('kjdbkabdkhasbdkasmdbjsahdbuhjd')
        print ('kjdbkabdkhasbdkasmdbjsahdbuhjd')
        print ('kjdbkabdkhasbdkasmdbjsahdbuhjd')
        print ('kjdbkabdkhasbdkasmdbjsahdbuhjd')
        print ('kjdbkabdkhasbdkasmdbjsahdbuhjd')
        print (data['doc_ids'])
        print (data)
        print (data)

        return {
            'doc_ids': data['doc_ids'],
            'doc_model': 'hr.employee',
            'docs': docs,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,
        }
        
