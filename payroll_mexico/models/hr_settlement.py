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
    
    settlement = fields.Boolean(string='Settlement')
    settlemen_date = fields.Date(string='Settlemen date', readonly=True, required=False,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)), states={'draft': [('readonly', False)]})
    reason_liquidation = fields.Selection([
            ('1', 'TERMINACIÓN DE CONTRATO'),
            ('2', 'SEPARACIÓN VOLUNTARIA'),
            ('3', 'ABANDONO DE EMPLEO'),
            ('4', 'DEFUNCIÓN'),
            ('7', 'AUSENTISMOS'),
            ('8', 'RESICIÓN DE CONTRATO'),
            ('9', 'JUBILACIÓN'),
            ('A', 'PENSIÓN'),
            ('5', 'CLAUSURA'),
            ('6', 'OTROS'),
            ], 
            string='Reason for liquidation', 
            required=False,
            states={'draft': [('readonly', False)]})
    agreement_employee = fields.Boolean(string='Agreement with the employee')
    amount_agreement = fields.Float('Amount of the agreement', required=False)
    indemnify_employee = fields.Boolean(string='Indemnify the employee')
    # ~ compensation_20 = fields.Boolean(string='I will pay the compensation of 20 days per year worked?')
    
    previous_contract_date = fields.Date('Previous Contract Date', related="contract_id.previous_contract_date", help="Start date of the previous contract for antiquity.")
    date_start = fields.Date('Start Date', required=True, default=fields.Date.today,
        help="Start date of the contract.", related="contract_id.date_start")
    date_end = fields.Date('End Date',
        help="End date of the contract", related="contract_id.date_end")
    years_antiquity = fields.Integer(string='Antiquity', related="contract_id.years_antiquity")
    days_rest = fields.Integer(string='Días de antigüedad ultimo año', related="contract_id.days_rest")
    type_contract = fields.Selection(string='Tipo de contrato', related="contract_id.type_id.type")
    
    @api.onchange('complete_name')
    def _compute_complete_name(self):
        for name in self:
            complete_name = name.name
            if name.last_name: 
                complete_name += ' ' + name.last_name
            if name.last_name: 
                complete_name += ' ' + name.mothers_last_name
            name.complete_name = complete_name
    
    @api.onchange('indemnify_employee','agreement_employee')
    def _compute_complete_name(self):
        for settlement in self:
            if settlement.indemnify_employee:
                settlement.agreement_employee = False
                settlement.amount_agreement = 0
            if settlement.agreement_employee:
                settlement.indemnify_employee = False
            else:
                settlement.amount_agreement = 0
            
    @api.multi
    def print_settlement_report(self):
        payroll_dic = {}
        data={
            'payroll_data':payroll_dic
            }
        return self.env.ref('payroll_mexico.action_report_settlement_template').report_action(self, {})

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    settlement = fields.Boolean(string='Settlement structure?')
    payroll_type = fields.Selection([
            ('O', 'Ordinary Payroll'),
            ('E', 'Extraordinary Payroll')], 
            string='Payroll Type', 
            required=True,)
