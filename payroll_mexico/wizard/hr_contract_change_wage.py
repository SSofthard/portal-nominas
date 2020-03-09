# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import time
import datetime
import calendar
import pytz
import dateutil
import xlsxwriter
import base64
import locale

from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from datetime import datetime
from xlrd import open_workbook
from dateutil.relativedelta import relativedelta


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo.tools.mimetypes import guess_mimetype
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, pycompat
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class HrContractChangeWageExport(models.TransientModel):
    _name = "hr.contract.change.wage.export"
    _description = "Contract Change Wage"

    group_id = fields.Many2one('hr.group', "Group", required=True)
    contracting_regime = fields.Selection([
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
    ], string='Contracting Regime', required=True,)

    def prepare_header(self):
        header = [
            {'name': 'MATRÍCULA EMPLEADO', 'larg': 14, 'col': {}},
            {'name': 'CURP', 'larg':18, 'col':{}},
            {'name': 'NOMBRE DEL EMPLEADO', 'larg': 40, 'col': {}},
            {'name': 'CLAVE DEL GRUPO', 'larg': 15, 'col': {}},
            {'name': 'CLAVE DEL CONTRATO', 'larg': 15, 'col': {}},
            {'name': 'MONTO DEL SUELDO', 'larg': 15, 'col': {}},
        ]
        return header

    def get_line_for_report(self):
        employee_data = []
        contracts = self.env['hr.contract'].search([
            ('group_id', '=', self.group_id.id),
            ('contracting_regime', '=', self.contracting_regime),
            ('state', '=', 'open'),
        ])
        if not contracts:
            raise UserError(
                _('No information was found with the data provided.'))
        for contract in contracts:
            employee_data.append({
                'enrollment':contract.employee_id.enrollment,
                'curp':contract.employee_id.curp,
                'employee_name':contract.employee_id.complete_name,
                'group':contract.group_id.code,
                'contract_code':contract.code,
                'wage':contract.wage,
            })
        return employee_data

    @api.multi
    def action_export_data(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        num_format = self.env.user.company_id.currency_id.excel_format
        bold = workbook.add_format({'bold':True})
        header_format = workbook.add_format(
            {'bold':True, 'border':1, 'top':1, 'font_size':8, 'align':'center',
             'valign':'vcenter', 'fg_color':'#CCCCFF', 'font_color':'#3341BE',
             'font_name':'MS Sans Serif'})
        middle = workbook.add_format({'bold':True, 'top':1})
        left = workbook.add_format({'left':1, 'top':1, 'bold':True})
        right = workbook.add_format({'right':1, 'top':1})
        top = workbook.add_format({'top':1})
        currency_format = workbook.add_format(
            {'num_format':num_format, 'bold':True, 'border':1, 'top':1,
             'font_size':8, 'align':'center', 'valign':'vcenter',
             'fg_color':'#CCCCFF', 'font_color':'#3341BE',
             'font_name':'MS Sans Serif'})
        formula_format = workbook.add_format(
            {'num_format':num_format, 'bold':True, 'border':1, 'top':1,
             'font_size':8, 'align':'center', 'valign':'vcenter',
             'fg_color':'#CCCCFF', 'font_name':'MS Sans Serif'})
        c_middle = workbook.add_format(
            {'border':1, 'bold':True, 'top':1, 'num_format':num_format})
        report_format2 = workbook.add_format(
            {'border':1, 'bold':True, 'font_size':8,
              'font_name':'MS Sans Serif',
             'align':'center'})
        report_format = workbook.add_format(
            {'border':1, 'bold':True, 'font_size':8, 'fg_color':'#CCCCFF', 'align':'center',
             'font_color':'#3341BE', 'font_name':'MS Sans Serif'})
        rounding = self.env.user.company_id.currency_id.decimal_places or 2
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        time_format = self.env['res.lang']._lang_get(lang_code).time_format

        row = 1
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

        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        today = fields.Date.today().strftime("%d/%b/%Y").title()
        timetoday = fields.Datetime.now().strftime("%d/%b/%Y %I:%M:%S").title()
        f_name = '%s %s %s' % (self._description.upper(), self.group_id.name, today)
        sheet = workbook.add_worksheet(f_name)

        def _header_sheet(sheet):
            sheet.merge_range('A1:C1','', report_format)
            sheet.write(0, 0, _('GRUPO: %s') % self.group_id.name.upper(), report_format)
            sheet.merge_range('D1:F1','', report_format)
            sheet.write(0, 3, _('HORA DE IMPRESIÓN: %s') % timetoday, report_format)

        if f_name:
            _header_sheet(sheet)
            all_lines = self.get_line_for_report()
            if all_lines:
                for j, h in enumerate(self.prepare_header()):
                    sheet.write(1, j, h['name'], header_format)
                    sheet.set_column(1, j, h['larg'])
                for i, line in enumerate(all_lines):
                    i += row
                    sheet.write(i, 0, line.get('enrollment', ''), report_format2)  # Clave
                    sheet.write(i, 1, line.get('curp', ''), report_format2)  # CURP
                    sheet.write(i, 2, line.get('employee_name', ''), report_format2)  # Nombre del trabajador
                    sheet.write(i, 3, line.get('group', ''), report_format2)  # GRUPO
                    sheet.write(i, 4, line.get('contract_code', ''), report_format2)  # GRUPO
                    sheet.write(i, 5, line.get('wage', ''), currency_format)  # SUELDO
                row = i
                for j, h in enumerate(self.prepare_header()):
                    sheet.set_column(j, j, h['larg'])

        workbook.close()
        xlsx_data = output.getvalue()

        export_id = self.env['hr.payslip.run.export.excel'].create(
            {'excel_file':base64.encodestring(xlsx_data),
             'file_name':f_name + '.xlsx'})
        return {
            'view_mode':'form',
            'res_id':export_id.id,
            'res_model':'hr.payslip.run.export.excel',
            'view_type':'form',
            'type':'ir.actions.act_window',
            'target':'new',
        }

class HrContractChangeWageImport(models.TransientModel):
    _name = "hr.contract.change.wage.import"
    _description = "Contract Change Wage"

    file_ids = fields.Many2many(string='Select File',
                                comodel_name='ir.attachment', required=True)
    file_name = fields.Char('File Name', related='file_ids.name')
    date_move = fields.Date(string='Move Date',
                            default=lambda self:fields.Date.to_string(date.today()),
                            help="Keep empty to use the current date. This date will be applied in the affiliate movement",)

    @api.multi
    def clean_file_ids(self):
        self.ensure_one()
        self.file_ids = False
        return {"type":"ir.actions.do_nothing"}

    @api.onchange('file_ids')
    def onchange_file_ids(self):
        if self.file_ids:
            self.read_document()

    def float_to_string(self, value):
        if isinstance(value, float):
            return str(value).split('.')[0]
        else:
            return value

    def check_field_many2one(self, domain, model):
        res_id = self.env[model].search(domain)
        return res_id

    def validate_float(self, value):
        if not isinstance(value, str):
            return value

    @api.multi
    def read_document(self):
        if self.file_ids and len(self.file_ids) > 1:
            raise ValidationError(_('Warning! \n'
                'You can only load one excel file. Please, to remove the files, press Remove file button.'))
        datafile = base64.b64decode(self.file_ids.datas)
        contract = []
        msg_required = ['Los siguientes columnas son mandatorios: \n']
        msg_not_found = ['\nNo se encontrarron resultados para: \n']
        msg_not_format = ['\nFormato incorrecto, en las columnas: \n']
        msg_more = ['\nSe encontraron dos o más coincidencias, en las columnas: \n']
        if datafile:
            book = open_workbook(file_contents=datafile)
            sheet = book.sheet_by_index(0)
            head = 1
            col = 0
            for row in range(2, sheet.nrows):
                lines = {}
                bank_data = {}
                for col in range(sheet.ncols):
                    if col == 0:
                        if sheet.cell_value(row, col):
                            employee = self.float_to_string(sheet.cell_value(row, col)).strip()
                            domain = [('enrollment', '=', employee)]
                            employee_id = self.check_field_many2one(domain, model='hr.employee')
                            if employee_id:
                                if len(employee_id) > 1:
                                    msg_more.append( '%s con la clave (%s) en la fila %s. \n' % (
                                        sheet.cell_value(head, col).upper(), employee,
                                        str(row + 1)))
                                else:
                                    lines['employee_id'] = employee_id.id
                            else:
                                msg_not_found.append(
                                    '%s con la clave (%s) en la fila %s. \n' % (
                                    sheet.cell_value(head, col).upper(), employee,
                                    str(row + 1)))
                        else:
                            msg_required.append('%s en la fila %s. \n' % (
                            sheet.cell_value(head, col).upper(), str(row + 1)))
                    if col == 4:
                        if sheet.cell_value(row, col):
                            value = self.float_to_string(sheet.cell_value(row, col)).strip()
                            domain = [('code', '=', value),('employee_id', '=', employee_id.id)]
                            contract_id = self.check_field_many2one(domain, model='hr.contract')
                            if contract_id:
                                if len(contract_id) > 1:
                                    msg_more.append( '%s con la clave (%s) en la fila %s. \n' % (
                                        sheet.cell_value(head, col).upper(), value,
                                        str(row + 1)))
                                else:
                                    lines['contract_id'] = contract_id.id
                            else:
                                msg_not_found.append(
                                    '%s con la clave (%s) para el empleado %s en la fila %s. \n' % (
                                    sheet.cell_value(head, col).upper(), value, employee,
                                    str(row + 1)))
                        else:
                            msg_required.append('%s en la fila %s. \n' % (
                            sheet.cell_value(head, col).upper(), str(row + 1)))
                    if col == 5:
                        if sheet.cell_value(row, col):
                            wage = self.validate_float(sheet.cell_value(row, col))
                            if wage:
                                lines['wage'] = float(wage)
                            else:
                                msg_not_format.append(
                                    '%s del valor (%s) en la fila %s. INGRESE VALORES NUMÉRICOS \n'
                                    % (sheet.cell_value(head, col).upper(),
                                       sheet.cell_value(row, col),
                                       str(row + 1)))
                        else:
                            msg_required.append('%s en la fila %s. \n' % (
                            sheet.cell_value(head, col).upper(), str(row + 1)))
                contract.append(lines)

            msgs = []
            fields_import = []
            if len(msg_required) > 1:
                msgs += msg_required
            if len(msg_not_found) > 1:
                msgs += msg_not_found
            if len(msg_not_format) > 1:
                msgs += msg_not_format
            if len(msg_more) > 1:
                msgs += msg_more
            if len(msgs):
                self.file_ids = False
                msg_raise = "".join(msgs)
                raise ValidationError(_(msg_raise))
            return contract

    @api.multi
    def import_data(self):
        if not self.file_name:
            raise UserError(
                'Do not load with without a file, or with a file with incorrect data..')
        contracts = self.read_document()
        if contracts:
            contract_obj = self.env['hr.contract']
            for contract in contracts:
                contract_id = contract_obj.browse(contract['contract_id'])
                contract_id.with_context(
                    date_move=self.date_move or fields.Date.today(),
                    update_wage=True).write({
                    'wage':contract['wage'],})
        return {'type':'ir.actions.client', 'tag':'reload',
                'res_model':'hr.contract',
                'context':"{'model': 'hr.contract'}"}

class Contract(models.Model):
    _inherit = 'hr.contract'

    def create_move_affiliate(self):
        print (self.contracting_regime)
        if self.contracting_regime and self.contracting_regime != '02':
            vals = {
                'contract_id': self.id,
                'employee_id': self.employee_id.id,
                'group_id': self.group_id.id,
                'type': '07',
                'date': self.env.context.get('date_move'),
                'origin_move':'400',
                'wage':self.wage,
                'salary':self.integral_salary,
                'contracting_regime':self.contracting_regime,
            }
            print (vals)
            self.env['hr.employee.affiliate.movements'].create(vals)

    @api.multi
    def write(self, vals, create=None):
        res = super(Contract, self).write(vals)
        if 'update_wage' in self.env.context:
            self.create_move_affiliate()
            print ('u')
            print ('kk')
            print ('r')
            print ('r')
            print ('kk')
            print ('r')
            print ('kk')
            print(self.env.context)
            print ('kk')
            print ('kk')
            print ('kk')
            print ('kk')
            # print (stop)