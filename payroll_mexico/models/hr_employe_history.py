# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeChangeHistory(models.Model):
    _name = 'hr.employee.change.history'
    _description = 'Employee Change History'
    _order = 'date_from desc'
    _rec_name = "employee_id"

    #Columns
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    currency_id = fields.Many2one(string="Currency", related='contract_id.currency_id')
    contracting_regime = fields.Selection(string="Contracting Regime", related='contract_id.contracting_regime')
    job_id = fields.Many2one('hr.job', index=True, string='Job Position')
    wage = fields.Monetary('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    salary = fields.Monetary('SDI', digits=(16, 2), help="SDI")
    date_from = fields.Date(string="Confirmation Date")
    date_to = fields.Date(string="Date end")
    type = fields.Selection([
        ('wage', 'Wage'),
        ('job', 'Job Position'),
        ('register', 'Register'),
    ], string='Change History', index=True,
        help="""* Type change'
                \n* If the changue is wage, the type is \'Wage\'.
                \n* If the changue is job then type is set to \'Job Position\'.""")
    before_job_id = fields.Char(string='before job')

    @api.multi
    def prepare_changes(self, **kwargs):
        self.create({
            'employee_id': kwargs.get('employee_id', ''),
            'contract_id': kwargs.get('contract_id', ''),
            'job_id': kwargs.get('job_id', ''),
            'before_job_id': kwargs.get('before_job_id', ''),
            'wage': kwargs.get('wage', ''),
            'salary': kwargs.get('salary', ''),
            'date_from': kwargs.get('date_from', ''),
            'date_to': kwargs.get('date_to', ''),
            'type': kwargs.get('type', ''),
        })


class Contract(models.Model):
    _inherit = 'hr.contract'
    
    # Translate fields
    reported_to_secretariat = fields.Boolean('Social Secretariat',
        help='Green this button when the contract information has been transfered to the social secretariat.')

    @api.constrains('wage')
    def _check_wage(self):
        for contract in self:
            if contract.wage <= 0:
                raise ValidationError(_('You cannot create a contract with a salary less than or equal to zero.'))


class Employee(models.Model):
    _inherit = 'hr.employee'

    history_count = fields.Integer(compute='_compute_history_count', string="Employee Change History")
    register = fields.Boolean(string="Register")

    @api.multi
    def _compute_history_count(self):
        for employee in self:
            employee.history_count = len(self.env['hr.employee.change.history'].search([('employee_id','=',employee.id)]))

    @api.multi
    def to_register_employee(self):
        for employee in self:
            contract = self.env['hr.contract'].search([('employee_id','=',employee.id),('state','=','open'),('contracting_regime','=','2')])
            if not contract:
                raise ValidationError(_("The employee is required to have a contract of regimen 'Wages and salaries' in process to give HIGH."))
            else:
                if contract.wage <= 0:
                    raise ValidationError(_("The salary cannot be negative."))
                else:
                    kwargs = {
                        'employee_id': employee.id,
                        'contract_id': contract.id,
                        'job_id': contract.job_id.id,
                        'wage': contract.wage,
                        'salary': contract.integral_salary,
                        'date_from': contract.date_start,
                        'type': 'register',
                    }
                    employee.register = True
                    contract.env['hr.employee.change.history'].prepare_changes(**kwargs)
                    
        
