# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

class EmployeeChangeHistoryWizard(models.TransientModel):
    _name = "hr.employee.change.history.wizard"

    #Columns
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    wage = fields.Float('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    date_from = fields.Date(string="Start Date", default=fields.Date.today())

    def apply_change(self):
        affiliate_movements = self.env['hr.employee.affiliate.movements'].search([('contract_id','=',self.contract_id.id),('type','=','07'),('state','in',['draft','generated']),('contracting_regime','in',['2'])])
        if affiliate_movements:
            raise ValidationError(_('There is already an affiliate movement for salary change in draft or generated status, please check and if you want to generate a new one, delete the current one.'))
        self.contract_id.wage = self.wage
        val = {
            'contract_id':self.contract_id.id,
            'employee_id':self.employee_id.id,
            'type':'07',
            'date': self.date_from,
            'wage':self.wage,
            'salary':self.contract_id.integral_salary,
            }
        self.env['hr.employee.affiliate.movements'].create(val)
        return True 

class EmployeeChangeJobWizard(models.TransientModel):
    _name = "hr.employee.change.job.wizard"

    #Columns
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    date_from = fields.Date(string="Fecha", default=fields.Date.today())
    job_id = fields.Many2one('hr.job', string='Puesto de trabajo')

    def change_job(self):
        self.contract_id.job_id = self.job_id.id
        self.employee_id.job_id = self.job_id.id
        history = self.env['hr.change.job'].search([('employee_id', '=', self.employee_id.id),('contract_id', '=', self.contract_id.id)], limit=1)
        history.write({'date_to': self.date_from})
        change_job = {
                'employee_id': self.employee_id.id,
                'contract_id': self.contract_id.id,
                'job_id': self.job_id.id,
                'date_from': self.date_from,
                'date_to': False,
        }
        self.env['hr.change.job'].create(change_job)
        return True 
