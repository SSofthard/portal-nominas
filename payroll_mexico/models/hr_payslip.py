# -*- coding: utf-8 -*-

import babel

from datetime import datetime
from pytz import timezone
from .tool_convert_numbers_letters import numero_to_letras

from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    payroll_type = fields.Selection([
            ('ordinary_payroll', 'Ordinary Payroll'),
            ('extraordinary_payroll', 'Extraordinary Payroll')], 
            string='Payroll Type', 
            default="ordinary_payroll", 
            # required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
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
            ('12', 'December')], string='Payroll month', 
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_of_month = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6')], string='Payroll of the month', 
            required=True, 
            default="1",
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_period = fields.Selection([
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('decennial', 'Decennial'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly')], 
            string='Payroll period', 
            default="biweekly",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    input_ids = fields.Many2many('hr.inputs', string="Inpust reported on payroll")
    table_id = fields.Many2one('table.settings', string="Table Settings")
    subtotal_amount_untaxed = fields.Float(string='Base imponible')
    amount_tax = fields.Float(string='Impuestos')
    payroll_tax_count = fields.Integer(compute='_compute_payroll_tax_count', string="Payslip Computation Details")
    move_infonacot_id = fields.Many2one('hr.credit.employee.account', string="FONACOT Move")
    group_id = fields.Many2one('hr.group', string="Group/Company", related="employee_id.group_id")
    integral_salary = fields.Float(string = 'Salario diario integral', related='contract_id.integral_salary')
    employer_register_id = fields.Many2one('res.employer.register', "Employer Register", required=False)
    # ~ integral_variable_salary = fields.Float(string = 'Salario diario variable', compute='_compute_integral_variable_salary')
    
    # ~ CFDI
    
    way_pay = fields.Selection([
            ('99', '99 - Por Definir'),
            ], 
            string='way to pay', 
            default="99",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    type_voucher = fields.Selection([
            ('N', 'Payroll'),
            ], 
            string='Type of voucher', 
            default="N",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    payment_method = fields.Selection([
            ('PUE', 'Payment in a single exhibition'),
            ], 
            string='Payment method', 
            default="PUE",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    cfdi_use = fields.Selection([
            ('P01', 'To define'),
            ], 
            string='Cfdi use', 
            default="P01",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    invoice_status = fields.Selection([
            ('factura_no_generada', 'Factura no generada'),
            ('factura_correcta', 'Factura correcta'),
            ('problemas_factura', 'Problemas con la factura'),
            ('problemas_cancelada', 'Factura cancelada'),
            ], 
            string='Invoice Status', 
            default="factura_no_generada",
            required=False,
            readonly=True)
    fiscal_folio = fields.Char(string='Fiscal Folio')
    

    @api.depends('subtotal_amount_untaxed')
    def _compute_integral_variable_salary(self):
        '''Este metodo se utiliza para el cálculo de salario diario integral variable'''
        perception_types = ['001','002','007','010','019','020','021','022']
        days_factor = {
                       'daily':1,
                       'weekly':7,
                       'decennial':10,
                       'biweekly':15,
                       'monthly':30,
                       }
        list_percepcions = self.line_ids.filtered(lambda o: o.salary_rule_id.type == 'perception' and
                                                                o.salary_rule_id.type_perception in perception_types
                                                                )
        total_perception = self.get_total_perceptions_to_sv(list_percepcions)
        factor_days = (self.employee_id.group_id.days/30)*days_factor[self.payroll_period]
        self.integral_variable_salary = total_perception/factor_days

    # ~ def get_total_perceptions_to_sv(self, lines):
        # ~ '''
        # ~ Este metodo permite consultar si la regla aplica según los criterios de evaluación por ley
        # ~ '''
        # ~ vals=[]
        # ~ for line in lines:
            # ~ if line.salary_rule_id.type_perception == '010':
                # ~ print ('''cuando el importe de cada uno no exceda del 10% del último SBC comunicado al
                        # ~ Seguro Social, de ser así la cantidad que rebase integrará''')
                # ~ proporcion_percepcion = line.amount/self.contract.salary_var
                # ~ if proporcion_percepcion > 0.1:
                    # ~ restante = (line.amount - (self.contract.salary_var*0.1))*line.quantity
                    # ~ vals.append(restante)
            # ~ if line.salary_rule_id.type_perception == '019':
                # ~ print ('''el generado dentro de los límites señalados en la Ley Federal del Trabajo (LFT), esto es que no
                        # ~ exceda de tres horas diarias ni de tres veces en una semana''')
                # ~ vals.append(line.total)
            # ~ if line.salary_rule_id.type_perception == '007':
                # ~ print ('''si su importe no rebasa el 40% del SMGVDF, de lo contrario el excedente se integrará''')
                # ~ minimum_salary = self.company_id.municipality_id.get_salary_min(self.date_from)
                # ~ if line.amount > (minimum_salary*0.40):
                    # ~ restante = (line.amount - (minimum_salary*0.40))*line.quantity
                    # ~ vals.append(restante)
            # ~ else:
                # ~ vals.append(line.total)
        # ~ return sum(vals)

    @api.multi
    def print_payroll_cfdi(self):
        payroll_dic = {}
        lines = []
        domain = [('slip_id','=', self.id)]
        sd = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI002')]).mapped('total'))
        sdi = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI003')]).mapped('total'))
        total_percep = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'P195')]).mapped('total'))
        total_ded = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'D103')]).mapped('total'))
        total = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'T001')]).mapped('total'))
        line_ids = self.env['hr.payslip.line'].search(domain + [('appears_on_payslip','=', True), ('total','!=', 0)])
        for line in line_ids:
            if line.category_id.code == 'PERCEPCIONES':
                lines.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'PERCEPCIONES',
                })
            if line.category_id.code == 'DED':
                lines.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'DED',
                })
        bank_account=self.env['bank.account.employee'].search([('employee_id','=', self.employee_id.id),('predetermined','=', True)])
        payroll_dic['name'] = self.employee_id.complete_name
        payroll_dic['enrollment'] = self.employee_id.enrollment
        payroll_dic['ssnid'] = self.employee_id.ssnid
        payroll_dic['rfc'] = self.employee_id.rfc
        payroll_dic['curp'] = self.employee_id.curp
        payroll_dic['date_from'] = self.date_from
        payroll_dic['date_to'] = self.date_to
        payroll_dic['payroll_period'] = dict(self._fields['payroll_period']._description_selection(self.env)).get(self.payroll_period).upper()
        payroll_dic['no_period'] = self.payroll_of_month
        payroll_dic['paid_days'] = 15
        payroll_dic['sd'] = sd
        payroll_dic['sdi'] = sdi
        payroll_dic['total_percep'] = total_percep
        payroll_dic['total_ded'] = total_ded
        payroll_dic['total'] = total
        payroll_dic['total_word'] = numero_to_letras(abs(total)) or 00
        payroll_dic['decimales'] =  str(round(total, 2)).split('.')[1] or 00
        payroll_dic['company'] = self.company_id.name.upper() or ''
        payroll_dic['lines'] = lines
        payroll_dic['bank'] = bank_account.bank_id.name
        payroll_dic['bank_account'] = bank_account.bank_account
        # Buscar Faltas
        leave_type = self.env['hr.leave.type'].search([('code','!=',False)])
        total_faults = 0
        absenteeism = 0
        inhability = 0
        for leave in leave_type:
            for wl in self.worked_days_line_ids:
                if leave.code == wl.code:
                    if leave.time_type == 'inability':
                        inhability += wl.number_of_days
                    if leave.time_type == 'leave':
                        absenteeism += wl.number_of_days
        total_faults += inhability + absenteeism
        payroll_dic['faults'] = total_faults
        data={
            'payroll_data':payroll_dic,
            'docs_ids':self.id,
            }
        
        return self.env.ref('payroll_mexico.action_payroll_cfdi_report').report_action(self,data) 
    
    @api.multi
    def print_payroll_receipt(self):
        payroll_dic = {}
        lines = []
        domain = [('slip_id','=', self.id)]
        sd = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI002')]).mapped('total'))
        sdi = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI003')]).mapped('total'))
        total_percep = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'P195')]).mapped('total'))
        total_ded = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'D103')]).mapped('total'))
        total = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'T001')]).mapped('total'))
        line_ids = self.env['hr.payslip.line'].search(domain + [('appears_on_payslip','=', True), ('total','!=', 0)])
        for line in line_ids:
            if line.category_id.code == 'PERCEPCIONES':
                lines.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'PERCEPCIONES',
                })
            if line.category_id.code == 'DED':
                lines.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'DED',
                })
        payroll_dic['name'] = self.employee_id.complete_name
        payroll_dic['ssnid'] = self.employee_id.ssnid
        payroll_dic['rfc'] = self.employee_id.rfc
        payroll_dic['curp'] = self.employee_id.curp
        payroll_dic['date_from'] = self.date_from
        payroll_dic['date_to'] = self.date_to
        payroll_dic['payroll_period'] = dict(self._fields['payroll_period']._description_selection(self.env)).get(self.payroll_period).upper()
        payroll_dic['no_period'] = self.payroll_of_month
        payroll_dic['paid_days'] = abs(self.date_from - self.date_to).days
        payroll_dic['sd'] = sd
        payroll_dic['sdi'] = sdi
        payroll_dic['total_percep'] = total_percep
        payroll_dic['total_ded'] = total_ded
        payroll_dic['total'] = total
        payroll_dic['total_word'] = numero_to_letras(abs(total)) or 00
        payroll_dic['decimales'] =  str(round(total, 2)).split('.')[1] or 00
        payroll_dic['company'] = self.company_id.name.upper() or ''
        payroll_dic['lines'] = lines
        # Buscar Faltas
        leave_type = self.env['hr.leave.type'].search([('code','!=',False)])
        total_faults = 0
        absenteeism = 0
        inhability = 0
        for leave in leave_type:
            for wl in self.worked_days_line_ids:
                if leave.code == wl.code:
                    if leave.time_type == 'inability':
                        inhability += wl.number_of_days
                    if leave.time_type == 'leave':
                        absenteeism += wl.number_of_days
        total_faults += inhability + absenteeism
        payroll_dic['faults'] = total_faults
        data={
            'payroll_data':payroll_dic
            }
        return self.env.ref('payroll_mexico.action_payroll_receipt_report').report_action(self,data)      

    @api.multi
    def _compute_payroll_tax_count(self):
        for payslip in self:
            line_ids = payslip.line_ids.filtered(lambda o: o.salary_rule_id.payroll_tax == True)
            payslip.payroll_tax_count = len(line_ids)

    @api.multi
    def action_view_payroll_tax(self):
        line_ids = self.mapped('line_ids')
        action = self.env.ref('hr_payroll.act_payslip_lines').read()[0]
        if len(line_ids) >= 1:
            line_tax_ids = line_ids.filtered(lambda o: o.salary_rule_id.payroll_tax == True)
            action['domain'] = [('id', 'in', line_tax_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


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
    
    @api.multi
    def compute_sheet(self):
        for payslip in self:
            if not payslip.settlement:
                number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            else:
                number = payslip.number or self.env['ir.sequence'].next_by_code('salary.settlement')
            payslip.search_inputs()
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
            if payslip.settlement:
                val = {
                    'contract_id':payslip.contract_id.id,
                    'employee_id':payslip.employee_id.id,
                    'type':'02',
                    'date': payslip.date_end,
                    'wage':payslip.contract_id.wage,
                    'salary':payslip.contract_id.integral_salary,
                    'reason_liquidation':payslip.reason_liquidation,
                    }
                self.env['hr.employee.affiliate.movements'].create(val)
                payslip.contract_id.state = 'close'
                history = self.env['hr.change.job'].search([('employee_id', '=', self.employee_id.id),('contract_id', '=', self.contract_id.id)], limit=1)
                history.date_to = self.date_end
                if self.contract_id.contracting_regime == '2':
                    infonavit = self.env['hr.infonavit.credit.line'].search([('employee_id', '=', self.employee_id.id),('state', 'in', ['active','draft','discontinued'])], limit=1)
                    if infonavit:
                        infonavit.state = 'closed'
                        val_infonavit = {
                            'move_type': 'low_credit',
                            'date': self.date_end,
                            'infonavit_id':infonavit.id,
                            }
                        self.env['hr.infonavit.credit.history'].create(val_infonavit)
                   
        return True
    
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
        if self.settlement:
            self.name= _('FINIQUITO %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        else:
            self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))

        if not self.contract_id or employee.id != self.contract_id.employee_id.id:
            self.contract_id = False
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
        if not contracts[0].date_end and self.settlement:
            self.contract_id = False
            self.worked_days_line_ids = []
            return
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
    
    @api.multi
    def compute_amount_untaxed(self):
        '''
        Este metodo calcula el monto de base imponible para la nomina a este monto se le calculara el impuesto
        '''
        for payslip in self:
            lines_untaxed = payslip.line_ids.filtered(lambda line: line.salary_rule_id.type == 'perception' and line.salary_rule_id.payroll_tax)
            payslip.subtotal_amount_untaxed = sum(lines_untaxed.mapped('amount'))
            payslip.get_tax_amount()


    @api.multi
    def get_tax_amount(self):
        '''
        Este metodo calcula el monto de impuesto para la nomina
        '''
        self.amount_tax = self.env['hr.isn'].get_value_isn(self.employee_id.work_center_id.state_id.id, self.subtotal_amount_untaxed, self.date_from.year)


    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to,payroll_period=False ):
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
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
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
            period = self.payroll_period
            if payroll_period:
                period = payroll_period
            if (to_full - from_full).days >= payroll_periods_days[period]:
                cant_days = payroll_periods_days[period]*(days_factor/30)
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
    
    @api.multi
    def unlink(self):
        for pay in self:
            pay.input_ids.write({'payslip':False,'state':'approve'})
        return super(HrPayslip, self).unlink()

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
    payroll_tax = fields.Boolean('Apply payroll tax?', default=False, help="If selected, this rule will be taken for the calculation of payroll tax.")
    settlement = fields.Boolean(string='Settlement structure?')

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

    @api.multi
    def name_get(self):
        result = []
        for inputs in self:
            name = '%s %s %s' %(inputs.employee_id.name.upper(), inputs.input_id.name.upper(), str(inputs.amount))
            result.append((inputs.id, name))
        return result


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
    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=False)
