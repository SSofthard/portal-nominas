# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from .tool_convert_numbers_letters import numero_to_letras
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta


class Contract(models.Model):

    _inherit = 'hr.contract'

    @api.multi
    @api.constrains('employee_id', 'contracting_regime', 'company_id', 'state')
    def _check_contract(self):
        vals=[(self.employee_id.id,self.company_id.id,self.contracting_regime,self.state)]
        contracting_regime = {1: 'Asimilado a salarios',
            2: 'Sueldos y salarios',3: 'Jubilados',
            4: 'Pensionados',5: 'Libre'}
        regimen=contracting_regime.get(int(self.contracting_regime))
        lista_contract=[]
        contr = self.env['hr.contract'].search([
                        ('employee_id', '=', self.employee_id.id), 
                        ])
        for contract in contr:
            if self.state == 'open':
                if contract.id != self.id:
                    lista_contract=[(contract.employee_id.id,
                            contract.company_id.id,
                            contract.contracting_regime,
                            contract.state)]
                    if lista_contract == vals:
                        raise ValidationError(_('Ya existe un contrato en proceso, del empleado (%s) \
                            para el régimen (%s).') % (self.employee_id.name,regimen))

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
        years_antiquity = int(days_antiquity/365.25)
        days_rest = int(days_antiquity%365.25)
        self.years_antiquity = years_antiquity
        self.days_rest = days_rest

    def _get_integral_salary(self):
        '''
        Esten metodo busca el salario integral fijo para agregarlo al formulario del empleado
        '''
        contracts = self
        for contract in contracts:
            current_date  =  fields.Date.context_today(self)+timedelta(days=1)
            start_date_contract = contract.previous_contract_date or contract.date_start
            years_antiquity = contract.years_antiquity
            antiguedad = self.env['tablas.antiguedades.line'].search([('antiguedad','=',years_antiquity),('form_id','=',contract.employee_id.group_id.antique_table.id)])
            daily_salary = contract.wage / contract.employee_id.group_id.days if contract.employee_id.group_id.days else contract.wage / 30
            integral_salary =  daily_salary + (daily_salary*(antiguedad.factor/100))
            contract.integral_salary = integral_salary

    # def _get_variable_salary(self):
    #     '''
    #     Este metodo buscara los salarios variables de las nominas y calculara el valor para agregarlo al empleado
    #     '''
    #     current_date = fields.Date.context_today(self)
    #     current_month = current_date.month
    #     date_start = date(current_date.year, current_month-2, 1)
    #     date_end = current_date
    #     payslips = self.env['hr.payslip'].search([('date_from','>=',date_start),('date_to','<=',date_end)])
    #     self.salary_var = sum(payslips.mapped('integral_variable_salary'))/len(payslips)


    #Columns
    code = fields.Char('Code',required=True, default= lambda self: self.env['ir.sequence'].next_by_code('Contract'))
    type_id = fields.Many2one(string="Type Contract")
    type_contract = fields.Selection(string="Type", related="type_id.type", invisible=True)
    company_id = fields.Many2one('res.company', default = ['employee_id','=', False])
    previous_contract_date = fields.Date('Previous Contract Date', help="Start date of the previous contract for antiquity.")
    power_attorney_id = fields.Many2one('company.power.attorney',string="Power Attorney")
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free'),
        ], string='Contracting Regime', required=True, default="2")
    years_antiquity = fields.Integer(string='Antiquity', compute='_get_years_antiquity')
    days_rest = fields.Integer(string='Días de antiguedad ultimo año', compute='_get_years_antiquity')
    integral_salary= fields.Float(string="SDI", compute='_get_integral_salary', copy=False, store=True)
    group_id = fields.Many2one('hr.group', "Grupo", store=True, related='employee_id.group_id')
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", store=True, related='employee_id.work_center_id')
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", store=True, related='employee_id.employer_register_id')
    # ~ salary_var= fields.Float("Salary Variable", compute='_get_variable_salary', copy=False) 
    
    fixed_concepts_ids = fields.One2many('hr.fixed.concepts','contract_id', "Fixed concepts")

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
        
    def holiday_bonus(self):
        years_antiquity = self.years_antiquity
        if years_antiquity == 0:
            years_antiquity = 1
        antiquity = self.env['tablas.antiguedades.line'].search([('form_id','=',self.employee_id.group_id.antique_table.id),('antiguedad','=',years_antiquity)],limit=1)
        return antiquity.prima_vac
        

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
