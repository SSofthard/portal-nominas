# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class hrLoanType(models.Model):
    _name = 'hr.loan.type'
    _description = 'Loan Type'
    
    # ~ @api.multi
    # ~ def onchange_interest_payable(self, int_payble):
        # ~ if not int_payble:
            # ~ return {'value':{'interest_mode':'', 'int_rate':0.0}}
        # ~ return {}
        
    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    interest = fields.Boolean(string='Apply interest rate?', default=True)
    interest_type = fields.Selection([('flat', 'Flat'), ('reducing', 'Reducing')], string='Interest Type', default='flat')
    rate = fields.Float(string='% interest', help='Enter the percentage of interest to apply to the loan', digits=(16, 2), required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self:self.env.user.company_id)
    payment_method = fields.Selection([('salary', 'Deduction From Payroll'),
                                       ('cash', 'Direct Cash/Cheque')], 
                                        string='Repayment Method', 
                                        default='salary')
    disburse_method = fields.Selection([('payroll', 'Through Payroll'),
                                        ('loan', 'Direct Cash/Cheque')], 
                                        string='Disburse Method', 
                                        default='loan')
    active = fields.Boolean('Active', defautl=True)
    

class hrLoanPolicy(models.Model):
    _name = "hr.loan.policy"
    _description = "Loan policies for employees"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    company_id = fields.Many2one('res.company','Company', required=True, default=lambda self:self.env.user.company_id)
    type = fields.Selection([
                ('upper_loan_limit', 'Upper loan limit'),
                ('time_between_loans', 'Time between loans'),
                ('time_in_the_company', 'Time in the company')], 
                string='Type', required=True)
    value = fields.Float(string='Value', 
        help='Set the value to be taken by the policy, it can take values ​​for amounts or number of months.')
    active = fields.Boolean('Active', defautl=True)

