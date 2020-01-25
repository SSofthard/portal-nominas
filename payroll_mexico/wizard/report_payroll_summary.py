# -*- coding: utf-8 -*-

import calendar
import pytz
import dateutil
import base64
import calendar

from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class PayslipSummary(models.TransientModel):
    _name = 'hr.payslip.sumary.wizard'
    _description = 'Reporte de Resumén de Nómina'

    #Columns
    group_id = fields.Many2one('hr.group', "Group", required=True)
    payroll_month = fields.Selection([
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December')], string='Payroll month', 
            required=True, default=str(date.today().month))
    year = fields.Integer('Year', required=True, default=date.today().year)
    # ~ rule_id = fields.Many2one('hr.salary.rule', index=True,  required=True, string='Regla de negocio')

    @api.multi
    def report_print(self, data):
        self.ensure_one()
        if self.year and len(str(self.year)) != 4:
            raise ValidationError(_('El formato del año es incorrecto, verifique! \
                                    \nFormato Correcto AAAA.'))
        date_from = "%s-%s-01" % (self.year, self.payroll_month)
        date_to = "%s-%s-%s" % (self.year, self.payroll_month, calendar.monthrange(self.year, int(self.payroll_month))[1])
        
        lines = {}
        line_data = {}
        
        
        domain = [  ('slip_id.date_from','>=', date_from),('slip_id.date_to','<=', date_to),
                    ('slip_id.group_id','=', self.group_id.id)
                ]
        line_ids = self.env['hr.payslip.line'].search(domain)
        if not line_ids:
            raise ValidationError(_('No se encontró información con los datos proporcionados.'))
        # ~ employees_ids = line_ids.mapped('employee_id')
        isn = []
        total = 0
        base_ss = 0
        base_ias = 0
        neto_ss = 0
        neto_ias = 0
        isn_ss = 0
        isn_ias = 0
        imss_rcv_infonavit_ss = 0
        imss_rcv_infonavit_ias = 0
        isr_ss = 0
        isr_ias = 0
        other_ded_ss = 0
        other_ded_ias = 0
        for line in line_ids:
            if line.slip_id.payroll_type == 'O':
                if line.slip_id.payslip_run_id.contracting_regime == '02': # Sueldos y Salarios
                    if not line.slip_id.payslip_run_id.id in isn:
                        isn.append(line.slip_id.payslip_run_id.id)
                        isn_ss += line.slip_id.payslip_run_id.amount_tax
                    if line.code == 'T001':
                        neto_ss += line.total
                    if line.code == 'P001':
                        base_ss += line.total
                    if line.code in ['C001', 'D002', 'UI126', 'UI127', 'UI128']:
                        imss_rcv_infonavit_ss += line.total
                    if line.code in ['D001']:
                        isr_ss += line.total
                    if line.category_id.code == 'DED':
                        other_ded_ss += line.total
                    
                if line.slip_id.payslip_run_id.contracting_regime in ['08','09','11']: # Asimilados a Salarios
                    if not line.slip_id.payslip_run_id.id in isn:
                        isn.append(line.slip_id.payslip_run_id.id)
                        isn_ias += line.slip_id.payslip_run_id.amount_tax
                    if line.code == 'P001':
                        base_ias += line.total
                    if line.code == 'T001':
                        neto_ias += line.total
                    if line.code in ['C001', 'D002', 'UI126', 'UI127', 'UI128']:
                        imss_rcv_infonavit_ias += line.total
                    if line.code in ['D001']:
                        isr_ias += line.total
                    if line.category_id.code == 'DED':
                        other_ded_ias += line.total
                # ~ line_data.append({
                    # ~ 'enrollment': line.employee_id.enrollment,
                    # ~ 'employee_name': line.employee_id.name_get()[0][1],
                    # ~ 'contracting_regime': line.slip_id.contract_id.contracting_regime, #dict(line._fields['contracting_regime']._description_selection(self.env)).get(line.slip_id.contract_id.contracting_regime),
                    # ~ 'reference': line.slip_id.number,
                    # ~ 'linename': line.name,
                    # ~ 'date_from': line.slip_id.date_from,
                    # ~ 'date_to': line.slip_id.date_to,
                    # ~ 'total': line.total,
                # ~ })
            # ~ lines['employees'] = line_data
            # ~ lines['date_from'] = self.date_from
        lines['base_ss'] = base_ss
        lines['base_ias'] = base_ias
        lines['base_total'] = base_ss + base_ias
        
        lines['neto_ss'] = neto_ss
        lines['neto_ias'] = neto_ias
        lines['neto_total'] = neto_ss + neto_ias
        
        lines['isn_ss'] = isn_ss
        lines['isn_ias'] = isn_ias
        lines['isn_total'] = isn_ss + isn_ias
        
        lines['imss_rcv_infonavit_ss'] = imss_rcv_infonavit_ss
        lines['imss_rcv_infonavit_ias'] = imss_rcv_infonavit_ias
        lines['imss_rcv_infonavit_total'] = imss_rcv_infonavit_ss + imss_rcv_infonavit_ias
        
        lines['isr_ss'] = isr_ss
        lines['isr_ias'] = isr_ias
        lines['isr_total'] = isr_ss + isr_ias
        
        lines['other_ded_ss'] = other_ded_ss - imss_rcv_infonavit_ss
        lines['other_ded_ias'] = other_ded_ias - imss_rcv_infonavit_ias
        lines['other_ded_total'] = (other_ded_ss - imss_rcv_infonavit_ss) + (other_ded_ias - imss_rcv_infonavit_ias)
        
        lines['subtotal_ss'] = base_ss + neto_ss + isn_ss + imss_rcv_infonavit_ss + isr_ss + (other_ded_ss - imss_rcv_infonavit_ss)
        lines['subtotal_ias'] = base_ias + neto_ias + isn_ias + imss_rcv_infonavit_ias + isr_ias + (other_ded_ias - imss_rcv_infonavit_ias)
        lines['subtotal_total'] = lines.get('base_total') + lines.get('neto_total') +  lines.get('isn_total') +  lines.get('imss_rcv_infonavit_total') + lines.get('isr_total') + lines.get('other_ded_total')
        
        lines['payroll_month'] = dict(self._fields['payroll_month']._description_selection(self.env)).get(self.payroll_month)
        data={
            'lines_data':lines
        }
        return self.env.ref('payroll_mexico.action_report_payroll_sumary').with_context(from_transient_model=True).report_action(self, data=data)
