# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class reportHrPayslipRun(models.TransientModel):
    _name = 'report.payroll_mexico.payslip_run_template'
        
    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.payslip.run'].browse(data['context'].get('active_ids'))
        slips = self.env['hr.payslip'].browse(data.get('slip_ids'))
        sum_subs_empleo = {}
        sum_subs_isr = {}
        sum_IMSS = {}
        sum_total_percepciones = {}
        sum_otras_percepciones = {}
        sum_otras_deducciones = {}
        sum_sueldo = {}
        total_efectivo = {}
        neto_pagado = {}
        total_gravable = {}
        for struct in slips.mapped('struct_id'):
            payslip_filtered = slips.filtered(lambda slip: slip.struct_id.id == struct.id)
            sum_subs_empleo[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.code == 'P105').mapped('total'))
            sum_subs_isr[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.salary_rule_id.type == 'deductions' and line.salary_rule_id.type_deduction == '002').mapped('total'))
            sum_IMSS[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.code == 'D002').mapped('total'))
            sum_otras_deducciones[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.salary_rule_id.type == 'deduction').mapped('total'))
            sum_total_percepciones[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.code == 'P195').mapped('total'))
            sum_otras_percepciones[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.salary_rule_id.type == 'perception' and line.code != 'P001').mapped('total'))
            sum_sueldo[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.salary_rule_id.type == 'perception' and line.code == 'P001').mapped('total'))
            total_efectivo[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.category_id.code == 'NETE' or line.category_id.code == 'GROSS').mapped('total'))
            neto_pagado[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.code == 'T001').mapped('total'))
            total_gravable[struct.id] = sum(payslip_filtered.mapped('line_ids').filtered(lambda line: line.salary_rule_id.payroll_tax).mapped('total'))

        print ('sum_subs_empleo')
        print (sum_subs_empleo)
        print ('sum_subs_isr')
        print (sum_subs_isr)
        print ('sum_IMSS')
        print (sum_IMSS)
        print ('sum_otras_deducciones')
        print (sum_otras_deducciones)
        print ('sum_total_percepciones')
        print (sum_total_percepciones)
        print ('sum_otras_percepciones')
        print (sum_otras_percepciones)
        print ('sum_sueldo')
        print (sum_sueldo)
        return {
            'doc_ids': docs._ids,
            'doc_model': 'hr.payslip.run',
            'docs': docs,
            'slip_ids': slips,
            'sum_subs_empleo': sum_subs_empleo,
            'sum_subs_isr': sum_subs_isr,
            'sum_IMSS': sum_IMSS,
            'sum_otras_deducciones': sum_otras_deducciones,
            'sum_total_percepciones': sum_total_percepciones,
            'sum_otras_percepciones': sum_otras_percepciones,
            'sum_sueldo': sum_sueldo,
            'data': data,
            'currency_precision': self.env.user.company_id.currency_id.decimal_places,
        }
        
