# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from .tool_convert_numbers_letters import numero_to_letras
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta


class Holidays(models.Model):
    _inherit = 'hr.leave'

    @api.depends('employee_id','holiday_status_id','number_of_days_display')
    def _compute_bonus(self):
        '''
        Este metodo calcula la prima vacacional extrayendo las antiguedades para cada uno de los contratos.
        llena el O2m prorate_lines y el total de la prima.
        :return:
        '''
        contracts = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id)])
        prorate_lines=[]
        amount_total = 0.0
        for contract in contracts:
            cfdi_record = self.env['tablas.antiguedades.line'].search(
                [('form_id', '=', self.holiday_status_id.cfdi_rule_id.id),
                 ('antiguedad', '=', contract.years_antiquity)])
            amount_bonus = ((contract.wage/30)*self.number_of_days_display) * cfdi_record.prima_vac / 100
            prorate_lines.append({'contract_id': contract.id,
                                  'holidays_bonus': amount_bonus,
                                  'leave_id': self.id
                                  })
            amount_total +=amount_bonus
        print (prorate_lines)
        print (prorate_lines)
        print (prorate_lines)
        self.prorate_lines = prorate_lines
        self.holidays_bonus = amount_total

    #Columns
    holidays_bonus = fields.Float(compute='_compute_bonus', string='Holidays total bonus')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    prorate_lines = fields.One2many(comodel_name='hr.holidays.prorate', inverse_name='leave_id', compute='_compute_bonus', store='True',string='Holidays Bonus')
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('confirmed', 'Confirmed'),
    # ], string='State', default='draft')



class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    time_type = fields.Selection(selection_add=[('holidays','Holidays')])
    cfdi_rule_id = fields.Many2one(comodel_name='tablas.cfdi', string='Holidays')


class HrLeaveAllocation(models.Model):
    _inherit='hr.leave.allocation'

    def _get_rules_cfdi(self):
        print (self)
        print (self)
        print (self)
        print (self)
        print (self)

    @api.onchange('contract_id','holiday_status_id')
    def onchange_contract_id(self):
        cfdi_record = self.env['tablas.antiguedades.line'].search([('form_id', '=',self.cfdi_rule_id.id),('antiguedad','=',self.contract_id.years_antiquity)])
        print (cfdi_record)
        print (cfdi_record)
        print (cfdi_record)
        print (cfdi_record)
        self.number_of_days_display = cfdi_record.vacaciones


    #Columns
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    cfdi_rule_id = fields.Many2one(related='holiday_status_id.cfdi_rule_id', string='Contrato')

class HrHolidaysProrate(models.Model):
    _name = 'hr.holidays.prorate'

    #Columns
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    holidays_bonus = fields.Float(string='Amount')
    leave_id = fields.Many2one(comodel_name='hr.leave', string='Holidays Form')