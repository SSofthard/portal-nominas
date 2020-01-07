# -*- coding: utf-8 -*-

from datetime import datetime
import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

from .tool_convert_numbers_letters import numero_to_letras
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta


class Holidays(models.Model):
    _inherit = 'hr.leave'


    @api.depends('employee_id', 'holiday_status_id', 'number_of_days_display')
    def _compute_remaining_days(self):
        '''En este metodo se busca los dias que quedan assignados por disfrute'''
        for record in self.holiday_status_id :
            name = record.name
            if record.allocation_type != 'no':
                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('%g días restantes de %g') % (
                        float_round(record.with_context(default_employee_id=self.employee_id.id).virtual_remaining_leaves, precision_digits=2) or 0.0,
                        float_round(record.with_context(default_employee_id=self.employee_id.id).max_leaves, precision_digits=2) or 0.0,
                    )
                }
        self.remaining_days = name


    @api.multi
    def action_validate(self):
        '''
        Este metodo ejecutará el metodo de validacón del super y agregará la prima vacacional a las entradas de nomina.
        :return:
        '''
        if self.holiday_status_id.is_holidays and self.contract_id.employee_id.payment_holidays_bonus:
            inputs_obj = self.env['hr.inputs']
            self.send_bonus_holidays(self.contract_id)
        return super(Holidays, self).action_validate()

    @api.multi
    def send_bonus_holidays(self, contract):
        '''
        Este metodo calcula la prima vacacional extrayendo las antiguedades para cada uno de los contratos.
        llena el O2m prorate_lines y el total de la prima.
        :return:
        '''
        inputs_obj = self.env['hr.inputs']
        cfdi_record = self.env['tablas.antiguedades.line'].search(
            [('antiguedad', '=', contract.years_antiquity),
             ('form_id', '=', self.employee_id.group_id.antique_table.id)])
        amount_bonus = ((contract.wage / 30) * self.number_of_days_display) * cfdi_record.prima_vac / 100
        vals = {
            'employee_id': self.employee_id.id,
            'input_id': self.holiday_status_id.input_type.id,
            'amount': amount_bonus,
            'type': 'perception',
        }
        inputs_obj.create(vals)

    @api.depends('employee_id','holiday_status_id','number_of_days_display')
    def _compute_bonus(self):
        '''
        Este metodo calcula la prima vacacional extrayendo las antiguedadespara el calculo total de la prima.
        :return:
        '''
        amount_total = 0.0
        cfdi_record = self.env['tablas.antiguedades.line'].search(
            [('antiguedad', '=', self.contract_id.years_antiquity),('form_id','=',self.employee_id.group_id.antique_table.id)])
        amount_bonus = ((self.contract_id.wage/30)*self.number_of_days_display) * cfdi_record.prima_vac / 100
        self.holidays_bonus =  amount_bonus

    #Columns
    holidays_bonus = fields.Float(compute='_compute_bonus', string='Holidays total bonus')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    remaining_days = fields.Char(compute='_compute_remaining_days', string='Remaining')
    date_payroll_asign = fields.Date(string='Indique la fecha de pago por nómina')


class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    @api.multi
    def name_get(self):
        if self._context.get('no_show_remaining'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(LeaveType, self).name_get()
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res

    time_type = fields.Selection(selection_add=[('holidays','Holidays')])
    is_holidays = fields.Boolean(string='Is holidays?')
    input_type = fields.Many2one(comodel_name='hr.rule.input', string='Tipo de entrada')


class HrLeaveAllocation(models.Model):
    _inherit='hr.leave.allocation'

    @api.multi
    def assign_allocations_for_employee(self):
        today = fields.Date.context_today(self)
        range_date = calendar.monthrange(today.year,today.month)
        date_init = date(today.year, today.month, 1)
        date_end = date(today.year, today.month, range_date[1])
        contracts = self.env['hr.contract'].search([('employee_id','!=', False), ('contracting_regime','=',2)])
        holidays_type = self.env['hr.leave.type'].search([('validity_start','<=',today),
                                                          ('validity_stop','>=',today),
                                                          ('is_holidays','=',True)])
        employees = []
        for contract in contracts:
            date_init = date(contract.date_start.year, today.month, 1)
            date_end = date(contract.date_start.year, today.month, range_date[1])
            allocations_assignated = sum(self.search([('employee_id','=',contract.employee_id.id)]).mapped('number_of_days_display'))
            if contract.date_start >= date_init and contract.date_start <= date_end:
                employees.append(contract.employee_id.id)
                days_holidays=self.env['tablas.antiguedades.line'].search([('antiguedad','=', contract.years_antiquity)]).vacaciones
                if days_holidays >  allocations_assignated:
                    vals = {
                        'mode':'employee',
                        'number_of_days':float(days_holidays),
                        'employee_id':contract.employee_id.id,
                        'contract_id':contract.id,
                        'holiday_status_id':holidays_type.id,
                    }
                    res_id = self.create(vals)
                    res_id.action_approve()
                    if not contract.employee_id.payment_holidays_bonus:
                        res_id.send_bonus_holidays(contract)

    @api.multi
    def send_bonus_holidays(self, contract):
        '''
        Este metodo calcula la prima vacacional extrayendo las antiguedades para cada uno de los contratos.
        llena el O2m prorate_lines y el total de la prima.
        :return:
        '''
        inputs_obj = self.env['hr.inputs']
        cfdi_record = self.env['tablas.antiguedades.line'].search(
            [('antiguedad', '=', contract.years_antiquity),('form_id','=',self.employee_id.group_id.antique_table.id)])
        amount_bonus = ((contract.wage/30)*self.number_of_days_display) * cfdi_record.prima_vac / 100
        vals = {
            'employee_id': self.employee_id.id,
            'input_id': self.holiday_status_id.input_type.id,
            'amount': amount_bonus,
            'type': 'perception',
        }
        inputs_obj.create(vals)

    @api.onchange('contract_id','holiday_status_id')
    def onchange_contract_id(self):
        cfdi_record = self.env['tablas.antiguedades.line'].search([('form_id', '=',self.employee_id.group_id.antique_table.id),('antiguedad','=',self.contract_id.years_antiquity)])
        self.number_of_days_display = cfdi_record.vacaciones


    #Columns
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    # cfdi_rule_id = fields.Many2one(related='holiday_status_id.cfdi_rule_id', string='Contrato')
