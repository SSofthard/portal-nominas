# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

class EmployeeChangeHistoryWizard(models.TransientModel):
    _name = "hr.employee.change.history.wizard"

    #Columns
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    currency_id = fields.Many2one(string="Currency", related='contract_id.currency_id')
    job_id = fields.Many2one('hr.job', index=True, string='Job Position')
    wage = fields.Monetary('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    date_from = fields.Date(string="Start Date", default=fields.Date.today())
    type = fields.Selection([
        ('wage', 'Wage'),
        ('job', 'Job Position'),
    ], string='Change History', index=True,
        help="""* Type changue'
                \n* If the changue is wage, the type is \'Wage\'.
                \n* If the changue is job then type is set to \'Job Position\'.""")

    def apply_change(self):
        kwargs = {
            'employee_id': self.employee_id.id,
            'contract_id': self.contract_id.id,
            'job_id': self.job_id.id if self.type == 'job' else self.contract_id.job_id.id,
            'wage': self.wage if self.type == 'wage' else self.contract_id.wage,
            'date_from': self.date_from,
            'type': self.type,
        }
        if self.type == 'job':
            self.contract_id.write({'job_id': self.job_id.id})
        if self.type == 'wage':
            if self.wage > 0:
                self.contract_id.write({'wage': self.wage})
            else:
                raise ValidationError(_("The salary cannot be negative."))
        self.env['hr.employee.change.history'].prepare_changes(**kwargs)
