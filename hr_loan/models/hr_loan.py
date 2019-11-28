# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning

import locale
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class hrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date asc"
    
    @api.multi
    @api.depends('loan_line_ids')
    def _cal_amount_all(self):
        for loan in self:
            amount_paid = 0
            for payment in loan.loan_line_ids:
                if payment.state == 'paid':
                    amount_paid += payment.amount_total
            
            loan.total_amount_paid = amount_paid
            loan.total_amount_due= loan.total_amount - amount_paid
    
    name = fields.Char('Reference', required=False, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, states={'draft':[('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, readonly=True, states={'draft':[('readonly', False)]})
    department_id = fields.Many2one('hr.department', string="Department", states={'paid':[('readonly', True)], 'disburse':[('readonly', True)], 'approved':[('readonly', True)]})
    
    date_applied = fields.Date(string='Applied Date', required=True, readonly=False, states={'paid':[('readonly', True)], 'disburse':[('readonly', True)], 'approved':[('readonly', True)]}, default=fields.Date.context_today)
    date_approved = fields.Date(string='Approved Date', readonly=True, copy=False)
    date_repayment = fields.Date(string='Repayment Date', readonly=False, states={'paid':[('readonly', True)], 'disburse':[('readonly', True)], 'approved':[('readonly', True)]}, copy=False)
    date_disb = fields.Date(string='Disbursement Date', readonly=False, states={'paid':[('readonly', True)], 'disburse':[('readonly', True)]})
    
    type_id = fields.Many2one('hr.loan.type', string='Loan Type', required=True, readonly=True, states={'draft':[('readonly', False)]})
    number_fees = fields.Integer(string='Number of fees', required=True, readonly=True, states={'draft':[('readonly', False)]})
    schedule_pay = fields.Selection([
                            ('monthly', 'Monthly'),
                            ('quarterly', 'Quarterly'),
                            ('semi-annually', 'Semi-annually'),
                            ('annually', 'Annually'),
                            ('weekly', 'Weekly'),
                            ('bi-weekly', 'Bi-weekly'),
                            ('bi-monthly', 'Bi-monthly'),
                        ], string='Scheduled Pay', index=True, default='monthly', required=True, readonly=True, help="Defines the frequency of the loan payment.")
    interest = fields.Boolean(string='Is Interest Payable', default=False, readonly=True, states={'draft':[('readonly', False)]})
    interest_type = fields.Selection(selection=[('flat', 'Flat'), ('reducing', 'Reducing'), ('', '')], string='Interest Type', default='', readonly=True, states={'draft':[('readonly', False)]})
    rate = fields.Float(string='Rate', multi='type', digits=(16, 2), readonly=True, states={'draft':[('readonly', False)]}, help='Interest rate between 0-100 in range',)
    loan_amount = fields.Float(string='Loan Amount', required=True, readonly=True, states={'draft':[('readonly', False)]})
    wage = fields.Float(string='Wage', required=False, readonly=True, states={'draft':[('readonly', False)]}, help='Salary of the employee based on the selected contract.',)
    total_interest_amount = fields.Float(string='Total Interest on Loan', store=True)
    total_amount = fields.Float(string='Total amount', store=True)
    total_amount_paid = fields.Float(compute='_cal_amount_all', string='Received From Employee', store=True)
    total_amount_due = fields.Float(compute='_cal_amount_all', string='Balance on Loan', store=True, help='Remaining Amount due.',)
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', 'Loan Line', copy=False)
    company_id = fields.Many2one('res.company', 'Company',required=True,readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='User', readonly=True, required=True,)
    state = fields.Selection([('draft', 'Draft'),
                              ('applied', 'Applied'),
                              ('approved', 'Approved'),
                              ('paid', 'Paid'),
                              ('disburse', 'Disbursed'),
                              ('rejected', 'Rejected'),
                              ('cancel', 'Cancelled')], 
                              string='State', readonly=True, copy=False, default='draft', track_visibility='onchange')
    notes = fields.Text(string='Note')
    
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.contract_id = False
            
    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            self.wage = self.contract_id.wage
            self.company_id = self.contract_id.company_id
            self.currency_id = self.contract_id.company_id.currency_id
            
    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id:
            self.interest = self.type_id.interest
            self.interest_type = self.type_id.interest_type
            self.rate = self.type_id.rate
    
    
    def verify_policy_compliance(self):
        msg = ''
        for policy in self.type_id.loan_policy_ids:
            if policy.type == 'upper_loan_limit':
                if float(self.loan_amount) > float(policy.value):
                    msg += policy.name +':%s \n' % (policy.value)
            elif policy.type == 'time_between_loans':
                loan_old = self.search([('state', '=', 'disburse'), ('employee_id', '=', self.employee_id.id)], order='date_applied asc', limit=1)
                if loan_old:
                    last_date = loan_old.date_applied
                    date_diff = last_date + relativedelta(months=int(policy.value))
                    if date_diff > last_date:
                        msg += '\n %s :\n\t\t Last loan date: %s \n\t\tGap required(months) :  %s \n\t\tcan apply on/after: %s \n' \
                                    % (policy.name, last_date, policy.value, date_diff.strftime('%Y-%m-%d'))
            else:
                contract_date = self.contract_id.date_start
                date_diff = contract_date + relativedelta(months=int(policy.value))
                if date_diff > contract_date:
                    msg += '\n %s :\n\t\tContract date: %s  \n\t\tGap required(months):%s \n\t\tcan apply on/after: %s \n'\
                            % (policy.name, contract_date, policy.value, date_diff.strftime('%Y-%m-%d'))
        if msg:
            raise Warning( _('Loan Policies not satisfied :\n %s ') % (_(msg)))
        return True
        
    @api.multi
    def action_applied(self):
        for loan in self:
            msg = ''
            if loan.loan_amount <= 0.0:
                msg += _('Loan Amount\n ')
            if loan.interest and loan.rate <= 0.0:
                msg += _('Interest Rate\n ')
            if loan.number_fees <= 0.0:
                msg += _('Number of fees')
            if msg:
                raise Warning( _('Enter values ​​greater than zero:\n %s ') % (msg))
            self.verify_policy_compliance()
            loan.state = 'applied'
            loan.name = self.env['ir.sequence'].get('hr.loan')
        return True
    
    @api.multi
    def action_approved(self):
        for loan in self:
            self.date_approved = date.today()
            self.state = 'approved'
    
    @api.multi
    def action_rejected(self):
        for loan in self:
            loan.state = 'rejected'
    
    @api.multi
    def action_reset(self):
        for loan in self:
            loan.state = 'draft'
    
    @api.multi
    def action_cancel(self):
        for loan in self:
            loan.state = 'cancel'
    
    @api.multi
    def action_disburse(self):
        for loan in self:
            self.compute_installments()
            if loan.type_id.disburse_method == 'payroll':
                loan.state = 'disburse'
            else:
                loan.state = 'disburse'
    
    def generate_payment_date_to(self,date_from):
        if self.schedule_pay == 'monthly':
            date_to = date_from + relativedelta(months=1)
        elif self.schedule_pay == 'quarterly':
            date_to = date_from + relativedelta(months=3)
        elif self.schedule_pay == 'semi-annually':
            date_to = date_from + relativedelta(months=6)
        elif self.schedule_pay == 'annually':
            date_to = date_from + relativedelta(years=1)
        elif self.schedule_pay == 'weekly':
            date_to = date_from + relativedelta(days=7)
        elif self.schedule_pay == 'bi-weekly':
            date_to = date_from + relativedelta(days=15)
        elif self.schedule_pay == 'bi-monthly':
            date_to = date_from + relativedelta(months=2)
        return date_to
    
    @api.model
    def reducing_balance_method(self, p, r, n):
        # Determine the interest rate on the loan, the length of the loan and the amount of the loan
        res = {}
        for i in range(0, n):
            print (i)
            step_1_p = p  # principal amount at the beginning of each period
            step_2_r_m = r / (12 * 100.00)  # interest rate per month
            step_3_r_m = 1 + step_2_r_m  # add 1 to interest rate per month
            step_4 = step_3_r_m ** (n - i)  # Raise the step_2_r_m to the power of the number of payments required on the loan
            step_5 = step_4 - 1  #  minus 1 from step_4
            step_6 = step_2_r_m / step_5  # Divide the interest rate per month(step_2_r_m) by the step_5
            step_7 = step_6 + step_2_r_m  # Add the interest rate per month to the step_6 
            step_8_EMI = round(step_7 * step_1_p, 2)  # Total EMI to pay month
            step_9_int_comp = round(step_1_p * step_2_r_m, 2)  # Total Interest component in EMI
            step_10_p_comp = round(step_8_EMI - step_9_int_comp, 2)  # Total principal component in EMI
            p -= step_10_p_comp  # new principal amount 
            res[self.name+'-'+str(i+1)] = {'emi':step_8_EMI,
                      'amount':step_10_p_comp,
                      'amount_interest_installment':step_9_int_comp
                      }
        return res
    
    @api.multi
    def compute_installments(self):
        for loan in self:
            loan.loan_line_ids.unlink()
            if not loan.date_disb:
                raise Warning(_('Please give disbursement date.'))
            installment_obj = self.env['hr.loan.line']
            amount = loan.loan_amount / (loan.number_fees or 1.0)
            amount_interest = 0
            amount_interest = 0
            acum = 0
            if loan.interest:
                amount_interest = (loan.loan_amount * loan.rate)/100
                amount_interest_installment = amount_interest / (loan.number_fees or 1.0)
            date_from = self.date_disb
            if loan.interest_type == 'reducing':
                reducing = self.reducing_balance_method(loan.loan_amount, loan.rate, loan.number_fees)
            for installment in range(0, loan.number_fees):
                date_from = date_from
                date_to = self.generate_payment_date_to(date_from)
                acum+=1
                name = loan.name+'-'+str(acum)
                if loan.interest_type == 'reducing':
                    amount = reducing[name]['amount']
                    if loan.interest:
                        amount_interest_installment = reducing[name]['amount_interest_installment']
                line = {'name':name,
                         'date_from':date_from,
                         'date_to':date_to,
                         'amount':amount,
                         'interest_amount':amount_interest_installment,
                         'amount_total':amount+amount_interest_installment,
                         'loan_id':loan.id
                         }
                date_from = date_to
                installment_obj.create(line)
            self.total_amount = self.loan_amount + amount_interest
            self.total_interest_amount = amount_interest
        return True
        
    def print_hr_loan(self):
        loan_dic = {}
        mensaje = []
        for loan in self:
            report=self.type_id.report_id
            if not report:
                mensaje.append('Debe llenar el campo reporte dentro de tipo de prestamo \n')
                
            depart=self.department_id
            if not depart:
                mensaje.append('Debe llenar el campo departamento \n')
                
            date_approved=self.date_approved
            if not date_approved:
                mensaje.append('Debe llenar el campo fecha de aprobación \n')
                
            interest_type=self.interest_type
            if not interest_type:
                mensaje.append('Debe llenar el campo tipo de interés \n')
                
            if len(mensaje):
                msg="".join(mensaje)
                raise  UserError(_(msg))
            
            loan_amount=self.loan_amount    
            total_interest_amount=self.total_interest_amount    
            total_amount=self.total_amount    
            locale.setlocale(locale.LC_ALL, '')
            loan_dic[loan.id]=[self.date_applied.strftime('%Y-%m-%d'),
                self.date_approved.strftime('%Y-%m-%d'),
                locale.format('%.2f', loan_amount, grouping=True, monetary=True),
                locale.format('%.2f', total_interest_amount, grouping=True, monetary=True),
                locale.format('%.2f', total_amount, grouping=True, monetary=True),
                self.date_disb.strftime('%Y-%m-%d'),
                ]
        
        data={
            'loan_data':loan_dic
            }
        return self.env.ref('hr_loan.report_loan_type_template').report_action(self,data)
    
    
class hrLoanLIne(models.Model):
    _name = 'hr.loan.line'
    _description = 'Line Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
            
    loan_id = fields.Many2one('hr.loan', string='Loan', readonly=True, required=False)
    name = fields.Char(string='Name', required=False, readonly=True)
    date_from = fields.Date(string='Date From', readonly=True)
    date_to = fields.Date(string='Date To', readonly=True)
    amount = fields.Float(string='Amount', digits=(16, 2), readonly=True)
    interest_amount = fields.Float(string='Amount Interest', digits=(16, 2), readonly=True)
    amount_total = fields.Float(string='Amount Total', digits=(16, 2), readonly=True)
    amount_paid = fields.Float(string='Amount Paid', digits=(16, 2), readonly=True)
    employee_id = fields.Many2one(related='loan_id.employee_id', string='Employee', readonly=True, store=True)
    state = fields.Selection(selection=[
                                ('unpaid', 'Unpaid'),
                                ('approve', 'Approved'),
                                ('paid', 'Paid')], 
                                string='State', readonly=True, default='unpaid',track_visibility='onchange')
    company_id = fields.Many2one('res.company', related='loan_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id', store=True)
    
class hrLoanType(models.Model):
    _name = 'hr.loan.type'
    _description = 'Loan Type'
                
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
    loan_policy_ids = fields.Many2many('hr.loan.policy', 'loan_policy_rel', 'policy_id', 'loan_type_id', string="Policies")
    active = fields.Boolean('Active', default=True)
    report_id = fields.Many2one('ir.actions.report',domain=[('model','=','hr.loan')],string="Report",)
    
    @api.onchange('interest')
    def onchange_interest(self):
        if not self.interest:
            self.interest_type = ''
            self.rate = 0

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
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('type_compnay_unique', 'unique (company_id,type)', "There is already a registered policy of this type for this company.!"),
        ('code_unique', 'unique (code)', "There is already a policy registered with this code.!"),
    ]
