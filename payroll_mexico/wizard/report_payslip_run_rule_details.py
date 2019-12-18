# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

class PayslipRunRuleDetails(models.TransientModel):
    _name = "hr.payslip.run.rule.details"

    #Columns
    payslip_run_id = fields.Many2one('hr.payslip.run', index=True, string='Payslip')
    rule_id = fields.Many2one('hr.salary.rule', index=True, string='Rule')

    @api.multi
    @api.onchange('payslip_run_id')
    def onchange_payslip_run_id(self):
        self.rule_id = False
        rule_ids = order.payslip_run_id.mapped('slip_ids').mapped('line_ids').mapped('salary_rule_id')

        domain = {'rule_id': [('id', 'in', self.payslip_run_id.mapped('slip_ids')..ids)]}
        return {'domain': domain}

    def apply_change(self):
        if self.type == 'job':
            self.contract_id.write({'job_id': self.job_id.id})
        if self.type == 'wage':
            if self.wage > 0:
                self.contract_id.write({'wage': self.wage})
            else:
                raise ValidationError(_("The salary cannot be negative."))
        kwargs = {
            'employee_id': self.employee_id.id,
            'contract_id': self.contract_id.id,
            'job_id': self.job_id.id if self.type == 'job' else self.contract_id.job_id.id,
            'wage': self.wage if self.type == 'wage' else self.contract_id.wage,
            'salary': self.employee_id.salary,
            'date_from': self.date_from,
            'type': self.type,
        }
        self.env['hr.employee.change.history'].prepare_changes(**kwargs)
