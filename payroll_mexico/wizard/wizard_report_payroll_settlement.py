# -*- coding: utf-8 -*-

import io
import base64
import xlsxwriter
import locale

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class payrollReportSettlement(models.TransientModel):
    _name = "payroll.report.settlement"
    _description = 'Settlement Report'

    #Columns
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    type = fields.Selection([
        ('1', 'Consolidated'),
        ('2', 'Per employee'),
         ],string = 'Type', required=True, default='1')
    employee_ids = fields.Many2many('hr.employee','report_settlement_employee_rel','report_settlement_id','employee_id', "Employees", required=False)
    salary_rule_ids = fields.Many2many('hr.salary.rule','report_settlement_salary_rule_rel','report_settlement_id','salary_rule_id', "Salary rules", required=False)

    @api.onchange('salary_rule_ids')
    def onchange_salary_rule_id(self):
        structure = self.env['hr.payroll.structure'].search([('settlement','=',True)])
        rule_ids = []
        for rule in structure.rule_ids:
            if rule.id not in rule_ids and rule.print_to_excel:
                rule_ids.append(rule.id)
        return {'domain': {'salary_rule_ids': [('id', 'in', rule_ids)]}}


    @api.multi
    def get_report_data(self):
        data={}
        if self.type == '2':
            domain = [('struct_id.settlement','=',True),
                      ('settlemen_date', '>=', self.date_from),
                      ('settlemen_date', '<=', self.date_to),
                      ('group_id', '=', self.group_id.id),
                      ('state', 'in', ['done'])]
            domain_rule = [('salary_rule_id.print_to_excel','=',True),
                            ('slip_id.settlemen_date', '>=', self.date_from),
                            ('slip_id.settlemen_date', '<=', self.date_to),
                            ('slip_id.group_id', '<=', self.group_id.id),
                            ('slip_id.struct_id.settlement','=',True),
                            ('slip_id.state','in',['done']),
                            ('total','>',0)]
            per_employee = {}
            amount_total = {}
            if self.employee_ids:
                domain.append(('employee_id','in',self.employee_ids.ids))
            if self.salary_rule_ids:
                domain_rule.append(('salary_rule_id','in',self.salary_rule_ids.ids))
            settlement_ids = self.env['hr.payslip'].search(domain)
            if not settlement_ids:
                raise UserError(_('There are no settlements for the requested search..'))
            salary_rule_list =   list(map(lambda x: x.code, self.env['hr.payslip.line'].search(domain_rule).mapped('salary_rule_id')))
            salary_rule_list_leyend =   list(map(lambda x: x.code+' - '+x.name, self.env['hr.payslip.line'].search(domain_rule).mapped('salary_rule_id')))
            perception_total = 0
            deduction_total = 0
            total_general = 0
            settlement_total = 0
            for settlement in settlement_ids:
                salary_rule_employee={}
                perception = sum(self.env['hr.payslip.line'].search([('category_id.code','in',['GROSS']),('slip_id','=',settlement.id)]).mapped('total'))
                deduction = sum(self.env['hr.payslip.line'].search([('category_id.code','in',['DEDT']),('slip_id','=',settlement.id)]).mapped('total'))
                total = sum(self.env['hr.payslip.line'].search([('category_id.code','in',['NET']),('slip_id','=',settlement.id)]).mapped('total'))
                perception_total += perception
                total_general += total
                deduction_total += deduction
                for code in salary_rule_list:
                     amount = sum(self.env['hr.payslip.line'].search([('salary_rule_id.code','=',code),('total','>',0),('slip_id','=',settlement.id)]).mapped('total'))
                     salary_rule_employee[code] = amount
                     if code in amount_total:
                         amount_total[code] = float(amount_total[code])+round(amount,2)
                     else:
                         amount_total[code] = round(amount,2)
                per_employee[settlement.employee_id.id]={
                                          'complete_name':settlement.employee_id.complete_name,
                                          'code':settlement.employee_id.enrollment,
                                          'low_date':settlement.date_end,
                                          'settlemen_date':settlement.settlemen_date,
                                          'perception':round(perception,2),
                                          'deduction':round(deduction,2),
                                          'total':round(total,2),
                                          'settlement_total':round(0,2),
                                          'reason_liquidation':dict(settlement._fields['reason_liquidation']._description_selection(self.env)).get(settlement.reason_liquidation),
                                          'salary_rule_employee':salary_rule_employee,
                                          }
            data['per_employee'] = per_employee
            data['salary_rule_list'] = salary_rule_list
            data['salary_rule_list_leyend'] = salary_rule_list_leyend
            data['amount_total'] = amount_total
            data['type'] = '2'
            data['perception_total'] = round(perception_total,2)
            data['deduction_total'] = round(deduction_total,2)
            data['total_general'] = round(total_general,2)
            data['settlement_total'] = round(settlement_total,2)
        else:
            rules_amount_dict = {}
            settlement_dict = {}
            domain_rule = [('salary_rule_id.print_to_excel','=',True),
                        ('slip_id.settlemen_date', '>=', self.date_from),
                        ('slip_id.settlemen_date', '<=', self.date_to),
                        ('slip_id.group_id', '<=', self.group_id.id),
                        ('slip_id.struct_id.settlement','=',True),
                        ('slip_id.state','in',['done']),
                        ]
            if self.salary_rule_ids:
                domain_rule.append(('salary_rule_id','in',self.salary_rule_ids.ids))
            if self.employee_ids:
                domain_rule.append(('slip_id.employee_id','in',self.employee_ids.ids))
            salary_rule_list =   list(map(lambda x: x.code, self.env['hr.payslip.line'].search(domain_rule).mapped('salary_rule_id')))
            if not salary_rule_list:
                raise UserError(_('There are no settlements for the requested search..'))
            settlement_ids = self.env['hr.payslip.line'].search(domain_rule).mapped('slip_id')
            for code in salary_rule_list:
                rule = self.env['hr.payslip.line'].search([('salary_rule_id.code','=',code)]+domain_rule)
                rules_amount_dict[code]={
                                        'amount':round(sum(rule.mapped('total')),2),
                                        'code':code,
                                        'name':rule[0].name,
                                        }
            for settlement in settlement_ids:
                settlement_dict[settlement.id]={
                                        'settlement':settlement.code_payslip+str(settlement.number),
                                        'employee':settlement.employee_id.complete_name,
                                        'settlemen_date':settlement.settlemen_date,
                                        'contract':settlement.contract_id.name,
                                        }
            data['type'] = '1'
            data['rules_amount_dict'] = rules_amount_dict
            data['settlement_dict'] = settlement_dict
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        data['group_id'] = self.group_id.name
        return data

    @api.multi
    def report_print(self):
        data = self.get_report_data()
        return self.env.ref('payroll_mexico.report_settlement_low').report_action([], data=data)
    
    @api.multi
    def report_print_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        num_format = self.env.user.company_id.currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True, 'border': 1, 'top': 1, 'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCFF', 'font_color':'#3341BE', 'font_name':'MS Sans Serif'})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format, 'bold': True, 'border': 1, 'top': 1, 'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCFF', 'font_color':'#3341BE', 'font_name':'MS Sans Serif'})
        formula_format = workbook.add_format({'num_format': num_format, 'bold': True, 'border': 1, 'top': 1, 'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCFF', 'font_name':'MS Sans Serif'})
        c_middle = workbook.add_format({'border': 1, 'bold': True, 'top': 1, 'num_format': num_format})
        report_format2 = workbook.add_format({'border': 1, 'bold': True, 'font_size': 8, 'fg_color': '#CCCCFF','font_color':'#3341BE', 'font_name':'MS Sans Serif', 'align': 'center'})
        report_format = workbook.add_format({'border': 1, 'bold': True, 'font_size': 8, 'fg_color': '#CCCCFF','font_color':'#3341BE', 'font_name':'MS Sans Serif'})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format
        print_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), fields.Datetime.now()).strftime(('%s %s') % (date_format, time_format)),
        
        def _get_data_float(data):
            if data is None or not data:
                return 0.0
            else:
                return company_ids[0].currency_id.round(data) + 0.0
        
        def get_date_format(date):
            if date:
                # date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
                date = date.strftime(date_format)
            return date
        
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        date_start = self.date_from.strftime("%d/%b/%Y").title()
        date_end = self.date_to.strftime("%d/%b/%Y").title()
        f_name = '%s - %s al %s' %(self.group_id.name, date_start, date_end)
        sheet_name = self.group_id.name
        sheet = workbook.add_worksheet(sheet_name.upper())
        
        def _header_sheet(sheet):
            sheet.merge_range('A1:D1','', report_format)
            sheet.merge_range('A2:D2','', report_format)
            sheet.merge_range('A3:D3','', report_format)
            sheet.merge_range('A4:D4','', report_format)
            sheet.write(0, 0, _('FINIQUITOS Y BAJAS'), report_format)
            sheet.write(1, 0, _('Período: %s al %s') %(get_date_format(self.date_from), get_date_format(self.date_to)), report_format)
            sheet.write(2, 0, _('Grupo/Empresa: %s') %(self.group_id.name), report_format)
            sheet.write(3, 0, _('Fecha y hora de la generación del Reporte: %s') % print_time, report_format)
        _header_sheet(sheet)
        
        data = self.get_report_data()
        if not data:
            raise UserError(_('There are no settlements for the requested search..'))
        print (data)
        
        def _insert_table_consolidated():
            main_col_count = 0
            row_count = 5
            sheet.set_row(row_count, 40, )
            sheet.write(row_count, main_col_count, 'N°', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Clave', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Nombre\nde la\nRegla', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Monto', header_format)
            main_col_count += 1
        
            row_count += 1
            
            col_count = 0
            count = 0
            for rule in data['rules_amount_dict']:
                count += 1
                sheet.write(row_count, col_count, count, report_format2)
                col_count += 1
                sheet.write(row_count, col_count, data['rules_amount_dict'][rule]['code'], report_format2)
                col_count += 1
                sheet.write(row_count, col_count, data['rules_amount_dict'][rule]['name'], report_format2)
                col_count += 1
                sheet.write(row_count, col_count, data['rules_amount_dict'][rule]['amount'], currency_format)
                col_count = 0
                row_count += 1
            row_count += 1
            start_range = xl_rowcol_to_cell(row_count, 0)
            end_range = xl_rowcol_to_cell(row_count, 4)
            merge_range = formula = "{:s}:{:s}".format(start_range, end_range)
            sheet.merge_range(merge_range,'Finiquitos/Liquidación tomados en cuenta para el calculo del consolidado.', report_format)
            row_count += 1
            
            # Second Table head
            main_col_count = 0
            sheet.set_row(row_count, 40, )
            sheet.write(row_count, main_col_count, 'N°', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Finiquito/Liquidación', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Nombre\ndel\nEmpleado', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Fecha de\nFiniquito/Liquidación', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Contrato', header_format)
            row_count += 1
            
            count2 = 0
            col_count2 = 0
            for settlement in data['settlement_dict']:
                count2 += 1
                sheet.write(row_count, col_count2, count2, report_format2)
                col_count2 += 1
                sheet.write(row_count, col_count2, data['settlement_dict'][settlement]['settlement'], report_format2)
                col_count2 += 1
                sheet.write(row_count, col_count2, data['settlement_dict'][settlement]['employee'], report_format2)
                col_count2 += 1
                settlemen_date = get_date_format(data['settlement_dict'][settlement]['settlemen_date'])
                sheet.write(row_count, col_count2, settlemen_date, report_format2)
                col_count2 += 1
                sheet.write(row_count, col_count2, data['settlement_dict'][settlement]['contract'], report_format2)
                col_count2 = 0
                row_count += 1
            row_count += 1
        
        
        if data['type'] == '1':
            _insert_table_consolidated()
            
        #Excel Settlement Groub By Employee
        def _head_employee(list_head):
            header = {}
            for h in list_head:
                code, name = h.split('-')
                header[code.strip()] = name.strip()
            return header
            
        def _head_employee2(list_head):
            header = []
            for h in list_head:
                code, name = h.split('-')
                header.append(name.strip())
            return header
            
        def _insert_table_employee(header_rules):
            main_col_count = 0
            row_count = 5
            sheet.set_row(row_count, 40, )
            sheet.write(row_count, main_col_count, 'N°', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Clave', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Nombre\ndel\nEmpleado', header_format)
            sheet.set_column(row_count, main_col_count, 60)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Fecha\nde\nBaja', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Fecha de\nFiniquito/Liquidación', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Percepciones', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Deducciones', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Total', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Finiquito\nTotal', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Motivo', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            for code in header_rules:
                col_name = header_rules[code].replace(' ', '\n')
                sheet.write(row_count, main_col_count, col_name, header_format)
                sheet.set_column(row_count, main_col_count, 20)
                main_col_count += 1
            
            row_count += 1
            
            col_count = 0
            count = 0
            for employee in data['per_employee']:
                count += 1
                sheet.write(row_count, col_count, count, report_format2)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['code'], report_format2)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['complete_name'], report_format2)
                col_count += 1
                low_date = get_date_format(data['per_employee'][employee]['low_date'])
                sheet.write(row_count, col_count, low_date, report_format2)
                col_count += 1
                settlemen_date = get_date_format(data['per_employee'][employee]['settlemen_date'])
                sheet.write(row_count, col_count, settlemen_date, report_format2)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['perception'], currency_format)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['deduction'], currency_format)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['total'], currency_format)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['settlement_total'], currency_format)
                col_count += 1
                sheet.write(row_count, col_count, data['per_employee'][employee]['reason_liquidation'], report_format2)
                col_count += 1
                
                salary_rule_employee = data['per_employee'][employee]['salary_rule_employee']
                for rule in salary_rule_employee:
                    sheet.write(row_count, col_count, salary_rule_employee[rule], currency_format)
                    start_range = xl_rowcol_to_cell(6, col_count)
                    end_range = xl_rowcol_to_cell(len(data['per_employee']) + 6, col_count)
                    fila_formula = xl_rowcol_to_cell(len(data['per_employee']) + 6 +1, col_count)
                    formula = "=SUM({:s}:{:s})".format(start_range, end_range)
                    sheet.write_formula(fila_formula, formula, formula_format, True)
                    col_count += 1
                    
                col_count = 0
                row_count += 1
            row_count += 1
            
        if data['type'] == '2':
            head_rules = _head_employee(data['salary_rule_list_leyend'])
            _insert_table_employee(head_rules)
        
        workbook.close()
        xlsx_data = output.getvalue()
        export_id = self.env['hr.payslip.run.export.excel'].create({ 'excel_file': base64.encodestring(xlsx_data),'file_name': f_name + '.xlsx'})
        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'hr.payslip.run.export.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    
