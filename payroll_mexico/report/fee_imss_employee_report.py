# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrFeeSettlement(models.TransientModel):
    _name = 'report.payroll_mexico.hr_fees_imss_employees'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.fees.settlement'].search([('id','in',docids)])
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print (docs)
        print (docs)
        print (docs)
        print (docs)
        date_settlement = date(docs.year, docs.month, 1)
        data['uma'] = self.env['table.uma'].search([('year', '=', docs.year)])
        data['salary_min'] = docs.mapped('employer_register_id').municipality_id.get_salary_min(date_settlement)
        data['prima_rt'] = docs.mapped('employer_register_id').risk_factor_ids.filtered(lambda line: line.date_from <= date_settlement and line.date_to >= date_settlement)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': docs,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,
        }
        

class reportHrFeeSettlementBimothly(models.TransientModel):
    _name = 'report.payroll_mexico.hr_fees_employees_bimonthly'

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.fees.settlement'].search([('id','in',docids)])
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print ('kmdlskmdlksmdlsmdlskdml')
        print (docs)
        print (docs)
        print (docs)
        print (docs)
        data['uma'] = self.env['table.uma'].search([('year','=',docs.year)])
        data['salary_min'] = docs.mapped('employer_register_id').municipality_id.get_salary_min(date(docs.year,docs.month,1))
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': docs,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,
        }

