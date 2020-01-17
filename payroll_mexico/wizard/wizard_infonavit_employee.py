# -*- coding: utf-8 -*-
from datetime import datetime, date
import calendar
from dateutil.relativedelta import relativedelta


from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class wizardInfonavitEmployee(models.TransientModel):
    _name = "wizard.infonavit.employee"

    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    start_bimester = fields.Char('Start bimester', required=True)
    bimester_end = fields.Char('Bimester of end', required=True)
    report_type = fields.Selection([
        ('1', 'Employee Payments'),
        ('2', 'Report creditor data'),
        ], string='Report', required=True, default="1")
    

    
    @api.multi
    def report_print(self):
        bimestre = {
            '01':[1,2],
            '02':[3,4],
            '03':[5,6],
            '04':[7,8],
            '05':[9,10],
            '06':[11,12],
            }
        if not bimestre.get(self.start_bimester.split('/')[0]) or not bimestre.get(self.bimester_end.split('/')[0]):
            raise ValidationError(_("Invalid bimester periods."))
        month_start = bimestre[self.start_bimester.split('/')[0]][0]
        month_end = bimestre[self.bimester_end.split('/')[0]][1]
        date_from="%s-%s-01" % (int(self.start_bimester.split('/')[1]), month_start)
        date_to="%s-%s-%s" % (int(self.bimester_end.split('/')[1]), month_end, calendar.monthrange(int(self.bimester_end.split('/')[1]), month_end)[1])
        date_from=datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to=datetime.strptime(date_to, '%Y-%m-%d').date()
        domain_register = [('employee_id.employer_register_id','=',self.employer_register_id.id)] if self.employer_register_id else []
        domain_work_center = [('employee_id.work_center_id','=',self.work_center_id.id)] if self.work_center_id else []
        domain_date = [('date','>=', date_from),('date','<=', date_to)] if date_from and date_to else []
        docs = self.env['hr.infonavit.credit.line'].search([('employee_id.group_id','=',self.group_id.id)]+domain_register+domain_work_center).mapped('employee_id')
        data = {
                'group': self.group_id.name,
                'employer_register': self.employer_register_id.employer_registry,
                'work_center': self.work_center_id.name,
                'start_bimester': self.start_bimester,
                'bimester_end': self.bimester_end,
            }
        if self.report_type == '2':
            credit = {}
            if not docs:
                raise ValidationError(_("No information was found with the specified data"))
            for employee in docs:
                move_infonavit_high_credit = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','high_credit'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
                move_infonavit_discontinued = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','discontinued'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
                move_infonavit_reboot = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','reboot'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
                move_infonavit_low_credit = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','low_credit'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
                if not move_infonavit_high_credit and not move_infonavit_discontinued and not move_infonavit_reboot and not move_infonavit_low_credit:
                    docs -= employee
                else:
                    if move_infonavit_high_credit.infonavit_id.type == 'percentage':
                        type = 'Porcentaje'
                    elif move_infonavit_high_credit.infonavit_id.type == 'umas':
                        type = 'UMA'
                    else:
                        type = 'Monto Fijo'
                    contract = self.env['hr.contract'].search([
                        ('employee_id','=',employee.id),
                        ('date_start','<=',move_infonavit_high_credit.date),
                        ('contracting_regime','=','02')
                        ],limit=1)
                    discharge_date = ''
                    if contract.date_end and contract.date_end >= date_from and contract.date_end <= date_to:
                        discharge_date = contract.date_end
                    
                    credit[str(employee.id)] = [move_infonavit_high_credit.date or '',
                                                move_infonavit_discontinued.date or '',
                                                move_infonavit_reboot.date or '',
                                                move_infonavit_low_credit.date or '',
                                                move_infonavit_high_credit.infonavit_id.infonavit_credit_number or '',
                                                type or '',
                                                move_infonavit_high_credit.infonavit_id.value or '',
                                                contract.date_start or '',
                                                float("{0:.2f}".format(contract.integral_salary)) or '',
                                                discharge_date
                                                ]
            credit_ids =  self.env['hr.infonavit.credit.history'].search([]+domain_date).mapped('infonavit_id')._ids
            data['docs_ids'] = docs._ids
            data['credit'] = credit
            return self.env.ref('payroll_mexico.report_infonavit_employee').report_action(list(docs._ids), data=data)
        elif self.report_type == '1':
            employee_dict = {}
            for employee in docs:
                payslip_line=self.env['hr.payslip.line'].search([
                                                        ('slip_id.employee_id','=',employee.id), 
                                                        ('slip_id.state','in',['done']),
                                                        ('slip_id.date_from','>=',date_from),
                                                        ('slip_id.date_to','<=',date_to),
                                                        ('salary_rule_id.code','in',['D094'])])
                if not payslip_line:
                    docs -= employee
                else:
                    amount = 0
                    for slip in payslip_line:
                        amount += slip.total
                    move_infonavit_high_credit = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),
                                                                                                 ('move_type','=','high_credit'),
                                                                                                 ('infonavit_id.employee_id','=',employee.id),
                                                                                                 ],limit=1)
                    if move_infonavit_high_credit.infonavit_id.type == 'percentage':
                        type = 'Porcentaje'
                    elif move_infonavit_high_credit.infonavit_id.type == 'umas':
                        type = 'UMA'
                    else:
                        type = 'Monto Fijo'
                    payslip_line_dict = {
                                'credito':move_infonavit_high_credit.infonavit_id.infonavit_credit_number,
                                'Concepto':slip.salary_rule_id.name,
                                'tipo':type,
                                'valor':move_infonavit_high_credit.infonavit_id.value,
                                'amount':amount,
                                }
                    employee_dict[employee.id]=payslip_line_dict
            if not docs:
                raise ValidationError(_("No information was found with the specified data"))
            data['docs_ids'] = docs._ids
            data['employee_dict'] = employee_dict
            return self.env.ref('payroll_mexico.report_infonavit_employee_amount').report_action(list(docs._ids), data=data)
        
