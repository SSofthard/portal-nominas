# -*- coding: utf-8 -*-

from datetime import datetime

import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time
from odoo.exceptions import UserError
from odoo.osv import expression

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'date_from', 'date_to','contract_id')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id
        if not self.contract_id:
            contract = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','in',['open'])])
            if not contract:
                return
            self.contract_id = contract[0].id
            contract_ids = [contract[0].id]
        else:
            contract_ids = [self.contract_id.id]
        self.struct_id=False
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        self.worked_days_line_ids = []
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        self.input_line_ids = input_lines
        return
        
    @api.onchange('contract_id')
    def onchange_contract(self):
        return

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    
    type_perception = fields.Selection(
        selection=[('001', 'Sueldos, Salarios  Rayas y Jornales'), 
                   ('002', 'Gratificación Anual (Aguinaldo)'), 
                   ('003', 'Participación de los Trabajadores en las Utilidades PTU'),
                   ('004', 'Reembolso de Gastos Médicos Dentales y Hospitalarios'), 
                   ('005', 'Fondo de ahorro'),
                   ('006', 'Caja de ahorro'),
                   ('007', 'Vales'),
                   ('008', 'Ayudas'),
                   ('009', 'Contribuciones a Cargo del Trabajador Pagadas por el Patrón'), 
                   ('010', 'Premios por puntualidad'),
                   ('011', 'Prima de Seguro de vida'), 
                   ('012', 'Seguro de Gastos Médicos Mayores'), 
                   ('013', 'Cuotas Sindicales Pagadas por el Patrón'), 
                   ('014', 'Subsidios por incapacidad'),
                   ('015', 'Becas para trabajadores y/o hijos'), 
                   ('016', 'Otros'), 
                   ('017', 'Subsidio para el empleo'), 
                   ('018', 'Fomento al primer empleo'), 
                   ('019', 'Horas extra'),
                   ('020', 'Prima dominical'), 
                   ('021', 'Prima vacacional'),
                   ('022', 'Prima por antigüedad'),
                   ('023', 'Pagos por separación'),
                   ('024', 'Seguro de retiro'),
                   ('025', 'Indemnizaciones'), 
                   ('026', 'Reembolso por funeral'), 
                   ('027', 'Cuotas de seguridad social pagadas por el patrón'), 
                   ('028', 'Comisiones')],
        string=_('Type of perception'),
    )
    type_deduction = fields.Selection(
        selection=[('001', 'Seguridad social'), 
                   ('002', 'ISR'), 
                   ('003', 'Aportaciones a retiro, cesantía en edad avanzada y vejez.'),
                   ('004', 'Otros'), 
                   ('005', 'Aportaciones a Fondo de vivienda'),
                   ('006', 'Descuento por incapacidad'),
                   ('007', 'Pensión alimenticia'),
                   ('008', 'Renta'),				   
                   ('009', 'Préstamos provenientes del Fondo Nacional de la Vivienda para los Trabajadores'), 
                   ('010', 'Pago por crédito de vivienda'),
                   ('011', 'Pago de abonos INFONACOT'), 
                   ('012', 'Anticipo de salarios'), 
                   ('013', 'Pagos hechos con exceso al trabajador'), 
                   ('014', 'Errores'),
                   ('015', 'Pérdidas'), 
                   ('016', 'Averías'), 
                   ('017', 'Adquisición de artículos producidos por la empresa o establecimiento'),
                   ('018', 'Cuotas para la constitución y fomento de sociedades cooperativas y de cajas de ahorro'), 				   
                   ('019', 'Cuotas sindicales'),
                   ('020', 'Ausencia (Ausentismo)'), 
                   ('021', 'Cuotas obrero patronales')],
        string=_('Type of deduction'),
    )
    
    type = fields.Selection([
        ('not_apply', 'Does not apply'),
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', default="not_apply")

class HrInputs(models.Model):
    _name = 'hr.inputs'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, states={'paid': [('readonly', True)]})
    amount = fields.Float('Amount', states={'paid': [('readonly', True)]}, digits=(16, 2))
    
    
    input_id = fields.Many2one('hr.rule.input', string='Input', required=True, states={'paid': [('readonly', True)]})
    
    
    state = fields.Selection([
        ('approve', 'Approved'),
        ('paid', 'Reported on payroll')], string='Status', readonly=True, default='approve')
        
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', related= 'input_id.type', readonly=True, states={'paid': [('readonly', True)]}, store=True)
    group_id = fields.Many2one('hr.group', "Group", related= 'employee_id.group_id', readonly=True, states={'paid': [('readonly', True)]}, store=True)



class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input'
    
    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|',('code', operator, name),('name', operator, name)]
        rule_input = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(rule_input).name_get()
    
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', required=True)

