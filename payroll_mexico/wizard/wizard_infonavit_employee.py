# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardExpiredContracts(models.TransientModel):
    _name = "wizard.infonavit.employee"

    date_from = fields.Date('Fecha inicial', required=False)
    date_to = fields.Date('Fecha final', required=False)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    
    @api.multi
    def report_print(self, data):
        date_from = self.date_from
        date_to = self.date_to
        domain_register = [('employee_id.employer_register_id','=',self.employer_register_id.id)] if self.employer_register_id else []
        domain_work_center = [('employee_id.work_center_id','=',self.work_center_id.id)] if self.work_center_id else []
        domain_date = domain_date = [('create_date','>=', date_from),('create_date','<=', date_to)] if date_from and date_to else []
        credit_ids =  self.env['hr.infonavit.credit.history'].search([]+domain_date).mapped('credit_id')._ids
        docs = self.env['hr.infonavit.credit.line'].search([('id','in',credit_ids),('employee_id.group_id','=',self.group_id.id)]+domain_register+domain_work_center).mapped('employee_id')
        print (docs)
        print (docs)
        data = {
            'group': self.group_id.name,
            'employer_register': self.employer_register_id.employer_registry,
            'work_center': self.work_center_id.name,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'docs_ids': docs._ids,
        }
        print (docs._ids)
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
