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
