# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from .tool_convert_numbers_letters import numero_to_letras
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta
import calendar

class Contract(models.Model):

    _inherit = 'hr.contract'

    @api.multi
    @api.constrains('employee_id', 'contracting_regime', 'company_id', 'state')
    def _check_contract(self):
        if not self.company_id and self.contracting_regime not in ['05']:
            raise ValidationError(_(
                'Select the company for the contract, if there is no company field in the form view, activate the multi company option'))
        contracting_regime = dict(
            self._fields['contracting_regime']._description_selection(
                self.env)).get(self.contracting_regime)
        domain = [
            ('employee_id','=', self.employee_id.id),
            ('company_id','=', self.company_id.id),
            ('contracting_regime','=', self.contracting_regime),
            ('state','=','open')
        ]
        contract = self.env['hr.contract'].search(domain)
        if len(contract) > 1:
            raise ValidationError(_(
                'There is already an open contract with the hiring regime "%s" for the employee "%s".') % (
                                  contracting_regime, self.employee_id.name))

    @api.one
    def _get_years_antiquity(self):
        '''
        Este metodo obtiene la antiguedad del contrato
        :return:
        '''
        date_end = fields.Date.today()
        if self.date_end and self.date_end < date_end:
            date_end = self.date_end + timedelta(days=1)
        date_start_contract =  self.previous_contract_date or self.date_start
        days_antiquity = (date_end - date_start_contract).days
        years_antiquity = int(days_antiquity/365)
        days_rest = int(days_antiquity%365)
        self.years_antiquity = years_antiquity
        self.days_rest = days_rest

    def _set_sequence_code(self):
        return self.env['ir.sequence'].with_context(force_company=self.env.user.company_id.id).next_by_code('Contract')

    # def _default_bank_account(self):
    #     return self.env['res.partner.category'].browse(self._context.get('category_id'))

    #Columns
    code = fields.Char('Code',required=True, default=_set_sequence_code)
    type_id = fields.Many2one(string="Type Contract")
    type_contract = fields.Selection(string="Type", related="type_id.type", invisible=True)
    company_id = fields.Many2one('res.company', default = ['employee_id','=', False], required=False)
    previous_contract_date = fields.Date('Previous Contract Date', help="Start date of the previous contract for antiquity.")
    power_attorney_id = fields.Many2one('company.power.attorney',string="Power Attorney")
    contracting_regime = fields.Selection([
        ('02', 'Wages and salaries'),
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
    ], string='Contracting Regime', required=True, default="02")
    years_antiquity = fields.Integer(string='Antiquity', compute='_get_years_antiquity')
    days_rest = fields.Integer(string='Días de antigüedad ultimo año', compute='_get_years_antiquity')
    integral_salary= fields.Float(string="SDI", copy=False)
    group_id = fields.Many2one('hr.group', "Grupo", store=True, related='employee_id.group_id')
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", store=True, related='employee_id.work_center_id')
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", store=True, related='employee_id.employer_register_id')
    fixed_concepts_ids = fields.One2many('hr.fixed.concepts','contract_id', "Fixed concepts")
    structure_type_id = fields.Many2one('hr.structure.types', string="Structure Types")
    bank_account_id = fields.Many2one('bank.account.employee', string="Bank account")

    @api.onchange('employee_id')
    def onchange_employee_id_default_bank_account(self):
        if self.employee_id:
            bank_account = self.employee_id.get_bank()
            if bank_account:
                self.bank_account_id = bank_account.id
            else:
                self.bank_account_id = False

    @api.multi
    def action_open(self):
        report=self.type_id.report_id
        if not report and self.contracting_regime == '02':
            raise ValidationError('Debe seleccionar el tipo de informe de contrato en el campo "Tipo de contrato".')
        return self.write({'state': 'open'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})
        
    @api.multi
    def action_cancel(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def action_pending(self):
        return self.write({'state': 'pending'})
        
    def action_close(self):
        if not self.date_end:
            raise ValidationError('Primero debe asignar la fecha de finalización del contrato.')
        else:
            to_date = fields.Date.today()
            if self.date_end > to_date:
                raise ValidationError('No puede cerrar un contrato con fecha de vigencia')
            if self.contracting_regime != '02':
                val = {
                    'contract_id':self.id,
                    'employee_id':self.employee_id.id,
                    'type':'02',
                    'reason_liquidation':'1',
                    'date':self.previous_contract_date or self.date_start,
                    'wage':self.wage,
                    'salary':self.integral_salary,
                }
                self.env['hr.employee.affiliate.movements'].create(val)
        return self.write({'state': 'close'})

    
    def compensation_20_days(self,payslip,SDI):
        compensation = 0
        if int(payslip.years_antiquity) == 0:
            compensation = (payslip.days_rest/2)*float(SDI)
        else:
            if payslip.contract_id.type_id.code in ['02','03']:
                for i in range(1,int(payslip.years_antiquity)+1):
                    if i == 1:
                        compensation += float(SDI)*180
                    else:
                        compensation += 20*float(SDI)
                if payslip.days_rest > 0:
                    proportion_days = (payslip.days_rest * 20)/365
                    compensation += proportion_days*float(SDI)
            else:
                for i in range(1,int(payslip.years_antiquity)+1):
                    compensation += 20*float(SDI)
                if payslip.days_rest > 0:
                    proportion_days = (payslip.days_rest * 20)/365
                    compensation += proportion_days*float(SDI)
        return compensation
                                                              
    def get_monthly_taxable_total(self,year,month,date_from,date_to,G190):
        taxable = 0
        day = calendar.monthrange(int(year), int(month))[1]
        date = str(year)+'-'+str(month)+'-'+str(day)
        date = datetime.strptime(date, '%Y-%m-%d').date()
        if date_from < date and date_to >= date:
            taxable = sum(self.env['hr.payslip.line'].search([('category_id.code','=','BRUTOG'),
                                                              ('employee_id','=',self.employee_id.id),
                                                              ('contract_id','=',self.id),
                                                              ('slip_id.payroll_month','=',month),
                                                              ('slip_id.year','=',year),
                                                              ('slip_id.state','=','done'),]).mapped('total'))
            if taxable > 0:
                taxable += G190
        return taxable
        
    def subsidy_paid(self,payroll_month):
        subsidy = sum(self.env['hr.payslip.line'].search([('category_id.code','=','PERCEPCIONES'),
                                                          ('salary_rule_id.type_other_payment','=','002'),
                                                          ('employee_id','=',self.employee_id.id),
                                                          ('contract_id','=',self.id),
                                                          ('slip_id.payroll_month','=',payroll_month),
                                                          ('slip_id.state','=','done'),]).mapped('total'))
        return subsidy
        
    def adjustment_subsidy_caused(self,payroll_month):
        subsidy = sum(self.env['hr.payslip.line'].search([('salary_rule_id.code','=','UI106'),
                                                          ('employee_id','=',self.employee_id.id),
                                                          ('contract_id','=',self.id),
                                                          ('slip_id.payroll_month','=',payroll_month),
                                                          ('slip_id.state','=','done'),]).mapped('total'))
        return subsidy
        
    @api.multi
    def get_all_structures(self,struct_id):
        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = struct_id
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))
    
    @api.onchange('company_id')
    def onchange_default_power_attorney(self):
        for contract in self:
            power = self.env['company.power.attorney'].search([('company_id','=',contract.company_id.id),('state','in',['valid']),('predetermined','=',True)])
            if power:
                contract.power_attorney_id = power.id
            else:
                power = self.env['company.power.attorney'].search([('company_id','=',contract.company_id.id),('state','in',['valid'])], limit=1)
                if power:
                    contract.power_attorney_id = power.id 
    
    def print_contract(self):
        contract_dic = {}
        mensaje = []
        for contract in self:
            employee=contract.employee_id
            if not employee:
                mensaje.append('Debe llenar el campo empleado en la ficha del Contrato \n')
            
            company=contract.company_id
            if not company:
                mensaje.append('Debe llenar el campo Compañia en el contrato \n')
            
            birthday=contract.employee_id.birthday
            if not birthday:
                mensaje.append('Debe llenar la fecha de nacimiento en la ficha de empleado \n')
            
            const_date=contract.company_id.constitution_date
            if not const_date:
                mensaje.append('Debe llenar la fecha Constitucion de la compañia \n')
            
            title_emplo=contract.employee_id.title.shortcut
            if not title_emplo:
                mensaje.append('Debe llenar el titulo en la ficha de empleado \n')
            
            title_repre=contract.company_id.legal_representative_id.title
            if not title_repre:
                mensaje.append('Debe llenar el titulo del representante legal en la ficha de compañia \n')
            
            direccion=contract.employee_id.address_home_id
            if not direccion:
                mensaje.append('Debe llenar la dirección de la ficha de empleado \n')
            
            dir_state=contract.employee_id.address_home_id.state_id
            if not dir_state:
                mensaje.append('Debe llenar el estado en la dirección de la ficha de empleado \n')
            
            report=self.type_id.report_id
            if not report:
                mensaje.append('Debe llenar el campo reporte dentro de la categoria de empleado \n')
                
            job=self.job_id
            if not job:
                mensaje.append('Debe llenar el campo puesto de trabajo en la ficha del contrato \n')
                
            rfc=self.employee_id.rfc
            if not rfc:
                mensaje.append('Debe llenar el campo RFC en la ficha del empleado \n')
                
            curp=self.employee_id.curp
            if not curp:
                mensaje.append('Debe llenar el campo CURP en la ficha del empleado \n')
                
            country=self.employee_id.country_id
            if not country:
                mensaje.append('Debe llenar el campo país en la ficha del empleado \n')
                
            nationality=self.employee_id.country_id.nationality
            if not nationality:
                mensaje.append('Debe llenar el campo nacionalidad donde se registra país en la parte técnica del sistema \n')
                
            if len(mensaje):
                msg="".join(mensaje)
                raise  UserError(_(msg))
            date = self.date_start
            previous_contract_date = ''
            if self.type_id.type == 'with_seniority':
                previous_contract_date = self.previous_contract_date.strftime('%d')+' del mes de '+self.previous_contract_date.strftime('%B').upper()+' de '+self.previous_contract_date.strftime('%Y')
            
            contract_dic[contract.id]=[date.strftime('%d')+' días del mes de '+date.strftime('%B').upper()+' de '+numero_to_letras(int(date.strftime('%Y'))).lower(),
            previous_contract_date,contract.employee_id.birthday.strftime('%d/%m/%Y'),
            contract.company_id.constitution_date.strftime('%d')+' de '+contract.company_id.constitution_date.strftime('%B').upper()+' de '+contract.company_id.constitution_date.strftime('%Y'),
            date.strftime('%d')+' de '+date.strftime('%B').upper()+' '+date.strftime('%Y'),
            date.strftime('%d')+' días del mes de '+date.strftime('%B').upper()+' de '+date.strftime('%Y'),
            ]
        data={
            'contract_data':contract_dic
            }
        return self.env.ref('payroll_mexico.report_contract_type_template').report_action(self,data)

    
    def time_worked_year(self,date_payroll,settlement=None):
        date_from = self.date_start
        date_to = self.date_end
        days = 0
        if self.type_id.type == 'with_seniority':
            date_from = self.previous_contract_date
        date1 =datetime.strptime(str(str(date_payroll.year)+'-01-01'), DEFAULT_SERVER_DATE_FORMAT).date()
        if date_from <= date1:
            days = 365
            if settlement:
                date2 =datetime.strptime(str(str(date_payroll.year)+'-01-01'), DEFAULT_SERVER_DATE_FORMAT).date()
                days =  (date_to - date2).days
        else:
            if not settlement:
                date2 =datetime.strptime(str(str(date_payroll.year)+'-12-31'), DEFAULT_SERVER_DATE_FORMAT).date()
                days = (date2 - date_from).days
            else:
                days = (date_to - date_from).days
        worked_days = self.env['hr.payslip.worked_days']
        days_discount = sum(worked_days.search([('payslip_id.employee_id','=',self.employee_id.id),
                                            ('code','in',['F01','F04']),
                                            ('payslip_id.year','=',str(date_payroll.year)),
                                            ('payslip_id.state','in',['done']),
                                            ('payslip_id.payroll_type','in',['O'])]).mapped('number_of_days'))
        
        days = days - days_discount
        if days < 0:
            days = 0
        return days

    def holiday_calculation_finiquito(self,date_payroll):
        date_from = self.date_start
        date_to = self.date_end
        days = 0
        if self.type_id.type == 'with_seniority':
            date_from = self.previous_contract_date
        date1 =datetime.strptime(str(str(date_payroll.year)+'-01-01'), DEFAULT_SERVER_DATE_FORMAT).date()
        if date_from <= date1:
            date2 =datetime.strptime(str(str(date_payroll.year)+'-01-01'), DEFAULT_SERVER_DATE_FORMAT).date()
            days =  (date_to - date2).days
        else:
            days = (date_to - date_from).days
        days = days+1
        years_antiquity = self.years_antiquity
        antiquity = self.env['tablas.antiguedades.line'].search([('form_id','=',self.employee_id.group_id.antique_table.id),('antiguedad','=',years_antiquity)],limit=1)
        proportional_days = (float("{0:.4f}".format(antiquity.vacaciones/365))) * days
        return float("{0:.2f}".format(proportional_days))
        
    def search_smvdf(self,date_payroll):
        municipalities = self.env['res.country.state.municipality'].search([('state_id.code', '=', 'DIF')])
        SMVDF = municipalities[0].get_salary_min(date_payroll)
        return SMVDF
    
    def holiday_bonus(self):
        years_antiquity = self.years_antiquity
        if years_antiquity == 0:
            years_antiquity = 1
        antiquity = self.env['tablas.antiguedades.line'].search([('form_id','=',self.employee_id.group_id.antique_table.id),('antiguedad','=',years_antiquity)],limit=1)
        return antiquity.prima_vac
    
    def search_antique_table_bonus(self):
        antique = self.env['tablas.antiguedades.line'].search([('form_id','=',self.employee_id.group_id.antique_table.id),('antiguedad','=',self.years_antiquity)],limit=1)
        return antique.aguinaldo
    
    def _calculate_integral_salary(self):
        current_date  =  fields.Date.context_today(self)+timedelta(days=1)
        start_date_contract = self.previous_contract_date or self.date_start
        years_antiquity = self.years_antiquity + 1 if self.days_rest > 0 else self.years_antiquity
        antiguedad = self.env['tablas.antiguedades.line'].search([('antiguedad','=',years_antiquity),('form_id','=',self.employee_id.group_id.antique_table.id)])
        daily_salary = self.wage / self.employee_id.group_id.days if self.employee_id.group_id.days else self.wage / 30
        daily_salary = float("{0:.4f}".format(daily_salary))
        integral_salary =  daily_salary * round(((antiguedad.factor/100)+1),4)
        return float("{0:.4f}".format(integral_salary))
        
    def _get_integral_salary(self):
        '''
        Esten metodo busca el salario integral fijo para agregarlo al formulario del contrato
        '''
        contracts = self
        for contract in contracts:
            if contract.contracting_regime == '02':
                contract.integral_salary = contract._calculate_integral_salary()
    
    contracting_regime = fields.Selection([
        ('02', 'Wages and salaries'),
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
    ], string='Contracting Regime', required=True, default="02")
    
    
    def calculate_salary_scheme(self,wage):
        today = date.today()
        payroll_periods_days = {
                '05': 30,
                '04': 15,
                '02': 7,
                '10': 10,
                '01': 1,
                '99': 1,
                }
        days = payroll_periods_days[self.employee_id.payroll_period]*(self.employee_id.group_id.days/30)
        table_id = self.env['table.settings'].search([('year','=',int(today.year))],limit=1)
        risk_factor = self.employee_id.employer_register_id.get_risk_factor(today)
        years_antiquity = self.years_antiquity + 1 if self.days_rest > 0 else self.years_antiquity
        antiquity = self.env['tablas.antiguedades.line'].search([('antiguedad','=',int(years_antiquity)),('form_id','=',self.employee_id.group_id.antique_table.id)])
        amount_wage_salaries = 0
        if self.contracting_regime == '02':
            amount_wage_salaries = self.employee_id.get_value_objetive(round((wage/self.employee_id.group_id.days)*days,2), days, table_id, antiquity, risk_factor)
            amount_wage_salaries = round((amount_wage_salaries/days)*self.employee_id.group_id.days,2)
        elif self.contracting_regime in ['05','99']:
            amount_wage_salaries = wage
        else:
            amount_wage_salaries = self.employee_id.get_value_objetive(round(wage/self.employee_id.group_id.days*days,2), days, table_id, antiquity, risk_factor, True)
            amount_wage_salaries = round((amount_wage_salaries/days)*self.employee_id.group_id.days,2)
        return amount_wage_salaries
        

class FixedConcepts(models.Model):
    _name = 'hr.fixed.concepts'
    
    contract_id = fields.Many2one('hr.contract', 'Contract')
    type = fields.Selection([
        ('1', 'Punctuality bonus'),
        ('2', 'Attendance bonus'),
        ('3', 'Pantry'),
        ('4', 'Saving Fund'),
        ], string='Type', required=True)
    type_application = fields.Selection([
        ('1', 'Percentage'),
        ('2', 'Monetary'),
        ('3', 'Times SM'),
        ], string='Type aplication', required=True)
    amount = fields.Float('Amount', required=True)
    faults = fields.Boolean('Faults', help="If you select this option this perception will not be taken into account in the event that the employee incurred a fault.")
    justified_fault = fields.Boolean('Justified fault', help="If you select this option this perception will not be taken into account in the event that the employee incurred a justified fault.")
    permission_with_enjoyment = fields.Boolean('Permission with enjoyment', help="If you select this option this perception will not be taken into account in the event that the employee incurred a permission with enjoyment.")
    permission_without_enjoyment = fields.Boolean('Permission without enjoyment', help="If you select this option this perception will not be taken into account in the event that the employee incurred a permission without enjoyment.")
    disabilities = fields.Boolean('Disabilities', help="If you select this option this perception will not be taken into account in the event that the employee incurred a disabilities.")
    holidays = fields.Boolean('Holidays', help="If you select this option this perception will not be taken into account in the event that the employee incurred a disabilities.")
    
    _sql_constraints = [
        ('type_uniq', 'unique (type,contract_id)', "Verify the assignment of fixed concepts for this contract, you are trying to assign the same concept twice.!"),
        ]
    
    
class CalendarResource(models.Model):
    _inherit = 'resource.calendar'

    #Columns
    turno = fields.Selection([('0','Dia'),('1','Noche'),('2','Mixto')], default='0',string='Turno')
