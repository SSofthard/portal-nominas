# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone

import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.osv import expression


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    payroll_type = fields.Selection([
            ('ordinary_payroll', 'Ordinary Payroll'),
            ('extraordinary_payroll', 'Extraordinary Payroll')], string='Payroll Type', default="ordinary_payroll", required=True)
    payroll_month = fields.Selection([
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December')], string='Payroll month', required=True)
    payroll_of_month = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6')], string='Payroll of the month', required=True)
    payroll_period = fields.Selection([
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('decennial', 'Decennial'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly')], string='Payroll period', default="biweekly",required=True)
    input_ids = fields.Many2many('hr.inputs', string="Inpust reported on payroll")
    table_id = fields.Many2one('table.settings', string="Table Settings")


    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []
        structure_ids = contracts.get_all_structures(self.struct_id)
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')
        hr_inputs = self.env['hr.inputs'].browse([])
        self.input_ids.write({'payslip':False})
        self.input_ids = False
        for contract in contracts:
            employee_id = (self.employee_id and self.employee_id.id) or (contract.employee_id and contract.employee_id.id)
            for input in inputs:
                amount = 0.0
                other_input_line = self.env['hr.inputs'].search([('employee_id', '=', employee_id),('input_id', '=', input.id),('state','in',['approve']),('payslip','=',False)])
                hr_inputs += other_input_line
                for line in other_input_line:
                    amount += line.amount
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'amount': amount,
                    'contract_id': contract.id,
                }
                res += [input_data]
            self.input_ids = hr_inputs
            hr_inputs.write({'payslip':True})
        return res

    
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
        if not self.contract_id:
            contract = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','in',['open'])])
            if not contract:
                return
            self.contract_id = contract[0].id
            contract_ids = [contract[0].id]
        else:
            contract_ids = [self.contract_id.id]
        self.company_id = self.contract_id.company_id
        self.struct_id=False
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        self.worked_days_line_ids = []
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        self.payroll_month = str(date_from.month)
        self.table_id = self.env['table.settings'].search([('year','=',int(date_from.year))],limit=1).id
        return
        
    def search_inputs(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to) or (not self.contract_id):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contracts = self.contract_id
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        '''Este metodo hereda el comportamiento nativo para agregar los dias feriados, prima dominical al O2m de dias trabajados'''
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.name or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to,
                                                                calendar=contract.resource_calendar_id, contract=contract)
            attendances_hours =  sum(attendace.hour_to - attendace.hour_from
                                    for attendace in calendar.attendance_ids
                                    )
            attendances_list = calendar.attendance_ids.mapped('dayofweek')
            count_days_week = list(set(attendances_list))
            count_days_weeks = {
                'name': _("Dias semana"),
                'sequence': 1,
                'code': 'DIASEMANA',
                'number_of_days': len(count_days_week),
                'number_of_hours': attendances_hours,
                'contract_id': contract.id,
            }
            days_factor = contract.employee_id.group_id.days
            elemento_calculo = {
                'name': _("Periodo mensual IMSS"),
                'sequence': 1,
                'code': 'PERIODOIMSS100',
                'number_of_days': days_factor,
                'number_of_hours': 0,
                'contract_id': contract.id,
            }
            date_start = date_from if contract.date_start < date_from else contract.date_start
            date_end =  contract.date_end if contract.date_end and contract.date_end < date_to else date_to
            from_full = date_start
            to_full = date_end + timedelta(days=1)
            payroll_periods_days = {
                'monthly': 30,
                'biweekly': 15,
                'weekly': 7,
                'decennial': 10,
                'daily': 1,
                                }
            if (to_full - from_full).days >= payroll_periods_days[self.payroll_period]:
                cant_days = payroll_periods_days[self.payroll_period]*(days_factor/30)
            else:
                cant_days = (to_full - from_full).days*(days_factor/30)

            cant_days_IMSS = {
                'name': _("Días a cotizar en la nómina"),
                'sequence': 1,
                'code': 'DIASIMSS',
                'number_of_days': cant_days,
                'number_of_hours': 0,
                'contract_id': contract.id,
            }
            if contract.employee_id.pay_holiday:
                dias_feriados = {
                    'name': _("Días feriados"),
                    'sequence': 1,
                    'code': 'FERIADO',
                    'number_of_days': work_data['public_days'],
                    'number_of_hours': work_data['public_days_hours'],
                    'contract_id': contract.id,
                }
                res.append(dias_feriados)
            prima_dominical = {
                'name': _("DOMINGO"),
                'sequence': 1,
                'code': 'DOMINGO',
                'number_of_days': work_data['sundays'],
                'number_of_hours': work_data['sundays_hours'],
                'contract_id': contract.id,
            }
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }
            res.append(count_days_weeks)
            res.append(cant_days_IMSS)
            res.append(elemento_calculo)
            res.append(attendances)
            res.append(prima_dominical)
            res.extend(leaves.values())
        return res
        
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
    payslip = fields.Boolean('Payroll?')
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
