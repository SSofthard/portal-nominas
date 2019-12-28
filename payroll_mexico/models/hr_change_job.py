# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class ChangeOfJob(models.Model):
    _name = 'hr.change.job'

    state = fields.Selection([
            ('alta','Alta'),
            ('baja','Baja'),
            ('cambio','Cambio de puesto'),], string="state")
    contract_id = fields.Many2one('hr.contract',string='Contracto',store=True)
    employee_id = fields.Many2one('hr.employee',string="Employee")
    date_from = fields.Date(string='Desde')
    job_before_id = fields.Many2one('hr.job', string='Puesto de trabajo anterior')
    job_current_id = fields.Many2one('hr.job', string='Puesto de trabajo actual')

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
                'state': 'alta',
                'contract_id': res.id,
                'employee_id': res.employee_id.id,
                'date_from': res.date_start,
                'job_before_id': '',
                'job_current_id': res.job_id.id,
        }
        self.env['hr.change.job'].create(change_job)
        return res
