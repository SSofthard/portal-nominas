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

    @api.onchange('type')
    def onchange_salary_rule_id(self):
        structure = self.env['hr.payroll.structure'].search([('settlement','=',True)])
        rule_ids = []
        for rule in structure.rule_ids:
            if rule.id not in rule_ids:
                rule_ids.append(rule.id)
        return {'domain': {'salary_rule_ids': [('id', 'in', rule_ids)]}}


    @api.multi
    def report_print(self):
        data={}
        domain = [] 
        
        if self.type == '2':
            if self.employee_ids:
                domain.append(('employee_id','in',employee_ids.ids))
            settlement = self.env['hr.payslip'].search([('struct_id.settlement','=',True),('settlement_date', '>=', self.date_from),('settlement_date', '<=', self.date_to)])
            print (settlement)
            print (settlement)
            print (settlement)
            print (settlement)
            print (settlement)
            print (settlement)
        print (iooo)
        return self.env.ref('payroll_mexico.report_settlement_low').report_action([], data=data)

    
