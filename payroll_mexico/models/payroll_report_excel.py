# -*- coding: utf-8 -*-

#from cStringIO import StringIO
import io
import time
import datetime
import xlwt
import base64
import xlsxwriter
import itertools
import locale

from datetime import datetime, time, timedelta, date
from xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell

from operator import itemgetter
import operator

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


class HrPayslipLine(models.Model):
    _inherit = 'hr.salary.rule'

    generated = fields.Boolean(string='generated en excel?', default=False, 
        help='Si está marcado indica que se se imprimiran los detalles en los reportes excel.')
    print_to_excel = fields.Boolean(string='Imprimir en excel?', default=False, 
        help='Si está marcado indica que se se imprimiran los detalles en los reportes excel.')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def test_print_report(self):
        for slip in self:
            slip.slip_ids.print_payroll_receipt()
        
    def prepare_header(self):
        if self.contracting_regime == '02':
            header = [ 
                {'sequence': 0.1, 'name': 'Clave', 'larg': 10, 'col': {}},
                {'sequence': 0.2, 'name': 'Nombre del trabajador', 'larg': 40, 'sequence': 0.2, 'col': {}},
                {'sequence': 0.3, 'name': 'NSS', 'larg': 10, 'col': {}},
                {'sequence': 0.4, 'name': 'RFC', 'larg': 10, 'col': {}},
                {'sequence': 0.5, 'name': 'CURP', 'larg': 10, 'col': {}},
                {'sequence': 0.6, 'name': 'Fecha\nde\nAlta', 'larg': 15, 'col': {}},
                {'sequence': 0.7, 'name': 'Departamento', 'larg': 5, 'col': {}},
                {'sequence': 0.8, 'name': 'Tipo\nSalario', 'larg': 10, 'col': {}},
            ]
        else:
            header = [ 
                {'sequence': 0.1, 'name': 'Clave', 'larg': 10, 'col': {}},
                {'sequence': 0.2, 'name': 'Nombre del trabajador', 'larg': 40, 'sequence': 0.2, 'col': {}},
                {'sequence': 0.4, 'name': 'RFC', 'larg': 10, 'col': {}},
                {'sequence': 0.5, 'name': 'CURP', 'larg': 10, 'col': {}},
                {'sequence': 0.6, 'name': 'Fecha\nde\nAlta', 'larg': 15, 'col': {}},
                {'sequence': 0.8, 'name': 'Tipo\nSalario', 'larg': 10, 'col': {}},
            ]
        domain = [('slip_id.payslip_run_id','=', self.id), ('total','!=',0)]
        rule_ids = self.env['hr.payslip.line'].search(domain).filtered(lambda r: r.salary_rule_id.print_to_excel == True).mapped('salary_rule_id')
        for rule in rule_ids:
            header.append({
                'sequence': rule.sequence,
                'name': rule.name.replace(' ', '\n'), 
                'larg': 15,
                'code': rule.code,
                'col': {'total_function': 'sum', 'total_row': 1},})
        header_sort = sorted(header, key=lambda k: k['sequence'])
        return header_sort

    @api.model
    def prepare_report_data(self):
        PayslipObj = self.env['hr.payslip'].sudo()
        domain = [
            ('payslip_run_id', '=', self.id),
        ]
        all_lines = {}
        result = {}
        header = {}
        payslips = PayslipObj.search(domain, order="date_from asc, id asc")
        
        for payslip in payslips:
            if payslip.employee_id not in all_lines:
                all_lines[payslip.employee_id] = {}
            if payslip.struct_id not in all_lines[payslip.employee_id]:
                all_lines[payslip.employee_id][payslip.struct_id] = []
            all_lines[payslip.employee_id][payslip.struct_id].append(
                payslip.line_ids.filtered(
                    lambda i: i.code == 'T001'
                ).mapped('total')[0]
            )
            if payslip.struct_id not in header:
                header[payslip.struct_id] = payslip.line_ids.filtered(
                    lambda i: i.slip_id.struct_id.id == payslip.struct_id.id and i.total > 0 and i.salary_rule_id.print_to_excel == True
                ).sorted(key=lambda l: l.sequence).mapped('name')
            if payslip.company_id not in result:
                result[payslip.company_id] = {}
            if payslip.struct_id not in result[payslip.company_id]:
                result[payslip.company_id][payslip.struct_id] = []
            lines = [payslip.line_ids.filtered(
                lambda i: i.slip_id.struct_id.id == payslip.struct_id.id and i.total > 0 and i.salary_rule_id.print_to_excel == True
            ).sorted(key=lambda l: l.sequence)]
            result[payslip.company_id][payslip.struct_id].append((payslip, lines))
        return {'result': result, 'header':header, 'all_lines': all_lines}

    def get_line_for_report(self):
        payroll_data = {}
        employee_data = []
        domain = [('slip_id.payslip_run_id','=', self.id), ('total','!=',0)]
        rule_code = self.env['hr.payslip.line'].search(domain).filtered(lambda r: r.salary_rule_id.print_to_excel == True).mapped('salary_rule_id')
        # ~ rule_code = self.estructure_id.rule_ids.filtered(lambda r: r.print_to_excel)
        for payroll in self.slip_ids:
            line_data = []
            for rule in rule_code:
                
                line_calc = payroll.line_ids.filtered(lambda line: line.code == rule.code and line.total != 0 and line.salary_rule_id.print_to_excel == True)
                if line_calc:
                    line_data.append({
                        'name': line_calc.name,
                        'code': line_calc.code,
                        'sequence': line_calc.sequence,
                        'total': line_calc.total,
                    })
                else:
                    line_data.append({
                        'code': rule.code,
                        'sequence': rule.sequence,
                        'total': 0,
                    })
            line_data_sort = sorted(line_data, key=lambda k: k['sequence'])
            if self.contracting_regime == '02':
                employee_data.append({
                    'enrollment': payroll.employee_id.enrollment,
                    'employee_name': payroll.employee_id.name_get()[0][1],
                    'nss': payroll.employee_id.ssnid,
                    'rfc': payroll.employee_id.rfc,
                    'curp': payroll.employee_id.curp,
                    'discharge_date': payroll.contract_id.date_start,
                    'department': payroll.employee_id.department_id.name,
                    'salary_type': dict(payroll.employee_id._fields['salary_type']._description_selection(self.env)).get(payroll.employee_id.salary_type),
                    'wage': payroll.contract_id.wage,
                    'lines': line_data_sort,
                    
                })
            else:
                employee_data.append({
                    'enrollment': payroll.employee_id.enrollment,
                    'employee_name': payroll.employee_id.name_get()[0][1],
                    'rfc': payroll.employee_id.rfc,
                    'curp': payroll.employee_id.curp,
                    'discharge_date': payroll.contract_id.date_start,
                    'salary_type': dict(payroll.employee_id._fields['salary_type']._description_selection(self.env)).get(payroll.employee_id.salary_type),
                    'wage': payroll.contract_id.wage,
                    'lines': line_data_sort,
                    
                })
        return employee_data

    @api.multi
    def action_print_report_group_by(self):
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
        
        payroll_dic = {} 
        company_ids = self.mapped('slip_ids').mapped('company_id')
        company_names =  ', '.join(company_ids.mapped('name'))
        company_rfc =  ', '.join(company_ids.mapped('rfc'))
        
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        date_start = self.date_start.strftime("%d/%b/%Y").title()
        date_end = self.date_end.strftime("%d/%b/%Y").title()
        f_name = 'Periodo de Pago: Del %s al %s' %(date_start, date_end)
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
        
        results = self.prepare_report_data()
        result = results['result']
        header = results['header']
        all_lines = results['all_lines']
        
        # All lines Consolidated Report
        sheet_all_name = _('Consolidated %s') % self.name
        sheet_all = workbook.add_worksheet(sheet_all_name.upper())
        row = 6
        col = 0
        row += 1
        start_row = row
            
        def _header_sheet_all(sheet_all):
            sheet_all.merge_range('A1:B1','', report_format)
            sheet_all.merge_range('A2:B2','', report_format)
            sheet_all.merge_range('A3:B3','', report_format)
            sheet_all.merge_range('A4:B4','', report_format)
            sheet_all.merge_range('A5:B5','', report_format)
            sheet_all.merge_range('A6:B6','', report_format)
            sheet_all.merge_range('A7:B7','', report_format)
            sheet_all.merge_range('A8:B8','', report_format)
            sheet_all.merge_range('A9:B9','', report_format)
            sheet_all.merge_range('A10:B10','', report_format)
            sheet_all.write(0, 0, _('Nombre de la Empresa(s): %s') % company_names, report_format)
            sheet_all.write(1, 0, _('Fecha de emisión del reporte: %s') % get_date_format(date.today()), report_format)
            sheet_all.write(2, 0, _('RFC: %s') % company_rfc, report_format)
            sheet_all.write(3, 0, _('Número de la Nómina: %s') % self.payroll_of_month, report_format)
            sheet_all.write(4, 0, _('Título de Reporte: Reporte de la nómina'), report_format)
            sheet_all.write(5, 0, _('Clasificación: ??????????'), report_format)
            sheet_all.write(6, 0, _('Rango de Departamentos: ') , report_format)
            sheet_all.write(7, 0, _('%s: ') % f_name, report_format)
            sheet_all.write(8, 0, _('Fecha y hora de la generación del Reporte: %s') % print_time, report_format)
        _header_sheet_all(sheet_all)
        
        struct_dic = {}
        def _insert_table_all(estructures_id, all_lines):
            main_col_count = 0
            row_count = 11
            sheet_all.set_row(row_count, 40, )
            sheet_all.write(row_count, main_col_count, 'CLAVE', header_format)
            sheet_all.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet_all.write(row_count, main_col_count, 'NOMBRE\nDEL\nTRABAJADOR', header_format)
            main_col_count += 1
            
            for struct in estructures_id:
                col_name = struct.name.replace(' ', '\n')
                sheet_all.write(row_count, main_col_count, col_name, header_format)
                sheet_all.set_column(row_count, main_col_count, 15)
                main_col_count += 1
            
            sheet_all.write(row_count, main_col_count, 'TOTAL', header_format)
            main_col_count += 1
            
            row_count += 1
            for employee in all_lines:
                col_count = 0
                sheet_all.write(row_count, col_count, employee.enrollment, report_format2) #Clave
                col_count += 1
                sheet_all.write(row_count, col_count, employee.complete_name, report_format2) #Nombre del trabajador
                col_count += 1
                
                line_drl = {}
                for line in all_lines[employee]:
                    line_drl[line.name] = [sum(all_lines[employee][line])]
                    if 'total' not in line_drl:
                        line_drl['total'] = []
                    line_drl['total'].append(line_drl[line.name][0])
                estructures = estructures_id.mapped('name')
                for name in estructures + ['total']:
                    if name not in line_drl:
                        sheet_all.write(
                            row_count, col_count, '-', currency_format
                        )
                    else:
                        sheet_all.write(
                            row_count, col_count, _get_data_float(sum(line_drl[name])), currency_format
                        )
                    start_range = xl_rowcol_to_cell(11, col_count)
                    end_range = xl_rowcol_to_cell(len(all_lines) + 11, col_count)
                    fila_formula = xl_rowcol_to_cell(len(all_lines) + 11 +2, col_count)
                    formula = "=SUM({:s}:{:s})".format(start_range, end_range)
                    sheet_all.write_formula(fila_formula, formula, formula_format, True)
                    col_count += 1
                row_count += 1
        _insert_table_all(self.estructures_id, all_lines)
        
        # Group by Company and Struture Salary
        def _header_sheet(sheet, company, struct_id):
            sheet.merge_range('A1:B1','', report_format)
            sheet.merge_range('A2:B2','', report_format)
            sheet.merge_range('A3:B3','', report_format)
            sheet.merge_range('A4:B4','', report_format)
            sheet.merge_range('A5:B5','', report_format)
            sheet.merge_range('A6:B6','', report_format)
            sheet.merge_range('A7:B7','', report_format)
            sheet.merge_range('A8:B8','', report_format)
            sheet.merge_range('A9:B9','', report_format)
            sheet.merge_range('A10:B10','', report_format)
            sheet.write(0, 0, _('Nombre de la Empresa: %s') % company.name, report_format)
            sheet.write(1, 0, _('Fecha de emisión del reporte: %s') % get_date_format(date.today()), report_format)
            sheet.write(2, 0, _('RFC: %s') % company.rfc, report_format)
            sheet.write(3, 0, _('Número de la Nómina: %s') % self.payroll_of_month, report_format)
            sheet.write(4, 0, _('Título de Reporte: Reporte de la nómina %s ') %struct_id.name, report_format)
            sheet.write(5, 0, _('Clasificación: ??????????'), report_format)
            sheet.write(6, 0, _('Rango de Departamentos: ') , report_format)
            sheet.write(7, 0, _('%s: ') % f_name, report_format)
            sheet.write(8, 0, _('Fecha y hora de la generación del Reporte: %s') % print_time, report_format)

        def _header_table(header, struct_dic):
            main_col_count = 0
            row_count = 11
            sheet.set_row(row_count, 40, )
            sheet.write(row_count, main_col_count, 'Clave', header_format)
            sheet.set_column(row_count, main_col_count, 20)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Nombre del trabajador', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'NSS', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'RFC', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'CURP', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Fecha\nde\nAlta', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Departamento', header_format)
            main_col_count += 1
            sheet.write(row_count, main_col_count, 'Tipo\nSalario', header_format)
            main_col_count += 1
            
            for head in header:
                col_name = head.replace(' ', '\n')
                sheet.write(row_count, main_col_count, col_name, header_format)
                sheet.set_column(row_count, main_col_count, 15)
                main_col_count += 1

            row_count += 1
            for payslip in struct_dic:
                col_count = 0
                name_list = payslip[1][0].mapped('name')
                sheet.write(row_count, col_count, payslip[0].employee_id.enrollment, report_format2) #Clave
                col_count += 1
                sheet.write(row_count, col_count, payslip[0].employee_id.complete_name, report_format2) #Nombre del trabajador
                col_count += 1
                sheet.write(row_count, col_count, payslip[0].employee_id.ssnid, report_format2) #NSS
                col_count += 1
                sheet.write(row_count, col_count, payslip[0].employee_id.rfc, report_format2) #RFC
                col_count += 1
                sheet.write(row_count, col_count, payslip[0].employee_id.curp, report_format2) #CURP
                col_count += 1
                sheet.write(row_count, col_count, get_date_format(payslip[0].contract_id.date_start), report_format2) #Fecha de Alta
                col_count += 1
                sheet.write(row_count, col_count, payslip[0].employee_id.department_id.name, report_format2) #Departamento
                col_count += 1
                salary_type = dict(payslip[0].employee_id._fields['salary_type']._description_selection(self.env)).get(payslip[0].employee_id.salary_type).upper()
                sheet.write(row_count, col_count, salary_type, report_format2) #Tipo Salario
                col_count += 1
                
                list_drl = {}
                for line in payslip[1][0]:
                    list_drl[line.name] = line.total
                
                for name in header:
                    if name not in list_drl:
                        sheet.write(
                            row_count, col_count, '-', currency_format
                        )
                    else:
                        sheet.write(
                            row_count, col_count, _get_data_float(list_drl[name]), currency_format
                        )
                    start_range = xl_rowcol_to_cell(11, col_count)
                    end_range = xl_rowcol_to_cell(len(struct_dic) + 11, col_count)
                    fila_formula = xl_rowcol_to_cell(len(struct_dic) + 11 +2, col_count)
                    formula = "=SUM({:s}:{:s})".format(start_range, end_range)
                    sheet.write_formula(fila_formula, formula, formula_format, True)
                    col_count += 1
                row_count += 1
        
        for company in result:
            for struct in result[company]:
                sheet_name = '%s - %s' % (struct.code, company.name)
                sheet = workbook.add_worksheet(sheet_name)
                _header_sheet(sheet, company, struct)
                _header_table(header[struct], result[company][struct])
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

    @api.multi
    def action_print_report(self):
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
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format
        
        payroll_dic = {} 
        company = self.mapped('slip_ids').mapped('company_id')
        payroll_dic['company_name'] = company.name
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        date_start = self.date_start.strftime("%d/%b/%Y").title()
        date_end = self.date_end.strftime("%d/%b/%Y").title()
        f_name = 'Periodo de Pago: Del %s al %s' %(date_start, date_end)
        print_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), fields.Datetime.now()).strftime(('%s %s') % (date_format, time_format)),
        sheet = workbook.add_worksheet(self.name)
        
        row = 6
        col = 0
        row += 1
        start_row = row
        def _get_data_float(data):
            if data is None or not data:
                return 0.0
            else:
                return company.currency_id.round(data) + 0.0

        def get_date_format(date):
            if date:
                # date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
                date = date.strftime(date_format)
            return date
            
        def _header_sheet(sheet):
            sheet.merge_range('A1:B1','', report_format)
            sheet.merge_range('A2:B2','', report_format)
            sheet.merge_range('A3:B3','', report_format)
            sheet.merge_range('A4:B4','', report_format)
            sheet.merge_range('A5:B5','', report_format)
            sheet.merge_range('A6:B6','', report_format)
            sheet.merge_range('A7:B7','', report_format)
            sheet.merge_range('A8:B8','', report_format)
            sheet.merge_range('A9:B9','', report_format)
            sheet.merge_range('A10:B10','', report_format)
            sheet.write(0, 0, _('Nombre de la Empresa: %s') % company, report_format)
            sheet.write(1, 0, _('Fecha de emisión del reporte: %s') % get_date_format(date.today()), report_format)
            sheet.write(2, 0, _('RFC: %s') % company.rfc, report_format)
            sheet.write(3, 0, _('Número de la Nómina: %s') % self.payroll_of_month, report_format)
            sheet.write(4, 0, _('Título de Reporte: Reporte de la nómina'), report_format)
            sheet.write(5, 0, _('Clasificación: ??????????'), report_format)
            sheet.write(6, 0, _('Rango de Departamentos: ') , report_format)
            sheet.write(7, 0, _('%s: ') % f_name, report_format)
            sheet.write(8, 0, _('Fecha y hora de la generación del Reporte: %s') % print_time, report_format)
        
        if f_name:
            _header_sheet(sheet)
            
            all_lines = self.get_line_for_report()
            if all_lines:
                for j, h in enumerate(self.prepare_header()):
                    sheet.write(10, j, h['name'], header_format)
                    sheet.set_column(10, j, h['larg'])
                    row = 10
                    row += 1
                    start_row = row
                    n = 0
                    if self.contracting_regime == '02':
                        for i, line in enumerate(all_lines):
                            i += row
                            sheet.write(i, 0, line.get('enrollment', ''), report_format2) #Clave
                            sheet.write(i, 1, line.get('employee_name', ''), report_format) #Nombre del trabajador
                            sheet.write(i, 2, line.get('nss', '') , report_format2) # NSS
                            sheet.write(i, 3, line.get('rfc', '') , report_format2) #RFC
                            sheet.write(i, 4, line.get('curp', '') , report_format2) #CURP
                            sheet.write(i, 5, get_date_format(line.get('discharge_date', '') ), report_format2) #Fecha de Alta
                            sheet.write(i, 6, line.get('department', '') , report_format2) #Departamento
                            sheet.write(i, 7, line.get('salary_type', '') , report_format2) #Tipo Salario
                            col = 7
                            col += 1
                            for n, rule in enumerate(line['lines']):
                                n += col
                                if h.get('sequence', '') == rule.get('sequence', ''):
                                    sheet.write(i, n, _get_data_float(rule.get('total', '')) , currency_format) # Montos
                                start_range = xl_rowcol_to_cell(11, n)
                                end_range = xl_rowcol_to_cell(len(all_lines) + 11, n)
                                fila_formula = xl_rowcol_to_cell(len(all_lines) + 11 +1, n)
                                formula = "=SUM({:s}:{:s})".format(start_range, end_range)
                                sheet.write_formula(fila_formula, formula, formula_format, True) 
                            col = n
                        row = i
                    else:
                        for i, line in enumerate(all_lines):
                            i += row
                            sheet.write(i, 0, line.get('enrollment', ''), report_format2) #Clave
                            sheet.write(i, 1, line.get('employee_name', ''), report_format) #Nombre del trabajador
                            sheet.write(i, 2, line.get('rfc', '') , report_format2) #RFC
                            sheet.write(i, 3, line.get('curp', '') , report_format2) #CURP
                            sheet.write(i, 4, get_date_format(line.get('discharge_date', '') ), report_format2) #Fecha de Alta
                            sheet.write(i, 5, line.get('salary_type', '') , report_format2) #Tipo Salario
                            col = 5
                            col += 1
                            for n, rule in enumerate(line['lines']):
                                n += col
                                if h.get('sequence', '') == rule.get('sequence', ''):
                                    sheet.write(i, n, _get_data_float(rule.get('total', '')) , currency_format) # Montos
                                start_range = xl_rowcol_to_cell(11, n)
                                end_range = xl_rowcol_to_cell(len(all_lines) + 11, n)
                                fila_formula = xl_rowcol_to_cell(len(all_lines) + 11 +1, n)
                                formula = "=SUM({:s}:{:s})".format(start_range, end_range)
                                sheet.write_formula(fila_formula, formula, formula_format, True) 
                            col = n
                        row = i
                    
                    for j, h in enumerate(self.prepare_header()):
                        sheet.set_column(j, j, h['larg'])
                    
        sheet.set_row(10, 40, )
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

