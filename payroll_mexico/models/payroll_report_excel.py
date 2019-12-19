# -*- coding: utf-8 -*-

#from cStringIO import StringIO
import io
import time
import datetime
import xlwt

from xlsxwriter.workbook import Workbook
from xlwt import easyxf
import base64
import xlsxwriter
import itertools
from operator import itemgetter
import operator

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


head = [ 

        {'name': 'Clave', 'larg': 10, 'col': {}},
        {'name': 'Nombre del trabajador', 'larg': 40, 'col': {}},
        {'name': 'NSS', 'larg': 20, 'col': {}},
        {'name': 'RFC', 'larg': 20, 'col': {}},
        {'name': 'CURP', 'larg': 20, 'col': {}},
        {'name': 'Fecha de Alta', 'larg': 15, 'col': {}},
        {'name': 'Departamento', 'larg': 5, 'col': {}},
        {'name': 'Tipo\nSalario', 'larg': 10, 'col': {}},
        {'name': 'Salario\nDiario', 'larg': 10, 'col': {}},
        {'name': 'SDI', 'larg': 10, 'col': {}},
        {'name': 'Días\ntrabajados', 'larg': 5, 'col': {}},
        {'name': 'Faltas', 'larg': 5, 'col': {}},
        {'name': 'Sueldo', 'larg': 10, 'col': {}},
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
        # ~ if not os.path.exists('/tmp/file.xlsx'):
            # ~ with open('/tmp/file.xlsx', 'w'): pass
        # ~ file_data = '/tmp/file.xlsx'
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        
        
        
        num_format = self.env.user.company_id.currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True, 'top': 1, 'font_size': 8, 'align': 'vcenter', })
        middle = workbook.add_format({'bold': True, 'top': 1})
        center = workbook.add_format({'align': 'center'})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 8})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        
        payroll_dic = {} 
        company = self.mapped('slip_ids').mapped('company_id')
        payroll_dic['company_name'] = company.name
        date_start = '%s/%s/%s' %(self.date_start.strftime("%d"), self.date_start.strftime("%b").title(), self.date_start.strftime("%Y"))
        date_end = '%s/%s/%s' %(self.date_end.strftime("%d"), self.date_end.strftime("%b").title(), self.date_end.strftime("%Y"))
        f_name = 'Periodo de Pago: Del %s al %s' %(date_start, date_end)
        
        worksheet = workbook.add_worksheet(f_name)
        worksheet.merge_range(1, 0, 1, 1, company.name or '',header_format)
        print (worksheet)
        print (worksheet)
        print (worksheet)
        print (worksheet)
        row = 5
        col = 0
        row += 1
        start_row = row
        
        # ~ for j, h in enumerate(head):
            # ~ sheet.set_column(j, j, h['larg'])
        # ~ table = []
        # ~ for h in head:
            # ~ col = {}
            # ~ col['header'] = h['name']
            # ~ col.update(h['col'])
            # ~ table.append(col)
        # ~ sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                        # ~ {'total_row': 1,
                         # ~ 'columns': table,
                         # ~ 'style': 'Table Style Light 9',
                        # ~ })
        # ~ sheet.set_row(0, 40, header_format)
        # ~ sheet.set_row(0, 40, center)
        # ~ workbook.close()
        # ~ with open(file_data, "rb") as file:
            # ~ file_base64 = base64.b64encode(file.read())
        # ~ export_id = self.env['hr.payslip.run.export.excel'].create({ 'excel_file': file_base64,'file_name': f_name})
        workbook.close()
        xlsx_data = output.getvalue()
        export_id = self.env['dev.export.file.excel'].create({ 'excel_file': base64.encodestring(xlsx_data),'file_name': f_name})
        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'hr.payslip.run.export.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        
