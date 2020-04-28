# -*- coding: utf-8 -*-

import time
import datetime
import calendar
import pytz
import dateutil
import base64
import locale

from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError


class HrPayrollDepositReport(models.TransientModel):
    _name = 'hr.wizard.deposit.report'
    _description = 'Deposit Report'

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(HrPayrollDepositReport, self).default_get(fields)
        if self._context.get('active_id'):
            active_id = int(self._context['active_id'])
            result['payslip_run_id'] = active_id
            payslip_run_id = self.env['hr.payslip.run'].search([('id', '=', active_id)], limit=1)
            result['payroll_month'] = payslip_run_id.payroll_month
        return result

    #Columns
    company_ids = fields.Many2many('res.company', string="Companies",)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True)
    wage = fields.Boolean(string='Wages and salaries', help="Hiring wages and salaries.")
    free = fields.Boolean(string='Free', help="Hiring free.")
    assimilated = fields.Boolean(string='Assimilated to salary', help="Hiring Assimilated to salary.")
    payroll_month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')], 
        string='Payroll month',
        readonly=True)

    @api.onchange('payslip_run_id')
    def _onchange_payslip_run_id(self):
        if self.payslip_run_id:
            company_ids = self.payslip_run_id.slip_ids.mapped('company_id.id')
            res = {
                'domain': {
                    'company_ids': [('id', 'in', company_ids)], 
                }
            }
        return res

    @api.multi
    def report_print(self, data):
        regime = {
            '02': 'SUELDOS Y SALARIOS',
            '05': 'SUELDO LIBRE',
            '08': 'ASIMILADOS COMISIONISTAS',
            '09': 'ASIMILADOS HONORARIOS',
            '11': 'ASIMILADOS OTROS',
            '99': 'OTRO REGIMEN',
        }
        
        contracting_domain = []
        PayslipObj = self.env['hr.payslip'].sudo()
        domain = [('payslip_run_id','=',self.payslip_run_id.id)]
        if self.company_ids:
            domain += [('company_id','in', self.company_ids.ids)]
        
        if self.wage:
            contracting_domain += ['02']
        if self.free:
            contracting_domain += ['05','99']
        if self.assimilated:
            contracting_domain += ['08','09','11']
        if contracting_domain:
            domain += [('contracting_regime','in', contracting_domain)]
        payslips = PayslipObj.search(domain, order="date_from asc, id asc")
        if not payslips:
            raise UserError(_('No results found.'))
        
        payroll_dic = {}
        payroll_dic['payroll_of_month'] = self.payslip_run_id.payroll_of_month
        payroll_dic['date_large'] = '%s a %s' %(self.payslip_run_id.date_start.strftime("%d/%b/%Y").title(), self.payslip_run_id.date_end.strftime("%d/%b/%Y").title())
        employees = []
        total = 0
        for slip in payslips:
            total += sum(slip.line_ids.filtered(lambda r: r.category_id.code == 'NET').mapped('total'))
            employees.append({
                'enrollment': slip.employee_id.enrollment,
                'name': slip.employee_id.complete_name,
                'contracting_regime': regime[slip.contracting_regime],
                'bank_key': slip.contract_id.bank_account_id.bank_id.code,
                'bank': slip.contract_id.bank_account_id.bank_id.name,
                'account': slip.contract_id.bank_account_id.bank_account,
                'total': slip.line_ids.filtered(lambda r: r.category_id.code == 'NET').mapped('total')[0] or self.not_total(),
            })
        payroll_dic['employees'] = sorted(employees, key=lambda k: k['name'])
        payroll_dic['total_records'] = len(payslips)
        payroll_dic['total'] = total
        
        data={
            'payroll_data': payroll_dic
            }
        return self.env.ref('payroll_mexico.payroll_deposit_report_template').report_action(self,data)    
