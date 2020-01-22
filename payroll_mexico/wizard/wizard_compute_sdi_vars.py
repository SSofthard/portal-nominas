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
        # ('01', 'Assimilated to wages'),
        ('02', 'Wages and salaries'),
        ('03', 'Senior citizens'),
        ('04', 'Pensioners'),
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
            payslips = self.env['hr.payslip'].search([('state','=','close'),('payroll_month','in',months), ('contract_id', '=', contract.id)])
            if payslips:
                salary_var = sum(payslips.mapped('integral_variable_salary')) / len(payslips)
            vals = {
                'contract_id':contract.id,
                'employee_id':contract.employee_id.id,
                'current_sdi':contract.integral_salary,
                'new_sdi':contract.integral_salary+salary_var,
                'days_worked':60,
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

        
        
    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))


class WizardComputeSDIVarLines(models.TransientModel):
    _name = "wizard.compute.sdi.vars.lines"

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    current_sdi = fields.Float(string='SDI Actual')
    new_sdi = fields.Float(string='SDI Nuevo')
    perceptions_bimonthly = fields.Float(string='Percepciones variables durante el bimestre')
    days_worked = fields.Integer(string='Días laborados durante el bimestre')
    compute_form_id = fields.Many2one(comodel_name='wizard.compute.sdi.vars', string='Calculo de variables')
