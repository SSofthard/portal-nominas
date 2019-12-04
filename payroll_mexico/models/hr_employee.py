# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

import datetime
from datetime import date
from odoo.osv import expression


def calculate_age(date_birthday):
    today = date.today() 
    try: 
        birthday = date_birthday.replace(year=today.year) 
    except ValueError: 
        birthday = date_birthday.replace(year=today.year, day=date_birthday.day - 1)
    if birthday > today:          
        return today.year - date_birthday.year - 1 
    else: 
        return today.year - date_birthday.year 


class Job(models.Model):
    _inherit = "hr.job"
    
    code = fields.Char("Code", copy=False, required=True)


class Employee(models.Model):
    _inherit = "hr.employee"
    
    @api.depends('birthday')
    def calculate_age_compute(self):
        for employee in self:
            if employee.birthday:
                employee.age = calculate_age(employee.birthday)
                
    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|',('enrollment', operator, name),('name', operator, name)]
        enrollment = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(enrollment).name_get()
    
    
    enrollment = fields.Char("Enrollment", copy=False, required=True, default=lambda self: _('/'), readonly=True)
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
    salary = fields.Float("Salary", copy=False)
    payment_period_id = fields.Many2one('hr.payment.period', "Payment period")
    bank_account_ids = fields.One2many('bank.account.employee','employee_id', "Bank account", required=True)
    group_id = fields.Many2one('hr.group', "Group", required=True)
    family_ids = fields.One2many('hr.family.burden','employee_id', "Family")
    age = fields.Integer("Age", compute='calculate_age_compute')
    infonavit_ids = fields.One2many('hr.infonavit.credit.line','employee_id', "INFONAVIT credit")
    hiring_regime_ids = fields.Many2many('hr.worker.hiring.regime', string="Hiring Regime")
    real_salary = fields.Float("Real Salary", copy=False)
    gross_salary = fields.Float("Gross Salary", copy=False)
    table_id = fields.Many2one('tablas.cfdi','Table CFDI',)
    
    address_id = fields.Many2one(required=True)
    department_id = fields.Many2one(required=True)
    
    type_salary = fields.Selection([
        ('gross', 'Gross'),
        ('net', 'Net'),
    ],"Real Salary", default="gross")
    
    monthly_salary = fields.Float("Monthly Salary", copy=False)
    
    wage_salaries = fields.Float("Wages and salaries", copy=False)
    assimilated_salary = fields.Float("Assimilated Salary", copy=False)
    free_salary = fields.Float("Free", copy=False)
    
    wage_salaries_gross = fields.Float("Wages and gross wages", copy=False, readonly=True)
    assimilated_salary_gross = fields.Float("Gross Assimilated Salary", copy=False, readonly=True)
    free_salary_gross = fields.Float("Gross Free", copy=False, readonly=True)
    
    company_assimilated_id = fields.Many2one('res.company', "Company (Assimilated)", required=False)
    last_name = fields.Char("Last Name")
    mothers_last_name = fields.Char("Mother's Last Name")
    
    
    _sql_constraints = [
        ('enrollment_uniq', 'unique (enrollment)', "There is already an employee with this registration.!"),
        ('enrollment_uniq', 'unique (identification_id)', "An employee with this ID already exists.!"),
        ('passport_uniq', 'unique (passport_id)', "An employee with this passport already exists.!"),
        ('rfc_uniq', 'unique (rfc)', "An employee with this RFC already exists.!"),
        ('curp_uniq', 'unique (curp)', "An employee with this CURP already exists.!"),
        ('social_security_number_unique', 'unique (social_security_number)', "An employee with this social security number already exists.!"),
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('enrollment', _('/')) == _('/'):
            vals['enrollment'] = self.env['ir.sequence'].next_by_code('Employee') or _('/')
        res = super(Employee, self).create(vals)
        name = res.group_id.name[0:3].upper()
        if res.department_id:
            name += '-'+res.department_id.name.upper()[0:3]
        res.enrollment = name+'-'+res.enrollment
        
        
        return res
    
    @api.onchange('ssnid')
    def _check_social_security_number_length(self):
        if self.ssnid:
            if len(self.ssnid) != 11:
                raise UserError(_('The length of the social security number is incorrect'))
    
    @api.onchange('rfc')
    def _check_rfc_length(self):
        if self.rfc:
            if sum(list(map(lambda x : len(x),  (list(filter(lambda x : x != '', self.rfc.split('_'))))))) != 13:
                raise UserError(_('RFC length is incorrect'))
                
    @api.onchange('curp')
    def _check_curp_length(self):
        if self.curp:
            if len(self.curp) != 18:
                raise UserError(_('CURP length is incorrect'))
    
    @api.multi
    def calculate_salary_scheme(self):
        for employee in self:
            
            if employee.monthly_salary <= 0:
                raise UserError(_('Please indicate the monthly salary'))
                
            if employee.wage_salaries <= 0:
                raise UserError(_('The amount of wages and salaries must be greater than 0'))
                
            if employee.type_salary == 'gross':
                if employee.wage_salaries == employee.monthly_salary:
                    employee.wage_salaries_gross = employee.wage_salaries
                    employee.assimilated_salary_gross = 0
                    employee.free_salary_gross = 0
                    employee.assimilated_salary = 0
                    employee.free_salary = 0
                elif employee.wage_salaries < employee.monthly_salary:
                    employee.wage_salaries_gross = employee.wage_salaries
                    employee.free_salary_gross = employee.free_salary
                    employee.assimilated_salary = employee.monthly_salary - employee.wage_salaries - employee.free_salary
                    employee.assimilated_salary_gross = employee.monthly_salary - employee.wage_salaries - employee.free_salary
            else:
                
                days = 30
                
                # ~ calculation of wages and salaries
                daily_salary = employee.wage_salaries/days
                minimum_integration_factor = 1.0452
                integrated_daily_wage = daily_salary * minimum_integration_factor
                salary = daily_salary*days
                lower_limit = 0
                applicable_percentage = 0
                fixed_fee = 0
                for table in employee.table_id.tabla_LISR:
                    if salary > table.lim_inf and salary < table.lim_sup:
                        lower_limit = table.lim_inf
                        applicable_percentage = table.s_excedente
                        fixed_fee = table.c_fija
                lower_limit_surplus = salary - lower_limit
                marginal_tax = lower_limit_surplus*applicable_percentage
                isr_113 = marginal_tax + fixed_fee
                employment_subsidy = 0
                for tsub in employee.table_id.tabla_subem:
                    if salary > tsub.lim_inf and salary < tsub.lim_sup:
                        employment_subsidy = tsub.s_mensual
                isr = isr_113 - employment_subsidy
                total_perceptions = salary+employment_subsidy
                risk_factor = 0.54355
                work_irrigation = (integrated_daily_wage * risk_factor * days)/100
                benefits_kind_fixed_fee_pattern = (employee.table_id.uma*employee.table_id.enf_mat_cuota_fija*days)/100
                benefits_kind_surplus_standard = 0
                if integrated_daily_wage - (employee.table_id.uma * 3) > 0:
                    benefits_kind_surplus_standard = integrated_daily_wage - (employee.table_id.uma * 3) * (employee.table_id.enf_mat_excedente_p/100) * days
                benefits_excess_insured_kind = 0
                if integrated_daily_wage - (employee.table_id.uma * 3) > 0:
                    benefits_excess_insured_kind = (integrated_daily_wage - (employee.table_id.uma * 3)) * (employee.table_id.enf_mat_excedente_e/100) * days
                benefits_employer_unique_money = integrated_daily_wage * (employee.table_id.enf_mat_prestaciones_p/100) * days
                benefits_insured_single_money = integrated_daily_wage * (employee.table_id.enf_mat_prestaciones_e/100) * days
                pensioned_medical_expenses_employer = integrated_daily_wage * (employee.table_id.enf_mat_gastos_med_p/100) * days
                pensioned_medical_expenses_insured = integrated_daily_wage * (employee.table_id.enf_mat_gastos_med_e/100) * days
                disability_life_employer = integrated_daily_wage * (employee.table_id.inv_vida_p/100) * days
                disability_life_insured = integrated_daily_wage * (employee.table_id.inv_vida_e/100) * days
                childcare_social_security_expenses_employer = integrated_daily_wage * (employee.table_id.guarderia_p/100) * days
                total_imss_employee = benefits_excess_insured_kind + benefits_insured_single_money + pensioned_medical_expenses_insured + disability_life_insured
                unemployment_old_age_insured = integrated_daily_wage * (employee.table_id.cesantia_vejez_e/100) * days
                total_rcv_infonavit = unemployment_old_age_insured
                total_deductions = isr_113  + total_imss_employee + total_rcv_infonavit
                total = total_perceptions - total_deductions
                
                employee.wage_salaries_gross = employee.wage_salaries + total_deductions
                employee.assimilated_salary = employee.monthly_salary - employee.wage_salaries - employee.free_salary
                employee.free_salary_gross = employee.free_salary
                
                # ~ calculation for assimilates

                daily_salary_assimilated = employee.assimilated_salary/days
                salary_assimilated = daily_salary_assimilated*days
                fixed_fee_assimilated = 0
                applicable_percentage_assimilated = 0
                applicable_percentage_assimilated = 0
                for table in employee.table_id.tabla_LISR:
                    if salary_assimilated > table.lim_inf and salary_assimilated < table.lim_sup:
                        lower_limit_assimilated = table.lim_inf
                        applicable_percentage_assimilated = table.s_excedente
                        fixed_fee_assimilated = table.c_fija
                lower_limit_surplus_assimilated = salary_assimilated - lower_limit_assimilated
                marginal_tax_assimilated = lower_limit_surplus_assimilated*applicable_percentage_assimilated
                isr_assimilated = marginal_tax_assimilated + fixed_fee_assimilated
                employee.assimilated_salary_gross = employee.assimilated_salary + isr_assimilated
        return True
        
    @api.multi
    def generate_contracts(self, type_id, date):
        for employee in self:
            contract_obj = self.env['hr.contract']
            contarct = contract_obj.search([('employee_id','=',employee.id),('contracting_regime','in',['1','2','5']),('state','in',['open'])])
            list_contract =[]
            if contarct:
                raise UserError(_('The employee has currently open contracts.'))
            if not employee.company_id:
                raise UserError(_('You must select a company for the salary and salary contract.'))
            if not employee.company_assimilated_id:
                raise UserError(_('You must select a company for the salary-like contract.'))
            if employee.wage_salaries_gross > 0:
                val = {
                    'name':employee.name+' - '+'Sueldos y Salarios',
                    'employee_id':employee.id,
                    'department_id':employee.department_id.id,
                    'job_id':employee.job_id.id,
                    'wage':employee.wage_salaries_gross,
                    'contracting_regime':'2',
                    'company_id':employee.company_id.id,
                    'type_id':type_id.id,
                    'date_start':date,
                        }
                list_contract.append(contract_obj.create(val).id)
            if employee.assimilated_salary_gross > 0:
                val = {
                    'name':employee.name+' - '+'Asimilado',
                    'employee_id':employee.id,
                    'department_id':employee.department_id.id,
                    'job_id':employee.job_id.id,
                    'wage':employee.assimilated_salary_gross,
                    'contracting_regime':'1',
                    'company_id':employee.company_assimilated_id.id,
                    'type_id':type_id.id,
                    'date_start':date,
                        }
                list_contract.append(contract_obj.create(val).id)
            if employee.free_salary_gross > 0:
                val = {
                    'name':employee.name+' - '+'Libre',
                    'employee_id':employee.id,
                    'department_id':employee.department_id.id,
                    'job_id':employee.job_id.id,
                    'wage':employee.free_salary_gross,
                    'contracting_regime':'5',
                    'company_id':employee.company_id.id,
                    'type_id':self.env.ref('payroll_mexico.hr_contract_type_services_other').id,
                    'date_start':date,
                        }
                list_contract.append(contract_obj.create(val).id)
            employee.salary = employee.wage_salaries_gross
        return list_contract
        
    
class paymentPeriod(models.Model):
    _name = "hr.payment.period"
    
    name = fields.Char("Name", copy=False, required=True)
    
class bankDetailsEmployee(models.Model):
    _name = "bank.account.employee"
    
    employee_id = fields.Many2one('hr.employee', "Employee", required=False)
    bank_id = fields.Many2one('res.bank', "Bank", required=True)
    beneficiary = fields.Char("Beneficiary", copy=False, required=True)
    bank_account = fields.Char("Bank account", copy=False, required=True)
    reference = fields.Char("Reference", copy=False, required=True)
    location_branch = fields.Char("Location / Branch")
    predetermined = fields.Boolean("Predetermined", copy=False, required=False)
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ],default="active")
    
    _sql_constraints = [
        ('predetermined_uniq', 'unique (employee_id,predetermined)', "There is already a default account number for this employee.!"),
    ]
    
    @api.multi
    def action_active(self):
        for account in self:
            account.state = 'active'
            
    @api.multi
    def action_inactive(self):
        for account in self:
            account.state = 'inactive'
    

class resBank(models.Model):
    _inherit = "res.bank"
    
    business_name = fields.Char("Business name", copy=False, required=False)
    clabe = fields.Char("Clabe", copy=False, required=False)
    code = fields.Char("Code", copy=False, required=False)

class hrGroup(models.Model):
    _name = "hr.group"
    
    name = fields.Char("Name", copy=False, required=True)
    implant_id = fields.Many2one('res.partner', "Implant", required=True)
    account_executive_id = fields.Many2one('res.partner', "Account Executive", required=True)
    
class hrFamilyBurden(models.Model):
    _name = "hr.family.burden"
    
    @api.depends('birthday')
    def calculate_age_compute(self):
        for family in self:
            if family.birthday:
                family.age = calculate_age(family.birthday)
    
    employee_id = fields.Many2one('hr.employee', "Employee", required=False)
    name = fields.Char("Name", copy=False, required=True)
    birthday = fields.Date("Birthday", required=True)
    age = fields.Integer("Age", compute='calculate_age_compute')
    relationship_id = fields.Many2one("hr.relationship","Relationship", required=True)

class hrRelationship(models.Model):
    _name = "hr.relationship"
    
    name = fields.Char("Name", copy=False, required=True)
    
class hrInfonavitCreditLine(models.Model):
    _name = "hr.infonavit.credit.line"
    
    employee_id = fields.Many2one('hr.employee', "Employee", required=False)
    infonavit_credit_number = fields.Char("INFONAVIT Credit Number", copy=False, required=True)
    value = fields.Float("Value", copy=False, required=False)
    date = fields.Date("Date", required=True)
    type = fields.Selection([
        ('umas', 'UMAS'),
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ],default="day", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ],default="draft")
    
    @api.multi
    def action_active(self):
        for credit in self:
            infonavit = self.search([('employee_id', '=', self.employee_id.id),('state', '=', 'active')])
            if not infonavit:
                credit.state = 'active'
            else:
                raise UserError(_("An active INFONAVIT credit already exists for the employee."))
            
    @api.multi
    def action_close(self):
        for credit in self:
            credit.state = 'closed'
            
    
    
class hrWorkerHiringRegime(models.Model):
    _name = "hr.worker.hiring.regime"
    
    name = fields.Char("Name", copy=False, required=True)
    code = fields.Char("code", copy=False, required=True)
    

class Country(models.Model):
    _inherit = "res.country"
    
    nationality = fields.Char("Nationality", copy=False, required=False)
