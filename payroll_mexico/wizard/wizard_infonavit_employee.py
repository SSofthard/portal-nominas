# -*- coding: utf-8 -*-
from datetime import datetime, date
import calendar
from dateutil.relativedelta import relativedelta


from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardExpiredContracts(models.TransientModel):
    _name = "wizard.infonavit.employee"

    # ~ date_from = fields.Date('Fecha inicial', required=False)
    # ~ date_to = fields.Date('Fecha final', required=False)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    start_bimester = fields.Char('Start bimester', required=True)
    bimester_end = fields.Char('Bimester of end', required=True)


    
    @api.multi
    def report_print(self, data):
        
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
        credit = {}
        if not docs:
            raise ValidationError(_("No information was found with the specified data"))
        for employee in docs:
            move_infonavit_high_credit = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','high_credit'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
            move_infonavit_discontinued = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','discontinued'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
            move_infonavit_reboot = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','reboot'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
            move_infonavit_low_credit = self.env['hr.infonavit.credit.history'].search([('infonavit_id.state','in',['active','discontinued','closed']),('move_type','=','low_credit'),('infonavit_id.employee_id','=',employee.id)]+domain_date,limit=1)
            if not move_infonavit_high_credit or not move_infonavit_discontinued or not move_infonavit_reboot or not move_infonavit_low_credit:
                docs -= employee
            else:
                if move_infonavit_high_credit.infonavit_id.type == 'percentage':
                    type = 'Porcentaje'
                elif move_infonavit_high_credit.infonavit_id.type == 'umas':
                    type = 'UMA'
                else:
                    type = 'Monto Fijo'
                credit[str(employee.id)] = [move_infonavit_high_credit.date,
                                            move_infonavit_discontinued.date,
                                            move_infonavit_reboot.date,
                                            move_infonavit_low_credit.date,
                                            move_infonavit_high_credit.infonavit_id.infonavit_credit_number,
                                            type,
                                            move_infonavit_high_credit.infonavit_id.value,
                                            ]
        
        credit_ids =  self.env['hr.infonavit.credit.history'].search([]+domain_date).mapped('infonavit_id')._ids
        data = {
            'group': self.group_id.name,
            'employer_register': self.employer_register_id.employer_registry,
            'work_center': self.work_center_id.name,
            'start_bimester': self.start_bimester,
            'bimester_end': self.bimester_end,
            'docs_ids': docs._ids,
            'credit': credit,
        }
        return self.env.ref('payroll_mexico.report_infonavit_employee').report_action(list(docs._ids), data=data)
        
    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))
