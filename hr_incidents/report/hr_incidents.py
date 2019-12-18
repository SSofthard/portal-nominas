# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrIncidentsWizard(models.TransientModel):
    _name = 'report.hr_incidents.hr_leave_incidents_report'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        print ('data22')
        return {
            'doc_ids': '',
            'doc_model': 'hr.leave',
            'docs': '',
            'data': data,
        }

    
class reportHrInhabilityAbsenteeism(models.TransientModel):
    _name = 'report.hr_incidents.inhability_absenteeism_report_view'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        print ('data')
        return {
            'doc_ids': '',
            'doc_model': 'hr.leave',
            'docs': '',
            'data': data,
        }
        
        
