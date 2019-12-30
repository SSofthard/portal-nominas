# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

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
        history = self.env['hr.change.job'].search([('employee_id', '=', self.employee_id.id),('contract_id', '=', self.contract_id.id)])
        print ('history')
        print (history)
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
