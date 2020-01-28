# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardComputeSDIVar(models.TransientModel):
    _name = "wizard.compute.sdi.vars"

    def _get_selection_year(self):
        current_year = fields.Date.context_today(self).year
        list_selection=[]
        for item in range(current_year-5,current_year+1):
            list_selection.append((item,str(item)))
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
    year = fields.Selection(_get_selection_year, string='Año')

    
    @api.multi
    def get_compute_lines(self):
        '''
        Este metodo obtiene las lineas de calculos de variables para el cambio de SDI
        '''
        self.compute_lines.unlink()
        compute_lines = []
        domain_work_center = []
        domain_register = []
        months = [(self.bimestre*2),((self.bimestre*2)-1)]
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        if self.contracting_regime:
            domain_work_center = [('contracting_regime', '=', self.contracting_regime)]
        contract_ids = self.env['hr.contract'].search(
            [('state','=','open'),('employee_id.group_id', '=', self.group_id.id)] + domain_register + domain_work_center)
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
                                                      # ('year','=',self.year),
                                                      # ('payroll_type','=','O'),
                                                      ])
            print (payslips)
            print (payslips)
            print (payslips)
            if payslips:
                salary_var = self._compute_integral_variable_salary(payslips)
            vals = {
                'contract_id':contract.id,
                'employee_id':contract.employee_id.id,
                'current_sdi':contract.integral_salary,
                'new_sdi':contract.integral_salary+(salary_var/61) if  salary_var > 0 else contract._get_integral_salary(),
                'days_worked':61,
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
    def _compute_integral_variable_salary(self, payslips):
        '''Este metodo se utiliza para el cálculo de salario diario integral variable'''
        days_factor = {
            'daily': 1,
            'weekly': 7,
            'decennial': 10,
            'biweekly': 15,
            'monthly': 30,
        }
        print (payslips)
        print (payslips)
        print (payslips)
        # print (x)
        list_percepcions = payslips.mapped('line_ids').filtered(lambda o: o.salary_rule_id.apply_variable_compute
                                                            and o.salary_rule_id.type == 'perception')
        print (list_percepcions)
        print (list_percepcions)
        total_perception = self.get_total_perceptions_to_sv(list_percepcions)
        return total_perception

    def get_total_perceptions_to_sv(self, lines):
        '''
        Este metodo permite consultar si la regla aplica según los criterios de evaluación por ley
        '''
        vals = []
        for line in lines:
            if line.salary_rule_id.type_perception in ['010', '049']:
                print('''cuando el importe de cada uno no exceda del 10% del último SBC comunicado al
                            ~ Seguro Social, de ser así la cantidad que rebase integrará''')
                proporcion_percepcion = line.amount / self.contract.salary_var
                if proporcion_percepcion > 0.1:
                    restante = (line.amount - (self.contract.salary_var * 0.1)) * line.quantity
                    vals.append(restante)
            if line.salary_rule_id.type_perception == '019' and line.salary_rule_id.type_overtime == '02':
                print('''el generado dentro de los límites señalados en la Ley Federal del Trabajo (LFT), esto es que no
                             exceda de tres horas diarias ni de tres veces en una semana''')
                vals.append(line.total)
            if line.salary_rule_id.type_perception in ['029']:
                print('''si su importe no rebasa el 40% del SMGVDF, de lo contrario el excedente se integrará''')
                minimum_salary = self.company_id.municipality_id.get_salary_min(self.date_from)
                if line.amount > (minimum_salary * 0.40):
                    restante = (line.amount - (minimum_salary * 0.40)) * line.quantity
                    vals.append(restante)
            else:
                vals.append(line.total)
        return sum(vals)


class WizardComputeSDIVarLines(models.TransientModel):
    _name = "wizard.compute.sdi.vars.lines"

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    current_sdi = fields.Float(string='SDI Actual')
    new_sdi = fields.Float(string='SDI Nuevo')
    perceptions_bimonthly = fields.Float(string='Percepciones variables durante el bimestre')
    days_worked = fields.Integer(string='Días laborados durante el bimestre')
    compute_form_id = fields.Many2one(comodel_name='wizard.compute.sdi.vars', string='Calculo de variables')
