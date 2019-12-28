# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

class EmployeeChangeJobWizard(models.TransientModel):
    _name = "hr.employee.change.job.wizard"

    #Columns
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    date_from = fields.Date(string="Fecha de inicio", default=fields.Date.today())
    job_current_id = fields.Many2one('hr.job', string='Puesto de trabajo actual')
    job_id = fields.Many2one('hr.job', string='Puesto de trabajo')

    def change_job(self):
        self.contract_id.job_id = self.job_id.id
        self.employee_id.job_id = self.job_id.id
        change_job = {
                'state': 'cambio',
                'contract_id': self.contract_id.id,
                'employee_id': self.employee_id.id,
                'date_from': self.date_from,
                'job_before_id': self.job_current_id.id,
                'job_current_id': self.job_id.id,
        }
        self.env['hr.change.job'].create(change_job)
        return True 
