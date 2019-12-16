# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeChangeHistory(models.Model):
    _name = 'hr.employee.change.history'
    _description = 'Employee Change History'
    _order = 'date_from desc'

    #Columns
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    currency_id = fields.Many2one(string="Currency", related='contract_id.currency_id')
    job_id = fields.Many2one('hr.job', index=True, string='Job Position')
    wage = fields.Monetary('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    date_from = fields.Date(string="Confirmation Date")
    type = fields.Selection([
        ('wage', 'Wage'),
        ('job', 'Job Position'),
    ], string='Change History', index=True,
        help="""* Type changue'
                \n* If the changue is wage, the type is \'Wage\'.
                \n* If the changue is job then type is set to \'Job Position\'.""")

    @api.multi
    def prepare_changes(self, **kwargs):
        self.create({
            'employee_id': kwargs.get('employee_id', ''),
            'contract_id': kwargs.get('contract_id', ''),
            'job_id': kwargs.get('job_id', ''),
            'wage': kwargs.get('wage', ''),
            'date_from': kwargs.get('date_from', ''),
            'type': kwargs.get('type', ''),
        })


class Contract(models.Model):
    _inherit = 'hr.contract'
    
    # Translate fields
    reported_to_secretariat = fields.Boolean('Social Secretariat',
        help='Green this button when the contract information has been transfered to the social secretariat.')


class Contract(models.Model):
    _inherit = 'hr.employee'

    history_count = fields.Integer(compute='_compute_history_count', string="Employee Change History")

    @api.multi
    def _compute_history_count(self):
        for employee in self:
            employee.history_count = len(self.env['hr.employee.change.history'].search([('employee_id','=',employee.id)]))
