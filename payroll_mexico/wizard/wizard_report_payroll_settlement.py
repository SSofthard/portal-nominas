# -*- coding: utf-8 -*-

import io
import base64

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class payrollReportSettlement(models.TransientModel):
    _name = "payroll.report.settlement"
    _description = 'Settlement Report'

    #Columns
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    type = fields.Selection([
        ('1', 'Consolidated'),
        ('2', 'Per employee'),
         ],string = 'Type', required=True, default='1')
    employee_ids = fields.Many2many('hr.employee','report_settlement_employee_rel','report_settlement_id','employee_id', "Employees", required=False)
    salary_rule_ids = fields.Many2many('hr.salary.rule','report_settlement_salary_rule_rel','report_settlement_id','salary_rule_id', "Salary rules", required=False)

    @api.onchange('salary_rule_ids')
    def onchange_salary_rule_id(self):
        structure = self.env['hr.payroll.structure'].search([('settlement','=',True)])
        rule_ids = []
        for rule in structure.rule_ids:
            if rule.id not in rule_ids and rule.print_to_excel:
                rule_ids.append(rule.id)
        return {'domain': {'salary_rule_ids': [('id', 'in', rule_ids)]}}


    @api.multi
    def report_print(self):
        data={}
        
        if self.type == '2':
            domain = [('struct_id.settlement','=',True),('settlemen_date', '>=', self.date_from),('settlemen_date', '<=', self.date_to),('group_id', '=', self.group_id.id)]
            domain_rule = [('salary_rule_id.print_to_excel','=',True),
                            ('slip_id.settlemen_date', '>=', self.date_from),
                            ('slip_id.settlemen_date', '<=', self.date_to),
                            ('slip_id.group_id', '<=', self.group_id.id),
                            ('slip_id.struct_id.settlement','=',True),
                            ('total','>',0)]
            per_employee = {}
            if self.employee_ids:
                domain.append(('employee_id','in',self.employee_ids.ids))
            if self.salary_rule_ids:
                domain_rule.append(('salary_rule_id','in',self.salary_rule_ids.ids))
            settlement_ids = self.env['hr.payslip'].search(domain)
            salary_rule_list =   list(map(lambda x: x.code, self.env['hr.payslip.line'].search(domain_rule).mapped('salary_rule_id')))
            for settlement in settlement_ids:
                salary_rule_employee={}
                perception = sum(self.env['hr.payslip.line'].search([('category_id.code','in',['GROSS']),('slip_id','=',settlement.id)]).mapped('total'))
                deduction = sum(self.env['hr.payslip.line'].search([('category_id.code','in',['DEDT']),('slip_id','=',settlement.id)]).mapped('total'))
                total = sum(self.env['hr.payslip.line'].search([('category_id.code','in',['NET']),('slip_id','=',settlement.id)]).mapped('total'))
                
                for code in salary_rule_list:
                     amount = sum(self.env['hr.payslip.line'].search([('salary_rule_id.code','=',code),('total','>',0),('slip_id','=',settlement.id)]).mapped('total'))
                     salary_rule_employee[code] = amount
                per_employee[settlement.employee_id.id]={
                                          'complete_name':settlement.employee_id.complete_name,
                                          'code':settlement.employee_id.enrollment,
                                          'low_date':settlement.date_end,
                                          'settlemen_date':settlement.settlemen_date,
                                          'perception':perception,
                                          'deduction':deduction,
                                          'total':total,
                                          'settlement_total':'0',
                                          'reason_liquidation':dict(settlement._fields['reason_liquidation']._description_selection(self.env)).get(settlement.reason_liquidation),
                                          'salary_rule_employee':salary_rule_employee,
                                          }
            data['per_employee'] = per_employee
            data['salary_rule_list'] = salary_rule_list
            data['type'] = '2'
        else:
            data['type'] = '1'
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        data['group_id'] = self.group_id.name
        return self.env.ref('payroll_mexico.report_settlement_low').report_action([], data=data)

    
