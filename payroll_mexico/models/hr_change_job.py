# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class ChangeOfJob(models.Model):
    _name = 'hr.change.job'

    contract_id = fields.Many2one('hr.contract',string='Contracto',store=True)
    employee_id = fields.Many2one('hr.employee',string="Employee")
    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')
    job_id = fields.Many2one('hr.job', string='Puesto de trabajo')

class Contract(models.Model):
    _inherit = 'hr.contract'
    
    @api.model
    def create(self, vals):
        res = super(Contract, self).create(vals)
        if res.contracting_regime == '2':
            val = {
                'contract_id':res.id,
                'employee_id':res.employee_id.id,
                'type':'high_reentry',
                'date':res.previous_contract_date or res.date_start,
                'wage':res.wage,
                'salary':res.integral_salary,
            }
            self.env['hr.employee.affiliate.movements'].create(val)
        change_job = {
                'employee_id': res.employee_id.id,
                'contract_id': res.id,
                'job_id': res.job_id.id,
                'date_from': res.date_start,
                'date_to': False,
                
        }
        self.env['hr.change.job'].create(change_job)
        return res
