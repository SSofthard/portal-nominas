# -*- coding: utf-8 -*-

import time
import datetime
import calendar
import pytz
import dateutil
import base64
import locale

from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError


class HrSumaryReport(models.TransientModel):
    _name = 'hr.wizard.sumary.report'
    _description = 'Sumary Report'

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(HrSumaryReport, self).default_get(fields)
        if self._context.get('active_id'):
            active_id = int(self._context['active_id'])
            result['payslip_run_id'] = active_id
            payslip_run_id = self.env['hr.payslip.run'].search([('id', '=', active_id)], limit=1)
            result['payroll_month'] = payslip_run_id.payroll_month
        return result

    #Columns
    company_ids = fields.Many2many('res.company', string="Companies",)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True)
    wage = fields.Boolean(string='Wages and salaries', help="Hiring wages and salaries.")
    free = fields.Boolean(string='Free', help="Hiring free.")
    assimilated = fields.Boolean(string='Assimilated to salary', help="Hiring Assimilated to salary.")
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
        ('12', 'December')], 
        string='Payroll month',
        readonly=True)

    @api.onchange('payslip_run_id')
    def _onchange_payslip_run_id(self):
        if self.payslip_run_id:
            company_ids = self.payslip_run_id.slip_ids.mapped('company_id.id')
            res = {
                'domain': {
                    'company_ids': [('id', 'in', company_ids)], 
                }
            }
        return res

    @api.multi
    def report_print(self, data):
        regimen = {
            '02': 'SUELDOS Y SALARIOS',
            '05': 'SUELDO LIBRE',
            '08': 'ASIMILADOS A SALARIOS',
            '09': 'ASIMILADOS A SALARIOS',
            '11': 'ASIMILADOS A SALARIOS',
            '99': 'SUELDO LIBRE',
        }
        apply_honorarium = self.payslip_run_id.apply_honorarium
        apply_honorarium_on = self.payslip_run_id.apply_honorarium_on
        pct_honorarium = self.payslip_run_id.group_id.percent_honorarium
        iva_tax = self.payslip_run_id.iva_tax
        
        def cal_honorarium(base_salary=False, net=False):
            if apply_honorarium:
                if pct_honorarium > 0:
                    if apply_honorarium_on == 'net':
                        return round((pct_honorarium / 100) * net, 2)
                    if apply_honorarium_on == 'gross':
                        return round((pct_honorarium / 100) * base_salary, 2)
                else:
                    raise ValidationError(_("Para Cargar 'Honorarios' a la nómina establesca el valor del porcentaje al 'Grupo/Empresa'."))
            else:
                return 0.0
        
        def cal_iva(subtotal):
            if iva_tax > 0:
                return round((iva_tax / 100) * subtotal, 2)
            else:
                return 0.0
                
        result = {}
        metadata = {}
        metadata['payroll_month'] = dict(self._fields['payroll_month']._description_selection(self.env)).get(self.payroll_month)
        
        PayslipObj = self.env['hr.payslip'].sudo()
        contracting_domain = []
        domain = [('payslip_run_id','=',self.payslip_run_id.id)]
        if self.company_ids:
            domain += [('company_id','in', self.company_ids.ids)]
        
        if self.wage:
            contracting_domain += ['02']
        if self.free:
            contracting_domain += ['05','99']
        if self.assimilated:
            contracting_domain += ['08','09','11']
        if contracting_domain:
            domain += [('contracting_regime','in', contracting_domain)]
        payslips = PayslipObj.search(domain, order="date_from asc, id asc")
        if not payslips:
            raise UserError(_('No results found.'))
            
        for payslip in payslips:
            base_salary = []
            net = []
            imss_rcv_infonavit = []
            isr = []
            contracting_regime = regimen[payslip.contracting_regime]
            if contracting_regime not in result:
                result[contracting_regime] = {}
            if 'base_salary' not in result[contracting_regime]:
                result[contracting_regime]['base_salary'] = 0
            if 'net' not in result[contracting_regime]:
                result[contracting_regime]['net'] = 0
            if 'imss_rcv_infonavit' not in result[contracting_regime]:
                result[contracting_regime]['imss_rcv_infonavit'] = 0
            if 'isr' not in result[contracting_regime]:
                result[contracting_regime]['isr'] = 0
            if 'honorarium' not in result[contracting_regime]:
                result[contracting_regime]['honorarium'] = []
            if 'subtotal' not in result[contracting_regime]:
                result[contracting_regime]['subtotal'] = 0
            if 'iva' not in result[contracting_regime]:
                result[contracting_regime]['iva'] = 0
            if 'regimen' not in result[contracting_regime]:
                result[contracting_regime]['regimen'] = []
            if 'isn' not in result[contracting_regime]:
                result[contracting_regime]['isn'] = 0
            
            base_salary.append(sum(payslip.line_ids.filtered(lambda l: l.code == 'P195').mapped('total')))
            net.append(sum(payslip.line_ids.filtered(lambda l: l.code == 'T001').mapped('total')))
            imss_rcv_infonavit.append(sum(payslip.line_ids.filtered(lambda l: l.code in ('C001', 'D002', 'UI126', 'UI127', 'UI128')).mapped('total')))
            isr.append(sum(payslip.line_ids.filtered(lambda l: l.code == 'D001').mapped('total')))
            
            result[contracting_regime]['base_salary'] += round(sum(base_salary), 2)
            result[contracting_regime]['net'] += round(sum(net), 2)
            result[contracting_regime]['imss_rcv_infonavit'] += round(sum(imss_rcv_infonavit), 2)
            result[contracting_regime]['isr'] += round(sum(isr), 2)
            result[contracting_regime]['honorarium'] = cal_honorarium(result[contracting_regime]['base_salary'], result[contracting_regime]['net'])
            result[contracting_regime]['subtotal']  = result[contracting_regime]['base_salary'] + \
                                                    result[contracting_regime]['imss_rcv_infonavit'] + \
                                                    result[contracting_regime]['isr'] +\
                                                    result[contracting_regime]['honorarium']
            result[contracting_regime]['iva'] = cal_iva(result[contracting_regime]['subtotal'])
            result[contracting_regime]['total'] = result[contracting_regime]['subtotal'] + result[contracting_regime]['iva']
        data = {
            'data': result,
            'metadata': metadata,
        }
        return self.env.ref('payroll_mexico.action_payroll_summary_report_multi').report_action(self, data)  
