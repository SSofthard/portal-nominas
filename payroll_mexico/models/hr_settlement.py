# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone

import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.osv import expression


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    settlement = fields.Boolean(string='Settlement')
    settlemen_date = fields.Date(string='Settlemen date', readonly=True, required=False,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)), states={'draft': [('readonly', False)]})
    reason_liquidation = fields.Selection([
            ('1', 'TERMINACIÓN DE CONTRATO'),
            ('2', 'SEPARACIÓN VOLUNTARIA'),
            ('3', 'ABANDONO DE EMPLEO'),
            ('4', 'DEFUNCIÓN'),
            ('5', 'AUSENTISMOS'),
            ('6', 'RESICIÓN DE CONTRATO'),
            ('7', 'JUBILACIÓN'),
            ('8', 'PENSIÓN'),
            ('9', 'ACEPTO OTRO EMPLEO # 42'),
            ('10', 'CLAUSURA'),
            ('11', 'OTROS'),
            ], 
            string='Reason for liquidation', 
            required=False,
            states={'draft': [('readonly', False)]})
    indemnify_employee = fields.Boolean(string='Indemnify the employee')
    
    @api.onchange('reason_liquidation')
    def onchange_estructure_id(self):
        if self.reason_liquidation in  ['2','1']:
            self.indemnify_employee = False
        return 

    @api.multi
    def print_settlement_report(self):
        # ~ payrolls = self.filtered(lambda s: s.state in ['close'])
        payroll_dic = {}
        # ~ employees = []
        # ~ total = 0
        # ~ for payroll in payrolls:
            # ~ payroll_dic['payroll_of_month'] = payroll.payroll_of_month
            # ~ payroll_dic['date_large'] = '%s/%s/%s' %(payroll.date_end.strftime("%d"), payroll.date_end.strftime("%b").title(), payroll.date_end.strftime("%Y"))
            # ~ company = payroll.mapped('slip_ids').mapped('company_id')
            # ~ payroll_dic['rfc'] = company.rfc
            # ~ payroll_dic['employer_registry'] = company.employer_register_ids.filtered(lambda r: r.state == 'valid').mapped('employer_registry')[0] or ''
            # ~ for slip in payroll.slip_ids:
                # ~ total += sum(slip.line_ids.filtered(lambda r: r.category_id.code == 'NET').mapped('total'))
                # ~ employees.append({
                    # ~ 'enrollment': slip.employee_id.enrollment,
                    # ~ 'name': slip.employee_id.name_get()[0][1],
                    # ~ 'fulltime': '?',
                    # ~ 'office': '?',
                    # ~ 'bank_key': slip.employee_id.get_bank().bank_id.code or '',
                    # ~ 'bank': slip.employee_id.get_bank().bank_id.name or '',
                    # ~ 'account': slip.employee_id.get_bank().bank_account or '',
                    # ~ 'total': slip.line_ids.filtered(lambda r: r.category_id.code == 'NET').mapped('total')[0] or self.not_total(),
                # ~ })
            # ~ payroll_dic['employees'] = employees
            # ~ payroll_dic['total_records'] = len(payroll.slip_ids)
        # ~ payroll_dic['total'] = total
        data={
            'payroll_data':payroll_dic
            }
        return self.env.ref('payroll_mexico.settlement_report').report_action(self,data)

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    settlement = fields.Boolean(string='Settlement structure?')
    payroll_type = fields.Selection([
            ('ordinary_payroll', 'Ordinary Payroll'),
            ('extraordinary_payroll', 'Extraordinary Payroll')], 
            string='Payroll Type', 
            required=True,)
