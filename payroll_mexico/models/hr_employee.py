# -*- coding: utf-8 -*-

import datetime
from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.addons import decimal_precision as dp
from odoo.addons.payroll_mexico.pyfiscal.generate import GenerateRFC, GenerateCURP, GenerateNSS, GenericGeneration

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

   
    @api.multi
    def name_get(self):
        result = []
        for employee in self:
            name = '%s %s %s' %(employee.name.upper(), employee.last_name.upper() \
                if employee.last_name else '', employee.mothers_last_name.upper() \
                if employee.mothers_last_name else '')
            result.append((employee.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|',('enrollment', operator, name),('name', operator, name)]
        enrollment = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(enrollment).name_get()\

    @api.depends('name','last_name','mothers_last_name')
    @api.onchange('complete_name')
    def _compute_complete_name(self):
        for name in self:
            name.complete_name = name.name + ' ' + name.last_name + ' ' + name.mothers_last_name

    #Columns
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
    payment_period_id = fields.Many2one('hr.payment.period', "Payment period")
    bank_account_ids = fields.One2many('bank.account.employee','employee_id', "Bank account", required=True)
    group_id = fields.Many2one('hr.group', "Group", required=True)
    family_ids = fields.One2many('hr.family.burden','employee_id', "Family")
    age = fields.Integer("Age", compute='calculate_age_compute')
    infonavit_ids = fields.One2many('hr.infonavit.credit.line','employee_id', "INFONAVIT credit")
    hiring_regime_ids = fields.Many2many('hr.worker.hiring.regime', string="Hiring Regime")
    real_salary = fields.Float("Real Salary", copy=False)
    gross_salary = fields.Float("Gross Salary", copy=False)
    country_id = fields.Many2one('res.country', 'Nationality (Country)', 
        default=lambda self: self.env['res.company']._company_default_get().country_id.id, groups="hr.group_hr_user")
    country_of_birth = fields.Many2one('res.country', string="Country of Birth",
        default=lambda self: self.env['res.company']._company_default_get().country_id.id, groups="hr.group_hr_user")
    address_id = fields.Many2one(required=False)
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
    # Extra Payments
    pay_holiday = fields.Boolean('Pay holiday?', default=False, help="If checked, holidays are paid to the employee")
    pay_extra_hours = fields.Boolean('Pay extra hours?', default=False, help="If checked, extra hours are paid to the employee")
    # Health Restrictions
    health_restrictions = fields.Text('Health Restrictions', copy=False)
    emergency_address = fields.Char('Emergency address',
        copy=False, help="Set emergency contact address")
    fonacot_credit_number = fields.Char(string='Numero de prestamo')
    fonacot_amount_debt = fields.Float(string='Deuda', compute='_get_fonacot_amount_debt')
    ammount_discounted = fields.Float(string='Monto a descontar')
    last_amount_update = fields.Float(string='Ultima deuda agregada')
    fonacot_payroll = fields.Boolean(string='¿Descontar Fonacot en nómina?')
    lines_fonacot = fields.One2many(inverse_name='employee_id', comodel_name='hr.credit.employee.account')
    work_center_id = fields.Many2one('hr.work.center', "Work Center", required=False)
    # Fields Translate
    spouse_complete_name = fields.Char(string="Spouse Complete Name", groups="hr.group_hr_user")
    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups="hr.group_hr_user")
    place_of_birth = fields.Many2one('res.country.state', string='Place of Birth', groups="hr.group_hr_user")
    certificate = fields.Selection([
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('other', 'Other'),
    ], 'Certificate Level', default='master', groups="hr.group_hr_user")
    km_home_work = fields.Integer(string="Km home-work", groups="hr.group_hr_user")
    salary_type = fields.Selection([('0','Fijo'),('1','Variable'),('2','Mixto')],string="Tipo de salario", default='0')
    working_day_week = fields.Selection([('0','Completa'),
                                         ('1','Trabaja un día'),
                                         ('2','Mixto'),
                                         ('3','Trabaja tres días'),
                                         ('4','Trabaja cuatro días'),
                                         ('5','Trabaja cinco días'),
                                         ('6','Jornada reducida'),
                                         ],
                                        string="Jornada semanal",
                                        default='0')
    # Fields Translate
    # Register pattern
    employer_register_id = fields.Many2one('res.employer.register', "Employer Register", required=False)
    contract_id = fields.Many2one('hr.contract', string='Contract', store=True)
    complete_name = fields.Char(compute='_compute_complete_name', string='Nombre completo', store=True)


    _sql_constraints = [
        ('enrollment_uniq', 'unique (enrollment)', "There is already an employee with this registration.!"),
        ('enrollment_uniq', 'unique (identification_id)', "An employee with this ID already exists.!"),
        ('passport_uniq', 'unique (passport_id)', "An employee with this passport already exists.!"),
        ('rfc_uniq', 'unique (rfc)', "An employee with this RFC already exists.!"),
        ('curp_uniq', 'unique (curp)', "An employee with this CURP already exists.!"),
        ('ssnid_unique', 'unique (ssnid)', "An employee with this social security number already exists.!"),
    ]

    def get_bank(self):
        bank_ids = []
        for employee in self:
            if not employee.bank_account_ids:
                return employee.bank_account_ids
            for bank in employee.bank_account_ids:
                if bank.predetermined:
                    return bank

    @api.constrains('ssnid','rfc','curp')
    def validate_ssnid(self):
        for record in self:
            if record.ssnid and len(record.ssnid) != 11:
                raise UserError(_('The length of the social security number is incorrect'))
            # ~ if record.rfc:
                # ~ if sum(list(map(lambda x : len(x),  (list(filter(lambda x : x != '', self.rfc.split('_'))))))) != 13:
                    # ~ raise UserError(_('RFC length is incorrect'))
            if record.curp and len(record.curp) != 18:
                raise UserError(_('CURP length is incorrect'))
    
    @api.multi
    def post(self):
        for employee in self:
            if employee.enrollment == '/':
                new_enrollment = False
                group_id = employee.group_id
                if group_id.sequence_id:
                    sequence = group_id.sequence_id
                    new_enrollment = sequence.with_context().next_by_id()
                else:
                    raise UserError(_('Please define a sequence on the group.'))
                if new_enrollment:
                    employee.enrollment = new_enrollment
        return True
        
    def search_minimum_wage(self):
        for employee in self:
            zone = self.env['res.municipality.zone'].search([('municipality_id','=',employee.work_center_id.municipality_id.id)],limit=1)
            wage = self.env['table.minimum.wages'].search([],limit=1)
            wage_minimum = 0
            if zone.zone == 'freezone':
                wage_minimum = wage.border_crossing
            elif zone.zone == 'singlezone':
                wage_minimum = wage.zone_a
        return wage_minimum

    @api.model
    def create(self, vals):
        # ~ if vals.get('enrollment', _('/')) == _('/'):
            # ~ vals['enrollment'] = self.env['ir.sequence'].next_by_code('Employee') or _('/')
        res = super(Employee, self).create(vals)
        # ~ name = res.group_id.name[0:3].upper()
        # ~ if res.department_id:
            # ~ name += '-'+res.department_id.name.upper()[0:3]
        # ~ res.enrollment = name+'-'+res.enrollment
        
        res.post()
        return res
    
    @api.multi
    def write(self, vals):
        res = super(Employee, self).write(vals)
        if 'group_id' in vals:
            self.post()
        return res
    
    @api.onchange('company_id')
    def _onchange_company(self):
        address = self.company_id.partner_id.address_get(['default'])
        self.address_id = address['default'] if address else False
        self.employer_register_id = False

    # ~ @api.onchange('ssnid')
    # ~ def _check_social_security_number_length(self):
        # ~ if self.ssnid:
            # ~ if len(self.ssnid) != 11:
                # ~ raise UserError(_('The length of the social security number is incorrect'))
    
    # ~ @api.onchange('rfc')
    # ~ def _check_rfc_length(self):
        # ~ if self.rfc:
            # ~ if sum(list(map(lambda x : len(x),  (list(filter(lambda x : x != '', self.rfc.split('_'))))))) != 13:
                # ~ raise UserError(_('RFC length is incorrect'))
                
    # ~ @api.onchange('curp')
    # ~ def _check_curp_length(self):
        # ~ if self.curp:
            # ~ if len(self.curp) != 18:
                # ~ raise UserError(_('CURP length is incorrect'))
    
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
                today = date.today()
                table_id = self.env['table.settings'].search([('year','=',int(today.year))],limit=1)
                days = employee.group_id.days
                
                # ~ calculation of wages and salaries
                
                daily_salary = employee.wage_salaries/days
                minimum_integration_factor = 1.0452
                
                integrated_daily_wage = daily_salary * minimum_integration_factor
                salary = daily_salary*days
                lower_limit = 0
                applicable_percentage = 0
                fixed_fee = 0
                for table in table_id.isr_monthly_ids:
                    if salary > table.lim_inf and salary < table.lim_sup:
                        lower_limit = table.lim_inf
                        applicable_percentage = (table.s_excedente)/100
                        fixed_fee = table.c_fija
                lower_limit_surplus = salary - lower_limit
                marginal_tax = lower_limit_surplus*applicable_percentage
                isr_113 = marginal_tax + fixed_fee
                employment_subsidy = 0
                for tsub in table_id.isr_monthly_subsidy_ids:
                    if salary > tsub.lim_inf and salary < tsub.lim_sup:
                        employment_subsidy = tsub.s_mensual
                total_perceptions = salary+employment_subsidy
                risk_factor = employee.group_id.get_risk_factor(today)[0]
                work_irrigation = (integrated_daily_wage * risk_factor * days)/100
                uma = table_id.uma_id.daily_amount
                benefits_kind_fixed_fee_pattern = (uma*table_id.em_fixed_fee*days)/100
                benefits_kind_surplus_standard = 0
                if integrated_daily_wage - (uma * 3) > 0:
                    benefits_kind_surplus_standard = integrated_daily_wage - (uma * 3) * (table_id.em_surplus_p/100) * days
                benefits_excess_insured_kind = 0
                if integrated_daily_wage - (uma * 3) > 0:
                    benefits_excess_insured_kind = (integrated_daily_wage - (uma * 3)) * (table_id.em_surplus_e/100) * days
                benefits_employer_unique_money = integrated_daily_wage * (table_id.em_cash_benefits_p/100) * days
                benefits_insured_single_money = integrated_daily_wage * (table_id.em_cash_benefits_e/100) * days
                pensioned_medical_expenses_employer = integrated_daily_wage * (table_id.em_personal_medical_expenses_p/100) * days
                pensioned_medical_expenses_insured = integrated_daily_wage * (table_id.em_personal_medical_expenses_e/100) * days
                disability_life_employer = integrated_daily_wage * (table_id.disability_life_p/100) * days
                disability_life_insured = integrated_daily_wage * (table_id.disability_life_e/100) * days
                childcare_social_security_expenses_employer = integrated_daily_wage * (table_id.nursery_social_benefits/100) * days
                total_imss_employee = benefits_excess_insured_kind + benefits_insured_single_money + pensioned_medical_expenses_insured + disability_life_insured
                unemployment_old_age_insured = integrated_daily_wage * (table_id.unemployment_old_age_e/100) * days
                total_rcv_infonavit = unemployment_old_age_insured
                total_deductions = isr_113  + total_imss_employee + total_rcv_infonavit
                employee.wage_salaries_gross = employee.wage_salaries + total_deductions
                employee.assimilated_salary = employee.monthly_salary - employee.wage_salaries - employee.free_salary
                employee.free_salary_gross = employee.free_salary
                
                # ~ calculation for assimilates

                daily_salary_assimilated = employee.assimilated_salary/days
                salary_assimilated = daily_salary_assimilated*days
                fixed_fee_assimilated = 0
                applicable_percentage_assimilated = 0
                applicable_percentage_assimilated = 0
                for table in table_id.isr_monthly_ids:
                    if salary_assimilated > table.lim_inf and salary_assimilated < table.lim_sup:
                        lower_limit_assimilated = table.lim_inf
                        applicable_percentage_assimilated = (table.s_excedente)/100
                        fixed_fee_assimilated = table.c_fija
                lower_limit_surplus_assimilated = salary_assimilated - lower_limit_assimilated
                marginal_tax_assimilated = lower_limit_surplus_assimilated*applicable_percentage_assimilated
                isr_assimilated = marginal_tax_assimilated + fixed_fee_assimilated
                employee.assimilated_salary_gross = employee.assimilated_salary + isr_assimilated
        return True

    def set_required_field(self, field_name):
        raise UserError(_('The following fields are required: %s.') %field_name)

    def set_gender_format(self, gender):
        if gender == 'male':
            return 'H'
        if gender == 'female':
            return 'M'

    def get_rfc_curp_data(self):
        
        kwargs = {
            "complete_name": self.name if self.name else self.set_required_field(self.fields_get()['name']['string']),
            "last_name": self.last_name if self.last_name else self.set_required_field(self.fields_get()['last_name']['string']),
            "mother_last_name": self.mothers_last_name if self.mothers_last_name else None,
            "birth_date": self.birthday.strftime('%d-%m-%Y') if self.birthday else self.set_required_field(self.fields_get()['birthday']['string']),
            "gender": self.set_gender_format(self.gender) if self.gender else self.set_required_field(self.fields_get()['gender']['string']),
            "city": self.place_of_birth.name if self.place_of_birth else self.set_required_field(self.fields_get()['place_of_birth']['string']),
            "state_code": None
        }
        curp = GenerateCURP(**kwargs)
        rfc = GenerateRFC(**kwargs)
        self.curp = curp.data
        self.rfc = rfc.data
    
    
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
        return list_contract

    def _get_fonacot_amount_debt(self):
        '''
        Este metodo calcula el monto adeudado según el estado de cuenta de FONACOT
        '''
        total_credit,total_debit = sum(line.credit for line in self.lines_fonacot),sum(line.debit for line in self.lines_fonacot)
        self.fonacot_amount_debt = total_credit - total_debit

    
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


class HrGroup(models.Model):
    _name = "hr.group"

    @api.constrains('days')
    def validate_ssnid(self):
        for record in self:
            if record.days <= 0:
                raise ValidationError(_('The number of days cannot be less than or equal to zero.'))

    name = fields.Char("Name", copy=False, required=True)
    implant_id = fields.Many2one('res.partner', "Implant", required=True)
    account_executive_id = fields.Many2one('res.partner', "Account Executive", required=True)
    sequence_id = fields.Many2one('ir.sequence', string='Employee Sequence',
        help="This field contains information related to the numbering of employees established by group.", copy=False)
    code = fields.Char(string='Short Code', size=5, required=True, help="Employees of this group will enrolled using this prefix.")
    sequence_number_next = fields.Integer(string='Next Number',
        help='The next sequence number will be used for the next invoice.',
        compute='_compute_seq_number_next',
        inverse='_inverse_seq_number_next')
    type = fields.Selection([
        ('governmental', 'Proporción 30,4'),
        ('private', 'Base 30 días mensuales'),
        ], string='type', required=True)
    job_risk = fields.Selection([
        ('1', 'Clase I'),
        ('2', 'Clase II'),
        ('3', 'Clase III'),
        ('4', 'Clase IV'),
        ('5', 'Clase V'),
        ], string='Job risk', required=True)
    days = fields.Float("Days", required=True)
    risk_factor_ids = fields.One2many('hr.group.risk.factor','group_id', string="Factor de riesgo anual")
    country_id = fields.Many2one('res.country', string='Country', store=True,
        default=lambda self: self.env['res.company']._company_default_get().country_id)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    bonus_days = fields.Float(string="Bonus days", required=True, default=15)
    antique_table = fields.Many2one('tablas.antiguedades', string='Antique table', required=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique (code)', "A registered code already exists, modify and save the document.!"),
    ]
    
    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            if len(self.name) >= 3:
                self.code = self.name[0:3].upper()
            else:
                raise UserError(_('The group name must contain three or more characters.'))

    @api.onchange('type')
    def onchange_type(self):
        if self.type:
            if self.type == 'governmental':
                self.days = 30.4
            if self.type == 'private':
                self.days = 30.0

    @api.onchange('code')
    def onchange_code(self):
        if self.code:
            if len(self.code) == 3:
                self.code = self.code[0:3].upper()
            else:
                raise UserError(_('The group code must contain only three characters.'))

    @api.multi
    # do not depend on 'sequence_id.date_range_ids', because
    # sequence_id._get_current_sequence() may invalidate it!
    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for group in self:
            if group.sequence_id:
                sequence = group.sequence_id._get_current_sequence()
                group.sequence_number_next = sequence.number_next_actual
            else:
                group.sequence_number_next = 1

    @api.multi
    def _inverse_seq_number_next(self):
        '''Inverse 'sequence_number_next' to edit the current sequence next number.
        '''
        for group in self:
            if group.sequence_id and group.sequence_number_next:
                sequence = group.sequence_id._get_current_sequence()
                sequence.sudo().number_next = group.sequence_number_next

    @api.model
    def _get_sequence_prefix(self, code):
        prefix = code.upper()
        return prefix + '-'

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every new Group"""
        prefix = self._get_sequence_prefix(vals['code'])
        seq_name = _('Group: ') + vals['code'] + ' ' + _(vals['name'])
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 5,
            'number_increment': 1,
        }
        seq = self.env['ir.sequence'].create(seq)
        return seq

    @api.model
    def create(self, vals):
        # We just need to create the relevant sequences according to the chosen options
        if not vals.get('sequence_id'):
            vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})
        return super(HrGroup, self).create(vals)

    @api.multi
    def write(self, vals):
        for group in self:
            if ('code' in vals and group.code != vals['code']):
                if self.env['hr.employee'].search([('group_id', 'in', self.ids)], limit=1):
                    raise UserError(_('This group already contains items, therefore you cannot modify its name.'))
                new_prefix = self._get_sequence_prefix(vals['code'])
                group.sequence_id.write({'prefix': new_prefix})
        return super(HrGroup, self).write(vals)

    def get_risk_factor(self, date_factor):
        risk_factor = 0.0
        for group in self:
            if group.risk_factor_ids:
                factor_ids = group.risk_factor_ids.filtered(
                    lambda factor: date_factor >= factor.date_from \
                    and date_factor <= factor.date_to)
                if factor_ids:
                    risk_factor = factor_ids.mapped('risk_factor')
                else:
                    risk_factor = 0.0
        return risk_factor
        

class HrGroupRiskFactor(models.Model):
    _name = "hr.group.risk.factor"
    _description="Annual Risk Factor"
    
    group_id = fields.Many2one('hr.group', string="group")
    risk_factor = fields.Float(string="Risk Factor", required=True, digits=dp.get_precision('Risk'))
    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)


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
    
    @api.depends('type')
    def _search_uma(self):
        for employee in self:
            if employee.type == 'umas':
                today = date.today()
                employee.uma = self.env['table.uma'].search([('year','=',int(today.year))],limit=1).daily_amount
    
    employee_id = fields.Many2one('hr.employee', "Employee", required=False)
    infonavit_credit_number = fields.Char("INFONAVIT Credit Number", copy=False, required=True)
    value = fields.Float("Value", copy=False, required=False)
    date = fields.Date("Date", required=True)
    uma = fields.Float('UMA', compute="_search_uma")
    type = fields.Selection([
        ('percentage', 'Percentage'),
        ('umas', 'UMAS'),
        ('fixed_amount', 'Fixed Amount'),
    ],default="percentage", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ],default="draft")
    history_ids = fields.One2many(inverse_name='credit_id', comodel_name='hr.infonavit.credit.history', string='Historico de cambios')
    
    @api.multi
    def action_active(self):
        for credit in self:
            infonavit = self.search([('employee_id', '=', self.employee_id.id),('state', '=', 'active')])
            if not infonavit:
                credit.state = 'active'
                self._set_to_history(name='Activando cobro de credito', move_type='0')
            else:
                raise UserError(_("An active INFONAVIT credit already exists for the employee."))
            
    @api.multi
    def action_reset(self):
        for credit in self:
            credit.state = 'draft'
            credit._set_to_history(name='Reiniciando credito', move_type='4')\

    @api.multi
    def action_close(self):
        for credit in self:
            credit.state = 'closed'
            credit._set_to_history(name='Cerrando credito', move_type='3')

    @api.model
    def create(self, vals):
        '''
        Este metodod ejecuta el metodo _set_to_history al momento de crear credito infonavit.
        '''
        res = super(hrInfonavitCreditLine, self).create(vals)
        self._set_to_history()
        return res

    def _set_to_history(self, name, move_type):
        '''
        Este metodo agrega al historico los cambios correspondientes al credito infonavit
        '''
        vals = {
            'name': 'name',
            'move_type': move_type,
            'discount_value': self.value,
            'discount_type': self.type,
            'apply_discount':True if self.state == 'active' else False ,
            'credit_id':self.id,
            }
        self.env['hr.infonavit.credit.history'].create(vals)


            
class hrInfonavitCreditHistory(models.Model):
    _name='hr.infonavit.credit.history'

    name = fields.Char(string='Name')
    move_type = fields.Selection([('0','Inicio de descuento'),('2','Stop'),('3','Reinicio'),('4','Cierre')],string='Tipo de movimiento')
    discount_value = fields.Float(string='Valor de descuento')
    discount_type = fields.Selection([
                                    ('percentage', 'Percentage'),
                                    ('umas', 'UMAS'),
                                    ('fixed_amount', 'Fixed Amount')],string='Tipo de descuento')
    apply_discount = fields.Boolean(string='Aplica descuento')
    credit_id = fields.Many2one(comodel_name='hr.infonavit.credit.line', string='Credito')

class hrWorkerHiringRegime(models.Model):
    _name = "hr.worker.hiring.regime"
    
    name = fields.Char("Name", copy=False, required=True)
    code = fields.Char("code", copy=False, required=True)


class HrWorkCenters(models.Model):
    _name = "hr.work.center"

    def _default_country(self):
        country_id = self.env['res.country'].search([('code','=','MX')], limit=1)
        return country_id

    name = fields.Char("Name", copy=False, required=True)
    code = fields.Char("code", copy=False, required=True)
    group_id = fields.Many2one('hr.group', string="Group")
    country_id = fields.Many2one('res.country', default=_default_country, string="Country")
    city = fields.Char(string="City")
    state_id = fields.Many2one('res.country.state', string="Fed. State")
    zip = fields.Char(string="ZIP")
    municipality_id = fields.Many2one('res.country.state.municipality', string='Municipality')
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    active = fields.Boolean(default=True)
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The work center name must be unique !'),
        ('code_uniq', 'code (name)', 'The work center code must be unique !')
    ]


class Country(models.Model):
    _inherit = "res.country"
    
    nationality = fields.Char("Nationality", copy=False, required=False)


class hrCreditsEmployeeAccount(models.Model):
    _name = 'hr.credit.employee.account'

    #Columns
    name = fields.Char("Name", required = True)
    date = fields.Date("Date", required = True)
    credit = fields.Float("Credit", required = True)
    debit = fields.Float("Debit", required = True)
    employee_id = fields.Many2one(comodel_name='hr.employee')

    def create_move(self, description, date=False, credit=0.0, debit=0.0, employee=False):
        '''
        Este metodo generara los movimientos para el estado de cuenta del credito de fonacot

        '''
        vals = {
            'name': description,
            'date': date or fields.Date.context_today(self),
            'credit': credit,
            'debit': debit,
            'employee_id': employee.id,
        }
        return self.create(vals)
