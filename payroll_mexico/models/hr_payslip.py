# -*- coding: utf-8 -*-

from datetime import date,datetime,time
from pytz import timezone

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

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
                                                                calendar=contract.resource_calendar_id)

            dias_feriados = {
                'name': _("Días feriados"),
                'sequence': 1,
                'code': 'DFER',
                'number_of_days': work_data['public_days'],
                'number_of_hours': work_data['public_days_hours'],
                'contract_id': contract.id,
            }
            prima_dominical = {
                'name': _("Prima Dominical"),
                'sequence': 1,
                'code': 'PDOM',
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

            res.append(attendances)
            res.append(prima_dominical)
            res.append(dias_feriados)
            res.extend(leaves.values())
        return res



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

