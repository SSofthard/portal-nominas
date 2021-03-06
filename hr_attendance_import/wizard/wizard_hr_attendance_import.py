import xlsxwriter
import base64
import logging
import psycopg2
import pandas as pd
import io
import pytz
import xlwt
import os

from xlrd import open_workbook
from datetime import datetime

from odoo import api, fields, models, _
from dateutil.parser import parse
from odoo.tools import pycompat
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


try:
    import xlrd
    try:
        from xlrd import xlsx # pylint: disable=W0611
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

_logger = logging.getLogger(__name__)


class WizardImportAttendance(models.TransientModel):
    _name = "wizard.import.attendance.xls"
    _description = 'Import Attendance Layout'

    file_xls = fields.Binary("File XLS/XLSX", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('successful', 'Successful'),
        ('error', 'Error'),
    ], default="draft")
    error_message = fields.Text(readonly=True)
    
    @api.onchange('file_xls')
    def onchange_file_xls(self):
        if self.file_xls:
            self.read_document()

    @api.multi
    def read_document(self):
        datafile = base64.b64decode(self.file_xls)
        input_file = io.BytesIO(datafile)
        xml_obj = pd.read_excel(input_file)
        xml_obj.columns = ['Employee', 'Check In', 'Check Out']
        grouped_by_code = xml_obj.groupby(["Employee", "Check In", "Check Out"])
        print (grouped_by_code)
        for code, group in grouped_by_code:
            self.check_employee(group['Employee'].values[0])

    @api.multi
    def check_employee(self, value):
        employee = self.env['hr.employee']
        if not value:
            raise UserError('The enrollment field is empty, complete all the fields in the file.' % str(value))
        else:
            employee_id = employee.search([('enrollment', '=', value),('active', '=', 'active')]).id
            if not employee_id:
                raise UserError('No results found for enrollment %s.' % (str(value)))
            else:
                return employee_id
    
    def validate_length_columns(self, field):
        if not xlrd:
            raise ValueError(
                _("Unable to load xls file: requires Python module xlrd"))
        data = base64.b64decode(self.file_xls)
        book = xlrd.open_workbook(file_contents=data)
        ncols = book.sheet_by_index(0).ncols
        if ncols > len(field):
            message = _(
                "The number of columns indicated in xls is greater than"
                "the columns allowed, the format must be:"
                "Employee, check in, check Out")
            raise ValueError(message)
        if ncols < len(field)-2:
            message = _(
                "The number of columns indicated in xls is less than"
                "the columns allowed, the minimum allowed is 3")
            raise ValueError(message)
        if ncols >= len(field)-2 and ncols <= len(field):
            field = field[0: ncols]
        return field

    @api.multi
    def compose_html_error(self, messages):
        colors = {'error': 'red', 'warning': 'yellow', 'info': 'green'}
        html = ""
        for msg in messages:
            if msg['type'] in ['error', 'warning']:
                self.state = 'error'
            color = colors.get(msg['type'], 'green')
            msg['color'] = color
            html += (
                "<p style=color:{color}>{message}</p><br/>".format(
                    **msg))
        self.error_message = html
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'res_model': 'wizard.import.attendance.xls',
            'target': 'new',
        }

    @api.multi
    def load_file(self):
        self.ensure_one()
        self._cr.execute('SAVEPOINT import')
        import_fields = ['employee_id', 'check_in', 'check_out']
        try:
            data, import_fields = self._convert_import_data(
                import_fields, {})
            
            data = self._parse_import_data(data, import_fields)
        except ValueError as error:
            message = [{
                'type': 'error',
                'message': pycompat.text_type(error),
                'record': False}]
            return self.compose_html_error(message)
        model = self.env['hr.attendance'].with_context(
            import_file=True)
        defer_parent_store = self.env.context.get(
            'defer_parent_store_computation', True)
        if defer_parent_store and model._parent_store:
            model = model.with_context(defer_parent_store_computation=True)
        import_result = model.load(import_fields, data)
        _logger.info('done')
        try:
            self._cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass
        if not import_result['messages']:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        return self.compose_html_error(import_result['messages'])

    @api.model
    def _convert_import_data(self, fields_val, options):
        import_fields = [f for f in fields_val if f]
        data = self.get_tuple_data_xls()
        return data, import_fields

    @api.multi
    def _parse_import_data(self, data, fields_val):
        base_import = self.env['base_import.import']
        return base_import._parse_import_data_recursive(
            'hr.attendance', '', data, fields_val, {'datetime_format': DEFAULT_SERVER_DATETIME_FORMAT})

    @api.multi
    def _read_xls(self):
        """ Read file content, using xlrd lib """
        base_import = self.env['base_import.import']
        data = base64.b64decode(self.file_xls)
        book = xlrd.open_workbook(file_contents=data)
        return base_import._read_xls_book(book)

    @api.multi
    def convert_utc_timestamp(self,date):
        tz_user = pytz.timezone(self.env.user.partner_id.tz)
        date = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        local_dt = tz_user.localize(date, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def get_tuple_data_xls(self):
        result = []
        datafile = base64.b64decode(self.file_xls)
        input_file = io.BytesIO(datafile)
        xml_obj = pd.read_excel(input_file)
        xml_obj.columns = ['Employee', 'Check In', 'Check Out']
        grouped_by_code = xml_obj.groupby(["Employee", "Check In", "Check Out"])
        for code, group in grouped_by_code:
            employee = self.env['hr.employee'].search([('enrollment', '=', group['Employee'].values[0])])
            check_in = group['Check In'].values[0]
            check_out = group['Check Out'].values[0]
            result += [[
                employee.name,
                pd.to_datetime(check_in).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                pd.to_datetime(check_out).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            ]]
        return result


class WizardExportAttendance(models.TransientModel):
    _name = "wizard.export.attendance.xls"
    _description = 'Export Attendance Layout'
    
    name = fields.Char("Name", default='Layout-' + str(fields.Date.today()))
    carrier_xlsx_document = fields.Binary("Layout", )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('successful', 'Successful'),
        ('error', 'Error'),
    ], default="draft")

    @api.multi
    def generate_excel(self):
        head = [
            {'name': 'Employee',
             'larg': 50,
             'col': {}},
            {'name': 'Check In',
             'larg': 20,
             'col': {}},
            {'name': 'Check Out',
             'larg': 20,
             'col': {}},
        ]
        if not os.path.exists('/tmp/file.xlsx'):
            with open('/tmp/file.xlsx', 'w'): pass
        file_data = '/tmp/file.xlsx'
        workbook = xlsxwriter.Workbook(file_data)
        sheet = workbook.add_worksheet(self.name)
        bold = workbook.add_format({'bold': True})
        row = 0
        col = 0
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
        sheet.write_comment('A1', 'This is a Employee Code, Example: \nEMP-0001')
        sheet.write_comment('B1', 'This is Date and time of entry, Example format: \nDD/MM/AAAA HH:MM:SS or \nAAAA-MM-DD HH:MM:SS')
        sheet.write_comment('C1', 'This is Date and time of departure, Example format: \nDD/MM/AAAA HH:MM:SS or \nAAAA-MM-DD HH:MM:SS')
        sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                        {'total_row': 1,
                         'columns': table,
                         'style': 'Table Style Light 9',
                        })
        sheet.set_row(0, 15, bold)
        workbook.close()
        with open(file_data, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.name = str(self.name) + '.xlsx'
        self.write({'carrier_xlsx_document': file_base64, })
        self.state = 'successful'

        
