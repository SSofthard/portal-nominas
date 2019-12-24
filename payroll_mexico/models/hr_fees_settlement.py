# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone
import io
import base64


import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.osv import expression


class HrFeeSettlement(models.Model):
    _name = 'hr.fees.settlement'

    @api.depends('fees_settlement_lines')
    def _compute_values(self):
        '''Este me'''


    #Columns
    name = fields.Char(string='Name')
    year = fields.Integer(string='Periodo (Año)')
    month = fields.Integer(string='Periodo (Mes)')
    cuota_fija = fields.Float(string='Cuota Fija', readonly=True, required=False,)
    exedente_3uma = fields.Float(string='Excedente', readonly=True, required=False,)
    prestaciones_en_dinero = fields.Float(string='Prestaciones en dinero', readonly=True, required=False,)
    gastos_medicos_pensionados = fields.Float(string='Gastos medicos pensionados', readonly=True, required=False,)
    maternidad = fields.Float(string='Maternidad', readonly=True, required=False,)
    riesgo_trabajo = fields.Float(string='Riesgo de trabajo', readonly=True, required=False,)
    invalidez_vida = fields.Float(string='Invalidez y vida', readonly=True, required=False,)
    gps = fields.Float(string='Guarderías y Prestaciones Sociales', readonly=True, required=False,)
    actualizacion_imss = fields.Float(string='Actualización', readonly=True, required=False,)
    recargos_imss = fields.Float(string='Recargos', readonly=True, required=False,)
    retiro = fields.Float(string='Retiro', readonly=True, required=False,)
    cesantia = fields.Float(string='Cesantía en edad avanzada y vejez', readonly=True, required=False,)
    actualizacion_infonavit = fields.Float(string='Actualización Infonavit', readonly=True, required=False,)
    recargos_infonavit = fields.Float(string='Recargos Infonavit', readonly=True, required=False,)
    aportaciones_voluntarias = fields.Float(string='Aportaciones voluntarias', readonly=True, required=False,)
    aportaciones_complementarias = fields.Float(string='Aportaciones complementarias', readonly=False, required=False,)
    aportacion_patronal_sc = fields.Float(string='Aportación patronal sin credito', readonly=True, required=False,)
    aportacion_patronal_cc = fields.Float(string='Aportación patronal con credito', readonly=True, required=False,)
    amortizacion = fields.Float(string='Amortización', readonly=True, required=False,)
    act_aport_amort = fields.Float(string='Actualización de Aportaciones y Amortizaciones', readonly=False, required=False,)
    rec_aport_amort = fields.Float(string='Recargos de Aportaciones y Amortizaciones', readonly=False, required=False,)
    multa = fields.Float(string='Multa', readonly=False, required=False,)
    fundemex = fields.Float(string='Donativo FUNDEMEX', readonly=True, required=False,)
    date_start = fields.Date('Desde')
    date_end = fields.Date('Hasta')
    group_id = fields.Many2one(comodel_name='hr.group', string='Grupo / Empresa')
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free'),
    ], string='Contracting Regime', required=True, default="2")
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", store=True)
    fees_settlement_lines = fields.One2many(inverse_name='sheet_settlement_id', comodel_name='hr.fees.settlement.details',string='Detalles de liquidación de cuotas')
    state = fields.Selection([('draft', 'Borrador'),('confirmed','Confirmado')],copy=False, default='draft')

    @api.multi
    def get_values(self):
        '''
        Este metodo obtiene los valores correspondiente para cada uno de los elementos declarados con relacion a las nominas ejecutadas en el mes.
        que se corre la liquidación de cuotas de IMSS
        '''
        self.fees_settlement_lines.unlink()
        print('kdmkjsdnkjsndkjasndkjsadn')
        payslip_run_ids = self.env['hr.payslip.run'].search(
            [('date_start', '>=', self.date_start), ('date_end', '<=', self.date_end)])
        employee_ids = payslip_run_ids.mapped('slip_ids.employee_id')
        print(employee_ids)
        print(employee_ids)
        print(employee_ids)
        print(employee_ids)
        self.fees_settlement_lines = self.fees_settlement_lines.get_values(payslip_run_ids)
        self.cuota_fija = sum(self.fees_settlement_lines.mapped('cuota_fija'))
        self.exedente_3uma = sum(self.fees_settlement_lines.mapped('exedente_3uma_patronal')) + sum(self.fees_settlement_lines.mapped('exedente_3uma_patronal'))
        self.prestaciones_en_dinero = sum(self.fees_settlement_lines.mapped('pd_patronal')) + sum(self.fees_settlement_lines.mapped('pd_obrero'))
        self.riesgo_trabajo = sum(self.fees_settlement_lines.mapped('riesgos_trabajo'))
        self.invalidez_vida = sum(self.fees_settlement_lines.mapped('iv_patronal')) + sum(self.fees_settlement_lines.mapped('iv_obrero'))
        self.gps = sum(self.fees_settlement_lines.mapped('guarderia_ps'))
        self.retiro = sum(self.fees_settlement_lines.mapped('retiro'))
        self.cesantia = sum(self.fees_settlement_lines.mapped('cesantia_vejez_patronal')) + sum(self.fees_settlement_lines.mapped('cesantia_vejez_obrero'))
        self.aportaciones_voluntarias = sum(self.fees_settlement_lines.mapped('aporte_voluntario_sar'))
        self.aportacion_patronal_sc = sum(self.fees_settlement_lines.mapped('aporte_patronal_sc'))
        self.aportacion_patronal_cc = sum(self.fees_settlement_lines.mapped('aporte_patronal_cc'))
        self.amortizacion = sum(self.fees_settlement_lines.mapped('amortizacion'))
        self.gastos_medicos_pensionados = sum(self.fees_settlement_lines.mapped('gmp_patronal'))+sum(self.fees_settlement_lines.mapped('gmp_obrero'))


        # for payslip_run_id in payslip_run_ids.mapped(''):
    @api.multi
    def action_confirm(self):
        '''
        Este metodo es para imprimir el txt de la liquidación que va a ser
        '''
        print ('action_confirm')
        print ('action_confirm')
        print ('action_confirm')
        print ('action_confirm')
        self.write({'state':'confirmed'})


    def action_print_txt(self):
        '''
        Este metodo es para imprimir el txt de la liquidación que va a ser
        '''
        output = io.BytesIO()
        print ('imprimir txt')
        print ('imprimir txt')
        print ('imprimir txt')
        print ('imprimir txt')
        f_name = 'Liquidacion de cuotas IMSS: Del %s al %s' % (self.date_start, self.date_end)
        content = 'prueba\tprueba\n'
        print (type(content))
        data = base64.encodebytes(bytes(content, 'utf-8'))
        export_id = self.env['hr.fees.settlement.report.txt'].create(
            {'txt_file': data, 'file_name': f_name + '.txt'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.fees.settlement.report.txt',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': export_id.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class HrFeeSettlementDetails(models.Model):
    _name = 'hr.fees.settlement.details'

    relaction_rule_IMSS = {
        'cuota_fija': 'UI112',
        'exedente_3uma_patronal': 'UI113',
        'exedente_3uma_obrero': 'UI114',
        'pd_patronal': 'UI115',
        'pd_obrero': 'UI116',
        'gmp_patronal': 'UI117',
        'gmp_obrero': 'UI118',
        'riesgos_trabajo': 'UI111',
        'iv_patronal': 'UI119',
        'iv_obrero': 'UI120',
        'sdi': 'UI003',
        'retiro': 'P100',
        'cesantia_vejez_patronal': 'UI123',
        'cesantia_vejez_obrero': 'UI124',
        'aporte_patronal_sc': '',
        'aporte_patronal_cc': '',
        'amortizacion': 'D094',
        'aporte_voluntario_sar': 'D091',
        'aporte_voluntario_infonavit': 'D092',
        'guarderia_ps': 'UI121',
    }

    #Columns
    year = fields.Integer(string='Periodo (Año)')
    month = fields.Integer(string='Periodo (Mes)')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado')
    incapacidades = fields.Integer(string='Incapacidades', readonly=True, required=False,)
    ausencias = fields.Integer(string='Ausencias', readonly=True, required=False,)
    cuota_fija = fields.Float(string='Cuota Fija', readonly=True, required=False,)
    exedente_3uma_patronal = fields.Float(string='Excedente a 3 UMA', readonly=True, required=False, )
    exedente_3uma_obrero = fields.Float(string='Excedente a 3 UMA', readonly=True, required=False, )
    pd_patronal = fields.Float(string='Prestaciones en dinero (Patronal)', readonly=True, required=False, )
    pd_obrero = fields.Float(string='Prestaciones en dinero (Obrero)', readonly=True, required=False, )
    gmp_patronal = fields.Float(string='Gastos medicos pensionados (Patronal)', readonly=True, required=False, )
    gmp_obrero = fields.Float(string='Gastos medicos pensionados (Obrero)', readonly=True, required=False, )
    riesgos_trabajo = fields.Float(string='Riesgo de trabajo', readonly=True, required=False, )
    iv_patronal = fields.Float(string='Invalidez y vida', readonly=True, required=False, )
    iv_obrero = fields.Float(string='Invalidez y vida', readonly=True, required=False, )
    guarderia_ps = fields.Float(string='Guarderia y Prestaciones sociales', readonly=True, required=False, )
    suma_patronal = fields.Float(string='Total patronal', readonly=True, required=False, )
    suma_obrero = fields.Float(string='Total obrero', readonly=True, required=False, )
    sdi = fields.Float(string='Salario Diario Integral', readonly=True, required=False, )
    retiro = fields.Float(string='Retiro', readonly=True, required=False, )
    cesantia_vejez_patronal = fields.Float(string='Cesantía Vejez (Patronal)', readonly=True, required=False, )
    cesantia_vejez_obrero = fields.Float(string='Cesantía Vejez (Obrero)', readonly=True, required=False, )
    aporte_patronal_sc = fields.Float(string='Aportación Patronal sin credito', readonly=True, required=False, )
    aporte_patronal_cc = fields.Float(string='Aportación Patronal con credito', readonly=True, required=False, )
    amortizacion = fields.Float(string='Amortización', readonly=True, required=False, )
    aporte_voluntario_sar = fields.Float(string='Aporte Voluntario', readonly=True, required=False, )
    aporte_voluntario_infonavit = fields.Float(string='Aporte Voluntario Infonavit', readonly=True, required=False, )
    date_start = fields.Date('Start Date', related='sheet_settlement_id.date_start')
    date_end = fields.Date('End Date', related='sheet_settlement_id.date_end')
    sheet_settlement_id = fields.Many2one(comodel_name='hr.fees.settlement', string='Liquidación de cuotas')

    @api.multi
    def get_values(self,payslip_run_ids):
        '''
        Este metodo busca particularmente para cada empleado los valores de las nominas dentro de periodo seleccionado.
        '''
        list_res = []
        employee_ids = payslip_run_ids.mapped('slip_ids.employee_id')
        for employee_id in employee_ids:
            vals = {}
            print (employee_id)
            vals['employee_id'] = employee_id.id

            vals['incapacidades'] = sum(payslip_run_ids.mapped('slip_ids.worked_days_line_ids').filtered(
                    lambda line: line.payslip_id.employee_id.id == employee_id.id and line.code == 'F1').mapped('number_of_days'))
            vals['ausencias'] = sum(payslip_run_ids.mapped('slip_ids.worked_days_line_ids').filtered(
                    lambda line: line.payslip_id.employee_id.id == employee_id.id and line.code == 'F2').mapped('number_of_days'))
            for key in self.relaction_rule_IMSS.keys():
                vals[key] = sum(payslip_run_ids.mapped('slip_ids.line_ids').filtered(
                    lambda line: line.employee_id.id == employee_id.id and line.code == self.relaction_rule_IMSS[key]).mapped('total'))
            print (vals)
            aporte_patronal_infonavit = sum(payslip_run_ids.mapped('slip_ids.line_ids').filtered(
                    lambda line: line.employee_id.id == employee_id.id and line.code == 'UI128').mapped('total'))
            if vals['amortizacion'] > 0:
                vals['aporte_patronal_cc'] = aporte_patronal_infonavit
            else:
                vals['aporte_patronal_sc'] = aporte_patronal_infonavit


            list_res.append(vals)
        print (list_res)
        return list_res
