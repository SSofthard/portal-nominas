# -*- coding: utf-8 -*-

#from cStringIO import StringIO
import io
import time
import datetime
import xlwt
import base64
import xlsxwriter
import itertools

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

    print_to_excel = fields.Boolean(string='Imprimir en excel?', default=False, 
        help='Si está marcado indica que se se imprimiran los detalles en los reportes excel.')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def prepare_header(self):
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
        rule_ids = self.estructure_id.rule_ids.filtered(lambda r: r.print_to_excel)
        for rule in rule_ids:
            header.append({
                'sequence': rule.sequence,
                'name': rule.name.replace(' ', '\n'), 
                'larg': 10,
                'code': rule.code,
                'col': {'total_function': 'sum', 'total_row': 1},})
        header_sort = sorted(header, key=lambda k: k['sequence'])
        return header_sort

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
        date_start = '%s/%s/%s' %(self.date_start.strftime("%d"), self.date_start.strftime("%b").title(), self.date_start.strftime("%Y"))
        date_end = '%s/%s/%s' %(self.date_end.strftime("%d"), self.date_end.strftime("%b").title(), self.date_end.strftime("%Y"))
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
            sheet.write(0, 0, _('Nombre de la Empresa: %s') % company.name, report_format)
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
                    sheet.write(10, j, h['name'])
                    sheet.set_column(10, j, h['larg'])
                    row = 10
                    row += 1
                    start_row = row
                    n = 0
                    for i, line in enumerate(all_lines):
                        i += row
                        sheet.write(i, 0, line.get('enrollment', ''), report_format2) #Clave
                        sheet.write(i, 1, line.get('employee_name', ''), report_format) #Nombre del trabajador
                        sheet.write(i, 2, line.get('nss', '') or '-', report_format2) # NSS
                        sheet.write(i, 3, line.get('rfc', '') or '-', report_format2) #RFC
                        sheet.write(i, 4, line.get('curp', '') or '-', report_format2) #CURP
                        sheet.write(i, 5, get_date_format(line.get('discharge_date', '') or '-'), report_format2) #Fecha de Alta
                        sheet.write(i, 6, line.get('department', '') or '-', report_format2) #Departamento
                        sheet.write(i, 7, line.get('salary_type', '') or '-', report_format2) #Tipo Salario
                        col = 7
                        col += 1
                        for n, rule in enumerate(line['lines']):
                            n += col
                            if h.get('sequence', '') == rule.get('sequence', ''):
                                sheet.write(i, n, _get_data_float(rule.get('total', '')) or '-', currency_format) # Montos
                            start_range = xl_rowcol_to_cell(11, n)
                            end_range = xl_rowcol_to_cell(len(all_lines) + 11, n)
                            fila_formula = xl_rowcol_to_cell(len(all_lines) + 11 +1, n)
                            formula = "=SUM({:s}:{:s})".format(start_range, end_range)
                            sheet.write_formula(fila_formula, formula, formula_format, True) 
                        col = n
                    row = i
                    
                    for j, h in enumerate(self.prepare_header()):
                        sheet.set_column(j, j, h['larg'])
                    
        sheet.set_row(10, 40, header_format)
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

    def get_line_for_report(self):
        payroll_data = {}
        employee_data = []
        rule_code = self.estructure_id.rule_ids.filtered(lambda r: r.print_to_excel)
        for payroll in self.slip_ids:
            line_data = []
            for rule in rule_code:
                line_calc = payroll.line_ids.filtered(lambda line: line.code == rule.code)
                if line_calc:
                    line_data.append({
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
        return employee_data
        
        
        
        
