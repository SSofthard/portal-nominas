# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

from .tool_convert_numbers_letters import numero_to_letras
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta



class Holidays(models.Model):
    _inherit = 'hr.leave'

    # @api.depends('employee_id', 'holiday_status_id', 'number_of_days_display')
    # def _compute_remaining_days(self):
    #     '''En este metodo se busca los dias que quedan assignados por disfrute'''
    #     print (self.holiday_status_id)
    #     print (self.holiday_status_id)
    #     print (self.holiday_status_id)
    #     print (self.holiday_status_id)
    #     for record in self.holiday_status_id:
    #         name = record.name
    #         if record.allocation_type != 'no':
    #             name = "%(name)s (%(count)s)" % {
    #                 'name': name,
    #                 'count': _('%g remaining out of %g') % (
    #                     float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
    #                     float_round(record.max_leaves, precision_digits=2) or 0.0,
    #                 )
    #             }
    #             print ('name')
    #             print (name)
    #             print (name)
    #             print (name)
    #     self.remaining = name


    @api.multi
    def action_validate(self):
        '''
        Este metodo ejecutará el metodo de validacón del super y agregará la prima vacacional a las entradas de nomina.
        :return:
        '''
        inputs_obj = self.env['hr.inputs']
        for line in self.prorate_lines:
            vals = {
                'employee_id' : self.employee_id.id,
                'input_id' : line.input_id.id,
                'amount' : line.holidays_bonus,
                'type' : 'perception',
            }
            inputs_obj.create(vals)
        return super(Holidays, self).action_validate()

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
            print (cfdi_record)
            amount_bonus = ((contract.wage/30)*self.number_of_days_display) * cfdi_record.prima_vac / 100
            prorate_lines.append({'contract_id': contract.id,
                                  'holidays_bonus': amount_bonus,
                                  'leave_id': self.id
                                  })
            amount_total +=amount_bonus
        print ([(0,0,line) for line in prorate_lines])
        self.prorate_lines = [(0,0,line) for line in prorate_lines]
        self.holidays_bonus = amount_total
        for record in self.holiday_status_id:
            name = record.name
            if record.allocation_type != 'no':
                name = "%(count)s" % {
                    'count': _('%g días restantes de %g') % (
                        float_round(record.virtual_remaining_leaves, precision_digits=2) or 0.0,
                        float_round(record.max_leaves, precision_digits=2) or 0.0,
                    )
                }
        self.remaining_days = name

    #Columns
    holidays_bonus = fields.Float(compute='_compute_bonus', string='Holidays total bonus')
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato')
    prorate_lines = fields.One2many(comodel_name='hr.holidays.prorate', inverse_name='leave_id', compute='_compute_bonus', store='True',string='Holidays Bonus')
    remaining_days = fields.Char(compute='_compute_remaining_days', string='Remaining')
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('confirmed', 'Confirmed'),
    # ], string='State', default='draft')


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
    input_id = fields.Many2one(comodel_name='hr.rule.input', string='Input')
    leave_id = fields.Many2one(comodel_name='hr.leave', string='Holidays Form')