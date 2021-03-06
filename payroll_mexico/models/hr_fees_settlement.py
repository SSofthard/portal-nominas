# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone
import io
import base64
import calendar


import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.addons import decimal_precision as dp


class HrFeeSettlement(models.Model):
    _name = 'hr.fees.settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    #Columns
    name = fields.Char(string='Name')
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal")
    year = fields.Integer(string='Periodo (Año)', size=4, default=lambda self :fields.Date.context_today(self).year)
    month = fields.Selection([
        (1,'Enero'),
        (2,'Febrero'),
        (3,'Marzo'),
        (4,'Abril'),
        (5,'Mayo'),
        (6,'Junio'),
        (7,'Julio'),
        (8,'Agosto'),
        (9,'Septiembre'),
        (10,'Octubre'),
        (11,'Noviembre'),
        (12,'Diciembre')], required=True,string='Periodo (Mes)')
    cuota_fija = fields.Float(string='Cuota Fija', readonly=True, required=False,)
    exedente_3uma = fields.Float(string='Excedente', readonly=True, required=False,)
    prestaciones_en_dinero = fields.Float(string='Prestaciones en dinero', readonly=True, required=False,)
    gastos_medicos_pensionados = fields.Float(string='Gastos medicos pensionados', readonly=True, required=False,)
    maternidad = fields.Float(string='Maternidad', readonly=True, required=False,)
    riesgo_trabajo = fields.Float(string='Riesgo de trabajo', readonly=True, required=False,)
    invalidez_vida = fields.Float(string='Invalidez y vida', readonly=True, required=False,)
    gps = fields.Float(string='Guarderías y Prestaciones Sociales', readonly=True, required=False,)
    actualizacion_imss = fields.Float(string='Actualización', readonly=True, required=False,)
    subtotal_imss = fields.Float(string='Subtotal', readonly=True, required=False,)
    total_imss = fields.Float(string='Total', readonly=True, required=False,)
    recargos_imss = fields.Float(string='Recargos', readonly=True, required=False,)
    retiro = fields.Float(string='Retiro', readonly=True, required=False,)
    cesantia = fields.Float(string='Cesantía en edad avanzada y vejez', readonly=True, required=False,)
    actualizacion_infonavit = fields.Float(string='Actualización Infonavit', readonly=True, required=False,)
    recargos_infonavit = fields.Float(string='Recargos Infonavit', readonly=True, required=False,)
    subtotal_infonavit = fields.Float(string='Subtotal', readonly=True, required=False,)
    total_infonavit = fields.Float(string='Total', readonly=True, required=False,)
    aportaciones_voluntarias = fields.Float(string='Aportaciones voluntarias', readonly=True, required=False,)
    aportaciones_complementarias = fields.Float(string='Aportaciones complementarias', readonly=False, required=False,)
    aportacion_patronal_sc = fields.Float(string='Aportación patronal sin credito', readonly=True, required=False,)
    aportacion_patronal_cc = fields.Float(string='Aportación patronal con credito', readonly=True, required=False,)
    amortizacion = fields.Float(string='Amortización', readonly=True, required=False,)
    act_aport_amort = fields.Float(string='Actualización de Aportaciones y Amortizaciones', readonly=True, required=False,)
    rec_aport_amort = fields.Float(string='Recargos de Aportaciones y Amortizaciones', readonly=True, required=False,)
    subtotal_aport_amort = fields.Float(string='Subtotal', readonly=True, required=False,)
    total_aport_amort = fields.Float(string='Total', readonly=True, required=False,)
    multa = fields.Float(string='Multa', readonly=False, required=False,)
    fundemex = fields.Float(string='Donativo FUNDEMEX', readonly=False, required=False,)
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
    payment_type = fields.Selection([('1', 'Pago Oportuno'), ('2', 'Pago Extemporaneo')], string='Tipo de pago', required=True)
    payment_date = fields.Date(string='Fecha de pago')
    regulatory_payment_date = fields.Date(string='Fecha de pago reglamentaria', compute='get_date_payment')
    index_update = fields.Float(string='Indice de actualizacion', compute='get_index_update',  digits=dp.get_precision('Payroll Rate'))
    subtotal = fields.Float(string='Total')
    total = fields.Float(string='Total a pagar')
    amount_total_update = fields.Float(string='Total a pagar')
    percentage_mothly = fields.Float(string='Porcentaje mensual %', default=1.47)
    percentage_total = fields.Float(string='Porcentaje total %')
    surcharge_amount = fields.Float(string='Monto de recargo')
    attachment_number = fields.Integer(string='Documentos adjuntos', compute='_compute_attachment_number')

    @api.multi
    def write(self,vals):
        '''
        Se utiliza para guardar la fecha de pago
        '''
        if self.payment_type == '1':
            vals['payment_date']=self.regulatory_payment_date
        return super(HrFeeSettlement,self).write(vals)

    @api.multi
    @api.onchange('payment_type')
    def onchange_payment_type(self):
        '''
        Este metodo se ejecuta cuando se cambia el tipo de pago de la liquidacion de cuotas, a traves de el se calcula
        los recargos y actualizaciones para el pago de la misma, tambien segun el tipo de pago se define la fecha de pago.
        '''
        if self.payment_type == '1':
            self.payment_date = self.regulatory_payment_date

    @api.one
    @api.depends('year', 'month', 'payment_date')
    def get_index_update(self):
        '''
        Este metodo obtiene el indice de actualización basado en la fechas de la liquidación / la fecha de pago
        '''
        if self.payment_date:
            index_document=self.env['hr.table.index.consume.price'].search([('year','=',self.year),('month','=',self.month)]).value
            index_payment=self.env['hr.table.index.consume.price'].search([('year','=',self.payment_date.year),('month','=',self.payment_date.month)]).value
            if not index_document:
                raise UserError('''No se encontraron valores en la tabla de indice nacional de precios al consumidor para el periodo que se desea calcular.
                                    Por favor cargue los indices correspondientes al mes %s - %s.
                ''' % (self.month, self.year))
            if not index_payment:
                raise UserError(
                   '''No se encontraron valores en la tabla de indice nacional de precios al consumidor para el mes de pago indicado.
                      Por favor cargue los indices correspondientes al mes %s - %s.  
                   ''' % (dict(self._fields['month']._description_selection(self.env)).get(self.payment_date.month), self.payment_date.year))
            self.index_update = index_payment/index_document if self.payment_type == '2' else 1


    @api.one
    @api.depends('year','month')
    def get_date_payment(self):
        '''
        Este metodo obtiene las fechas para el pago en caso de que el pago sea de tipo oportuno
        '''
        state = self.group_id.state_id
        month_payment = self.month+1 if self.month != 12 else 1
        year_payment = self.year if self.month != 12 else self.year+1
        public_holidays_days = self.env['hr.days.public.holidays'].search([]).mapped('date')
        # public_holidays_days = self.env['hr.days.public.holidays'].search([('state_ids', 'in', state._ids)]).mapped('date')
        payment_date = date(year_payment, month_payment, 17)
        while payment_date in public_holidays_days or payment_date.weekday() in [5,6]:
            payment_date += timedelta(days=1)
        self.regulatory_payment_date = payment_date

    @api.multi
    def get_values(self):
        '''
        Este metodo obtiene los valores correspondiente para cada uno de los elementos declarados con relacion a las nominas ejecutadas en el mes.
        que se corre la liquidación de cuotas de IMSS
        '''
        self.fees_settlement_lines.unlink()
        if self.payment_type == '2':
            interes_range = self.payment_date - self.regulatory_payment_date
            interes_range = int((self.payment_date - self.regulatory_payment_date).days / 30.40)
            self.percentage_total = self.percentage_mothly * interes_range
        else:
            self.percentage_total = 0.0
        date_start = date(self.year, self.month, 1)
        last_day = calendar.monthrange(self.year,self.month)[1]
        date_end = date(self.year,self.month,last_day)
        payslip_run_rcv_ids = False
        payslip_run_ids = self.env['hr.payslip.run'].search(
            [('date_start', '>=', date_start), ('date_end', '<=', date_end),('contracting_regime', '=', 2)])
        employee_ids = payslip_run_ids.mapped('slip_ids.employee_id')
        if self.month % 2 == 0:
            date_start = date(self.year,self.month-1,1)
            payslip_run_rcv_ids = self.env['hr.payslip.run'].search(
                [('date_start', '>=', date_start), ('date_end', '<=', date_end),
                 ('contracting_regime', '=', 2)])
            employee_ids = employee_ids | payslip_run_rcv_ids.mapped('slip_ids.employee_id')
            print (employee_ids)
            print (employee_ids)
            print (employee_ids)
            print (employee_ids)
        self.fees_settlement_lines = self.fees_settlement_lines.get_values(payslip_run_ids,payslip_run_rcv_ids)
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
        print ([
            self.cuota_fija,
            self.prestaciones_en_dinero,
            self.riesgo_trabajo,
            self.invalidez_vida,
            self.gps,
            self.retiro,
            self.cesantia,
            self.aportaciones_voluntarias,
            self.aportacion_patronal_sc,
            self.aportacion_patronal_cc,
            self.amortizacion,
            self.gastos_medicos_pensionados,
        ])
        self.subtotal_imss = sum([
            self.cuota_fija,
            self.exedente_3uma,
            self.prestaciones_en_dinero,
            self.gastos_medicos_pensionados,
            self.riesgo_trabajo,
            self.invalidez_vida,
            self.gps,
        ])
        self.actualizacion_imss = self.subtotal_imss*self.index_update
        self.recargos_imss = self.actualizacion_imss*(self.percentage_total/100)
        self.total_imss = self.actualizacion_imss+self.recargos_imss
        self.subtotal_infonavit = sum([
            self.retiro,
            self.cesantia,
        ])
        self.actualizacion_infonavit = self.subtotal_infonavit * self.index_update
        self.recargos_infonavit = self.actualizacion_infonavit * (self.percentage_total / 100)
        self.total_infonavit = self.actualizacion_infonavit + self.recargos_infonavit + self.aportaciones_voluntarias + self.aportaciones_complementarias
        self.subtotal_aport_amort = sum([
            self.aportacion_patronal_sc,
            self.aportacion_patronal_cc,
            self.amortizacion,
        ])
        self.act_aport_amort = self.subtotal_aport_amort * self.index_update
        self.rec_aport_amort = self.act_aport_amort * (self.percentage_total / 100)
        self.total_aport_amort = self.act_aport_amort+self.rec_aport_amort+self.multa+self.fundemex

        self.amount_total_update = self.subtotal * self.index_update
        self.total = self.total_imss+self.total_infonavit+self.total_aport_amort


    @api.constrains('payment_date')
    def constrain_date_payment(self):
        '''
        Constrain para validar fecha de pago
        '''
        if self.payment_date < self.regulatory_payment_date:
            raise UserError('La fecha de pago no puede ser menor al los 17 días del mes siguiente al periodo a calcular')


    @api.multi
    def action_confirm(self):
        '''
        Este metodo es para imprimir el txt de la liquidación que va a ser
        '''
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
        f_name = 'Liquidacion de cuotas IMSS: %s - %s' % (self.month, self.year)
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

    @api.multi
    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.fees.settlement'), ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'hr.fees.settlement',
            'default_res_id': self.id,
            'create': False,
            'edit': False,
        }
        return res

    @api.multi
    def _compute_attachment_number(self):
        '''
        Este metodo obtiene el numero de documentos adjuntos para la liquidacion
        '''
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.fees.settlement'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for settlement in self:
            settlement.attachment_number = attachment.get(settlement.id, 0)


class HrFeeSettlementDetails(models.Model):
    _name = 'hr.fees.settlement.details'

    relaction_rule_IMSS = {
        # IMSS
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
        'guarderia_ps': 'UI121',
        # -------
        'sdi': 'UI003',

    }

    relaction_rule_Infonavit_RCV = {
        # Infonavit
        'retiro': 'P100',
        'cesantia_vejez_patronal': 'UI123',
        'cesantia_vejez_obrero': 'UI124',
        # -----------------
        # RCV
        'aporte_patronal_sc': '',
        'aporte_patronal_cc': '',
        'amortizacion': 'D094',
        'aporte_voluntario_sar': 'D091',
        'aporte_voluntario_infonavit': 'D092',
    }

    @api.one
    def _compute_totals(self):
        '''
        Este metodo calcula los totales de la cedula de autodeterminacion
        '''
        self.suma_obrero_imss = sum(
            [
                self.exedente_3uma_obrero,
                self.pd_obrero,
                self.gmp_obrero,
                self.iv_obrero,
            ]
        )
        self.suma_patronal_imss = sum(
            [
                self.cuota_fija,
                self.exedente_3uma_patronal,
                self.pd_patronal,
                self.riesgos_trabajo,
                self.iv_patronal,
                self.guarderia_ps,
            ]
        )

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
    suma_patronal_imss = fields.Float(string='Total patronal', readonly=True, required=False, compute='_compute_totals')
    suma_obrero_imss = fields.Float(string='Total obrero', readonly=True, required=False, )
    sdi = fields.Float(string='Salario Diario Integral', readonly=True, required=False, )
    retiro = fields.Float(string='Retiro', readonly=True, required=False, )
    cesantia_vejez_patronal = fields.Float(string='Cesantía Vejez (Patronal)', readonly=True, required=False, )
    cesantia_vejez_obrero = fields.Float(string='Cesantía Vejez (Obrero)', readonly=True, required=False, )
    aporte_patronal_sc = fields.Float(string='Aportación Patronal sin credito', readonly=True, required=False, )
    aporte_patronal_cc = fields.Float(string='Aportación Patronal con credito', readonly=True, required=False, )
    amortizacion = fields.Float(string='Amortización', readonly=True, required=False, )
    aporte_voluntario_sar = fields.Float(string='Aporte Voluntario', readonly=True, required=False, )
    aporte_voluntario_infonavit = fields.Float(string='Aporte Voluntario Infonavit', readonly=True, required=False, )
    sheet_settlement_id = fields.Many2one(comodel_name='hr.fees.settlement', string='Liquidación de cuotas')

    @api.multi
    def get_values(self,payslip_run_ids,payslip_run_rcv_ids=False):
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
            if payslip_run_rcv_ids:
                for key in self.relaction_rule_Infonavit_RCV.keys():
                    vals[key] = sum(payslip_run_rcv_ids.mapped('slip_ids.line_ids').filtered(
                        lambda line: line.employee_id.id == employee_id.id and line.code ==
                                     self.relaction_rule_Infonavit_RCV[key]).mapped('total'))
                aporte_patronal_infonavit = sum(payslip_run_rcv_ids.mapped('slip_ids.line_ids').filtered(
                    lambda line: line.employee_id.id == employee_id.id and line.code == 'UI128').mapped('total'))
                if vals['amortizacion'] > 0:
                    vals['aporte_patronal_cc'] = aporte_patronal_infonavit
                else:
                    vals['aporte_patronal_sc'] = aporte_patronal_infonavit
            list_res.append(vals)
        print (list_res)
        return list_res


