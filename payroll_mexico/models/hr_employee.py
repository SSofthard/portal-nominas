# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Job(models.Model):
    _inherit = "hr.job"
    
    code = fields.Char("Code", copy=False, required=True)


class Employee(models.Model):
    _inherit = "hr.employee"
    
    enrollment = fields.Char("Enrollment", copy=False, required=True)
    title = fields.Many2one('res.partner.title','Title')
    rfc = fields.Char("RFC", copy=False)
    curp = fields.Char("CURP", copy=False)
    personal_email = fields.Char("Personal Email", copy=False)
    personal_movile_phone = fields.Char("Personal movile phone", copy=False)
    personal_phone = fields.Char("Personal phone", copy=False)
    blood_type = fields.Selection([
        ('O-', 'O-'),
        ('O+', 'O+'),
        ('A-', 'A-'),
        ('A+', 'A+'),
        ('B-', 'B-'),
        ('B+', 'B+'),
        ('AB-', 'AB-'),
        ('AB+', 'AB+'),
        ], string='Blood type', required=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], groups="hr.group_hr_user", default="male")
    social_security_number = fields.Char("Social Security Number", copy=False)
    salary = fields.Float("Salary", copy=False)
    payment_period_id = fields.Many2one('hr.payment.period', "Payment period")
    bank_account_ids = fields.One2many('bank.account.employee','employee_id', "Bank account", required=True)
    
    @api.onchange('social_security_number')
    def _check_social_security_number_length(self):
        if self.social_security_number:
            if len(self.social_security_number) != 11:
                raise UserError(_('The length of the social security number is incorrect'))
    
    @api.onchange('rfc')
    def _check_rfc_length(self):
        if self.rfc:
            if len(self.rfc) != 12 or len(self.rfc) != 13:
                raise UserError(_('RFC length is incorrect'))

    
class paymentPeriod(models.Model):
    _name = "hr.payment.period"
    
    name = fields.Char("Name", copy=False, required=True)
    
class bankDetailsEmployee(models.Model):
    _name = "bank.account.employee"
    
    employee_id = fields.Many2one('hr.employee', "Bank", required=True)
    bank_id = fields.Many2one('res.bank', "Bank", required=True)
    beneficiary = fields.Char("Beneficiary", copy=False, required=True)
    bank_account = fields.Char("Bank account", copy=False, required=True)
    predetermined = fields.Boolean("Predetermined", copy=False, required=False)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ],default="active")
    
    _sql_constraints = [
        ('predetermined_uniq', 'unique (employee_id,predetermined)', "There is already a default account number for this employee.!"),
    ]

class resBank(models.Model):
    _inherit = "res.bank"
    
    business_name = fields.Char("Business name", copy=False, required=False)
    code = fields.Char("Code", copy=False, required=False)
    


