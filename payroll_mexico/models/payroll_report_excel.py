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
from xlwt import easyxf

from operator import itemgetter
import operator

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime


head = [ 

        {'name': 'Clave', 'larg': 10, 'col': {}},
        {'name': 'Nombre del trabajador', 'larg': 40, 'col': {}},
        {'name': 'NSS', 'larg': 10, 'col': {}},
        {'name': 'RFC', 'larg': 10, 'col': {}},
        {'name': 'CURP', 'larg': 10, 'col': {}},
        {'name': 'Fecha de Alta', 'larg': 15, 'col': {}},
        {'name': 'Departamento', 'larg': 5, 'col': {}},
        {'name': 'Tipo\nSalario', 'larg': 10, 'col': {}},
        {'name': 'Salario\nDiario', 'larg': 10, 'col': {}},
        {'name': 'SDI', 'larg': 10, 'col': {}},
        {'name': 'Días\ntrabajados', 'larg': 5, 'col': {}},
        {'name': 'Faltas', 'larg': 5, 'col': {}},
        {'name': 'Sueldo', 'larg': 10, 'col': {}},
        {'name': 'SUELDO', 'larg': 8, 'col': {}},
        {'name': 'COMISIONES', 'larg': 10, 'col': {}},
        {'name': 'HORAS\nEXTRAS\nDOBLES', 'larg': 10, 'col': {}},
        {'name': 'AGUINALDO', 'larg': 10, 'col': {}},
        {'name': 'HORAS\nEXTRAS\nTRIPLES', 'larg': 10, 'col': {}},
        {'name': 'FONDO\nDE\nAHORRO\nPATRON*', 'larg': 10, 'col': {}},
        {'name': 'PRESTAMO\nDEL\nFONDO', 'larg': 10, 'col': {}},
        {'name': 'INTERESES\nDEL\nFONDO', 'larg': 10, 'col': {}},
        {'name': 'VACACIONES', 'larg': 10, 'col': {}},
        {'name': 'PRIMA\nVACACIONAL', 'larg': 10, 'col': {}},
        {'name': 'REPARTO\nDE\nUTILIDADES', 'larg': 10, 'col': {}},
        {'name': 'ALIMENTACION*', 'larg': 10, 'col': {}},
        {'name': 'HABITACION*', 'larg': 10, 'col': {}},
        {'name': 'DESPENSA*', 'larg': 10, 'col': {}},
        {'name': 'PREMIOS\nDE\nASISTENCIA', 'larg': 10, 'col': {}},
        {'name': 'PREMIOS\nDE\nPUNTUALIDAD', 'larg': 10, 'col': {}},
        {'name': 'PRIMA\nDOMINICAL', 'larg': 10, 'col': {}},
        {'name': 'SUBSIDIOS\nPOR\nINCAPACIDAD', 'larg': 10, 'col': {}},
        {'name': 'COMPENSACION', 'larg': 10, 'col': {}},
        {'name': 'INDEMNIZACION', 'larg': 10, 'col': {}},
        {'name': 'PRIMA\nDE\nANTIGUEDAD', 'larg': 10, 'col': {}},
        {'name': 'Total\nPercepciones', 'larg': 10, 'col': {}},
        {'name': 'Total\nGravable', 'larg': 10, 'col': {}},
        {'name': 'Total\nIMSS', 'larg': 10, 'col': {}},
        {'name': 'Total\nISR', 'larg': 10, 'col': {}},
        {'name': 'Subsidio\nEmpleo', 'larg': 10, 'col': {}},
        {'name': 'ISR', 'larg': 10, 'col': {}},
        {'name': 'IMSS', 'larg': 10, 'col': {}},
        {'name': 'ANTICIPO\nDE\nNOMINA', 'larg': 10, 'col': {}},
        {'name': 'PRESTAMO\nPERSONAL', 'larg': 10, 'col': {}},
        {'name': 'FONDO\nDE\nAHORRO', 'larg': 10, 'col': {}},
        {'name': 'ALIMENTACION', 'larg': 10, 'col': {}},
        {'name': 'HABITACION', 'larg': 10, 'col': {}},
        {'name': 'PENSION\nALIMENTICIA', 'larg': 10, 'col': {}},
        {'name': 'SAR\nVOLUNTARIO', 'larg': 10, 'col': {}},
        {'name': 'INFONAVIT\nVOLUNTARIO', 'larg': 10, 'col': {}},
        {'name': 'CREDITO\nFONACOT', 'larg': 10, 'col': {}},
        {'name': 'CREDITO\nINFONAVIT', 'larg': 10, 'col': {}},
        {'name': 'SUBSIDIO\nPARA\nEL\nEMPLEO', 'larg': 10, 'col': {}},
        {'name': 'IMPUESTO\nLOCAL', 'larg': 10, 'col': {}},
        {'name': 'Total\nDeducciones', 'larg': 10, 'col': {}},
        {'name': 'Total\nEfectivo', 'larg': 10, 'col': {}},
        {'name': 'Total\nen\nEspecie', 'larg': 10, 'col': {}},
        {'name': 'Neto\nPagado', 'larg': 10, 'col': {}},
    ]


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

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
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'bold': True, 'font_size': 8, 'fg_color': '#CCCCFF','font_color':'#3341BE', 'font_name':'MS Sans Serif'})
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
                return self.company_currency_id.round(data) + 0.0

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
            
            row = 10
            row += 1
            start_row = row
            for j, h in enumerate(head):
                sheet.set_column(j, j, h['larg'])
            table = []
            for h in head:
                col = {}
                col['header'] = h['name']
                col.update(h['col'])
                table.append(col)
            sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                            {'total_row': 1,
                             'columns': table,
                             'style': 'Table Style Light 9',
                            })
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
        payroll_dic = {}
        for payroll in self.slip_ids:
            for line in payroll.line_ids:
                print (line.code)
                print (line.name)
        
        print (stop)
        
        
        
        
