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
    date_from = fields.Date(string="Start Date")
    type = fields.Selection([
        ('wage', 'Wage'),
        ('job', 'Job Position'),
    ], string='Change History', index=True,
        help="""* Type changue'
                \n* If the changue is wage, the type is \'Wage\'.
                \n* If the changue is job then type is set to \'Job Position\'.""")


class Contract(models.Model):
    _inherit = 'hr.contract'
    
    # Translate fields
    reported_to_secretariat = fields.Boolean('Social Secretariat',
        help='Green this button when the contract information has been transfered to the social secretariat.')
    
    

# ~ class Contract(models.Model):
    # ~ _inherit = 'hr.employee'

    
