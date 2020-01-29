# -*- coding: utf-8 -*-
from datetime import datetime
import calendar

from datetime import date, datetime, time, timedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardComputeSDIVar(models.TransientModel):
    _name = "wizard.compute.sdi.vars"

    def _get_selection_year(self):
        current_year = fields.Date.context_today(self).year
        list_selection=[]
        for item in range(current_year-5,current_year+1):
            list_selection.append((str(item),str(item)))
        return list_selection

    bimestre = fields.Selection([
        (1, 'Enero - Febrero'),
        (2, 'Marzo - Abril'),
        (3, 'Mayo - Junio'),
        (4, 'Julio - Agosto'),
        (5, 'Septiembre - Octubre'),
        (6, 'Noviembre - Diciembre'),
                                 ],string = 'Bimestre', required=True)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    contracting_regime = fields.Selection([
        ('02', 'Wages and salaries'),
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
    ], string='Contracting Regime', required=True, default="02")
    compute_lines = fields.One2many(comodel_name='wizard.compute.sdi.vars.lines', inverse_name='compute_form_id', string='Calculos')
    # employee_ids = fields.Many2many(comodel_name='hr.employee', string='Empleados')
    computed = fields.Boolean(string="Calculado")
    year = fields.Selection(_get_selection_year, string='Año', required=True)

    
    @api.multi
    def get_compute_lines(self):
        '''
        Este metodo obtiene las lineas de calculos de variables para el cambio de SDI
        '''


        self.compute_lines.unlink()
        compute_lines = []
        domain_work_center = []
        domain_register = []
        domain_contract_processed = []
        contract_processed = self.env['compute.sdi.vars.lines'].search(
            [('year', '=', self.year), ('bimestre', '=', self.bimestre)]).mapped('contract_id')._ids
        if len(contract_processed):
            domain_contract_processed = [('id', 'not in', contract_processed)]
        year = int(self.year)
        months = [(self.bimestre*2),((self.bimestre*2)-1)]
        date_start = date(year, months[1], 1)
        last_day = calendar.monthrange(year, months[0])[1]
        date_end = date(year, months[0], last_day) + timedelta(days=1)
        days_bimestre = (date_end - date_start).days
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        if self.contracting_regime:
            domain_work_center = [('contracting_regime', '=', self.contracting_regime)]
        contract_ids = self.env['hr.contract'].search(
            [('state','=','open'),('employee_id.group_id', '=', self.group_id.id),] + domain_register + domain_work_center + domain_contract_processed)
        for contract in contract_ids:
            salary_var = 0.0
            print (contract)
            print (contract)
            print (contract)
            print (months)
            print (months)
            print (months)
            payslips = self.env['hr.payslip'].search([('state','=','done'),
                                                      ('payroll_month','in',months),
                                                      ('contract_id', '=', contract.id),
                                                      ('year','=',year),
                                                      # ('payroll_type','=','O'),
                                                      ])
            print (payslips)
            print (payslips)
            print (payslips)
            if payslips:
                if contract.employee_id.salary_type == '1':
                    salary_var = self._compute_integral_variable_salary(payslips,days_bimestre,contract)
                if contract.employee_id.salary_type == '2':
                    salary_var = self._compute_integral_variable_salary(payslips,days_bimestre,contract) + contract._calculate_integral_salary()
            vals = {
                'contract_id':contract.id,
                'employee_id':contract.employee_id.id,
                'current_sdi':contract.integral_salary,
                'new_sdi':salary_var,
                'days_worked':days_bimestre,
                'perceptions_bimonthly':salary_var,
            }
            compute_lines.append(vals)
        self.compute_lines = compute_lines
        self.computed = True
        return {'type': 'ir.actions.act_window',
                'res_model': 'wizard.compute.sdi.vars',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new'}

    @api.multi
    def proccess_data(self, data):
        '''
        Este metodo setea los  nuevos valores de SDI a los contratos
        '''
        for line in self.compute_lines:
            line.contract_id.integral_salary = line.new_sdi
            res_id = self.env['hr.employee.affiliate.movements'].create({
                'contract_id': line.contract_id.id,
                'employee_id': line.employee_id.id,
                'group_id': line.employee_id.group_id.id,
                'type': '07',
                'date': fields.Date.context_today(self),
                'salary': line.new_sdi,
                'state': 'draft',
                'contracting_regime': '02',
            })
            if res_id:
                vals = {
                    'contract_id': line.contract_id.id,
                    'employee_id': line.employee_id.id,
                    'current_sdi': line.current_sdi,
                    'new_sdi': line.new_sdi,
                    'days_worked': line.days_worked,
                    'perceptions_bimonthly': line.perceptions_bimonthly,
                    'bimestre': self.bimestre,
                    'year': self.year,
                }
                res_calulate_vars_line = self.env['compute.sdi.vars.lines'].create(vals)


        
        
    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))

    @api.multi
    def _compute_integral_variable_salary(self, payslips,days_bimestre, contract):
        '''Este metodo se utiliza para el cálculo de salario diario variable'''

        days_factor = {
            'daily': 1,
            'weekly': 7,
            'decennial': 10,
            'biweekly': 15,
            'monthly': 30,
        }
        list_percepcions = payslips.mapped('line_ids').filtered(lambda o: o.salary_rule_id.apply_variable_compute
                                                            and o.salary_rule_id.type == 'perception')
        percepcions_bimonthly = self.group_bimonthly_perceptions(list_percepcions)
        total_perception = self.get_total_perceptions_to_sv(percepcions_bimonthly,payslips,days_bimestre, contract)
        return total_perception

    def group_bimonthly_perceptions(self,list_percepcions):
        '''
        Este metodo agrupa los montos por conceptos para hacer los calculos variables
        :return:
        '''
        code_perceptions = list_percepcions.mapped('salary_rule_id.type_perception')
        perception_bimonthly = {code_perceptions[i]:0 for i in range(len(code_perceptions))}
        print (perception_bimonthly)
        print (perception_bimonthly)
        print (perception_bimonthly)
        for key in perception_bimonthly.keys():
            perception_bimonthly[key] = sum(list_percepcions.filtered(lambda line: line.salary_rule_id.type_perception == key).mapped('total'))
        print (perception_bimonthly)
        return perception_bimonthly

    def get_total_perceptions_to_sv(self, perceptions, payslips,days_bimestre, contract):
        '''
        Este metodo permite consultar si la regla aplica según los criterios de evaluación por ley
        '''
        vals = {}
        leave_codes = self.env['hr.leave.type'].search([('time_type', '=', 'leave'),('code','!=',False)]).mapped('code')
        print ('leave_codes')
        print (leave_codes)
        leave_days = sum(payslips.mapped('worked_days_line_ids').filtered(lambda line: line.code in leave_codes).mapped(
            'number_of_days'))
        bimonthly_days = days_bimestre-leave_days
        for key in perceptions.keys():
            if key in ['010', '049']:
                print('''Asistencia y puntualidad: Cuando el importe de cada uno no exceda del 10% del último SBC comunicado al
                            ~ Seguro Social, de ser así la cantidad que rebase integrará''')
                print (contract.integral_salary)
                exent_amount = (contract.integral_salary*0.1)*bimonthly_days
                exent_amount
                restante = (perceptions[key] - exent_amount)/bimonthly_days
                if restante > 0:
                    print (restante)
                    vals[key] = restante
            if key in ['030', '048']:
                print('''Alimentacion y Habitación: cuando el importe de cada uno no exceda del 20% del SMGVDF, de ser así la cantidad que rebase integrará''')
                deductions = payslips.mapped('line_ids').filtered(lambda o: o.salary_rule_id.type_deduction in ['055','061']
                                                       and o.salary_rule_id.type == 'deductions')
                SMGVDF = []
                municipalities = self.env['res.country.state.municipality'].search([('state_id.code', '=', 'DIF')])
                for municipality in municipalities:
                    municipality.name
                    SMGVDF.append(municipality.get_salary_min(fields.Date.context_today(self)))
                SMGVDF = list(set(SMGVDF))[0]
                exent_amount = (SMGVDF*bimonthly_days)*0.20
                restante = (perceptions[key] - exent_amount)/bimonthly_days
                if restante > 0:
                    print(restante)
                    vals[key] = restante
            if key == '019':
                print('''el generado dentro de los límites señalados en la Ley Federal del Trabajo (LFT), esto es que no
                             exceda de tres horas diarias ni de tres veces en una semana''')
                print (perceptions[key])
                print (perceptions[key])
                print (bimonthly_days)
                vals[key] = restante/bimonthly_days
            if key in ['029']:
                print('''si su importe no rebasa el 40% del SMGVDF, de lo contrario el excedente se integrará''')
                SMGVDF = []
                municipalities = self.env['res.country.state.municipality'].search([('state_id.code', '=', 'DIF')])
                for municipality in municipalities:
                    municipality.name
                    SMGVDF.append(municipality.get_salary_min(fields.Date.context_today(self)))
                SMGVDF = list(set(SMGVDF))[0]
                exent_amount = (SMGVDF * bimonthly_days) * 0.40
                restante = (perceptions[key] - exent_amount) / bimonthly_days
                if restante > 0:
                    print(restante)
                    vals[key] = restante
            else:
                print (key)
                print(perceptions[key]/bimonthly_days)
                vals[key] = perceptions[key]/bimonthly_days
        print (vals)
        print (vals)
        print (sum(vals.values()))
        return sum(vals.values())


class WizardComputeSDIVarLines(models.TransientModel):
    _name = "wizard.compute.sdi.vars.lines"

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    current_sdi = fields.Float(string='SDI Actual')
    new_sdi = fields.Float(string='SDI Nuevo')
    perceptions_bimonthly = fields.Float(string='Percepciones variables durante el bimestre')
    days_worked = fields.Integer(string='Días laborados durante el bimestre')
    compute_form_id = fields.Many2one(comodel_name='wizard.compute.sdi.vars', string='Calculo de variables')

class ComputeSDIVarLines(models.Model):
    _name = "compute.sdi.vars.lines"

    def _get_selection_year(self):
        current_year = fields.Date.context_today(self).year
        list_selection=[]
        for item in range(current_year-5,current_year+1):
            list_selection.append((str(item),str(item)))
        return list_selection

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    current_sdi = fields.Float(string='SDI Actual')
    new_sdi = fields.Float(string='SDI Nuevo')
    perceptions_bimonthly = fields.Float(string='Percepciones variables durante el bimestre')
    days_worked = fields.Integer(string='Días laborados durante el bimestre')
    history_id = fields.Many2one(comodel_name='hr.employee.affiliate.movements', string='Affiliates move')
    bimestre = fields.Selection([
        (1, 'Enero - Febrero'),
        (2, 'Marzo - Abril'),
        (3, 'Mayo - Junio'),
        (4, 'Julio - Agosto'),
        (5, 'Septiembre - Octubre'),
        (6, 'Noviembre - Diciembre'),],string = 'Bimestre', required=True)
    year = fields.Selection(_get_selection_year, string='Año', required=True)