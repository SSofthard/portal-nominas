# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import os
import time
import datetime
import calendar
import pytz
import dateutil
import base64
import codecs
import zipfile
import tempfile

from zipfile import ZipFile
from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from datetime import datetime
from xlrd import open_workbook
from dateutil.relativedelta import relativedelta
from os import listdir


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo.tools.mimetypes import guess_mimetype
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, pycompat, misc
from odoo import tools, api, fields, models, _
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


class HrIncidentsImport(models.TransientModel):
    _name = "hr.incidents.import"
    _description = "Incidents Import"

    file_ids = fields.Many2many(string='Incidents File', comodel_name='ir.attachment',required=True)
    file_name = fields.Char('File name', related='file_ids.name', required=False)
    create_document = fields.Boolean("Create Documents", default=True)
    file_zip = fields.Binary(string="File Content Document",required=False, filters='*.zip')

    @api.onchange('create_document')
    def onchange_create_document(self):
        if not self.create_document:
            self.file_zip = False
    
    @api.multi
    def clean_file_ids(self):
        self.ensure_one()
        self.file_ids = False
        return {"type":"ir.actions.do_nothing"}

    @api.onchange('file_zip')
    def onchange_file_zip(self):
        if self.file_zip:
            datafile = base64.b64decode(self.file_zip)
            input_file = io.BytesIO(datafile)
            self.file_ids = False
            if not zipfile.is_zipfile(input_file):
                raise UserError(_('Only zip files are supported.'))

    @api.onchange('file_ids')
    def onchange_file_ids(self):
        if self.file_ids:
            if self.create_document and not self.file_zip:
                raise UserError(_('File Content Document is required.'))
            self.read_document()

    # ~ def get_folder(self, employee_id, ):
        # ~ """ Function get folder is not exists, create folder """
        # ~ Folder = self.env['documents.folder']
        # ~ #Search or Create Group Folder 
        # ~ group_folder = employee_id.group_id.name.upper()
        # ~ group_folder_id = Folder.search([('name','=',group_folder)])
        # ~ if not group_folder_id:
            # ~ group_folder_id = Folder.create({
                # ~ 'name': group_folder,
                # ~ 'company_id': employee_id.company_id.id,
            # ~ })
        # ~ #Search or Create Incidents Folser 
        # ~ incidents_folder = 'INCIDENCIAS'
        # ~ incidents_folder_id = Folder.search([('name','=',incidents_folder)])
        # ~ if not incidents_folder_id:
            # ~ incidents_folder_id = Folder.create({
                # ~ 'name': incidents_folder,
                # ~ 'company_id': employee_id.company_id.id,
            # ~ })
        # ~ #Search or Create Year Folder
        # ~ year_folder = str(self.year)
        # ~ year_folder_id = Folder.search([('name','=',year_folder),('parent_folder_id','=',incidents_folder_id)])
        # ~ if not year_folder_id:
            # ~ year_folder_id = Folder.create({
                # ~ 'name': year_folder,
                # ~ 'parent_folder_id': group_folder_id.id,
                # ~ 'company_id': self.company_id.id,
            # ~ })
        # ~ #Search or Create Month Folder
        # ~ month_folder = dict(
            # ~ self._fields['payroll_month']._description_selection(
                # ~ self.env)).get(self.payroll_month).upper()
        # ~ month_folder_id = Folder.search([('name','=',month_folder),('parent_folder_id','=',year_folder_id.id)])
        # ~ if not month_folder_id:
            # ~ month_folder_id = Folder.create({
                # ~ 'name': month_folder,
                # ~ 'parent_folder_id': year_folder_id.id,
                # ~ 'company_id': self.company_id.id,
            # ~ })
        # ~ #Search or Create Period Folder
        # ~ date_from = self.date_from.strftime('%d/%b/%Y').title()
        # ~ date_to = self.date_to.strftime('%d/%b/%Y').title()
        # ~ period_folder = '%s A %s' %(date_from, date_to)
        # ~ period_folder_id = Folder.search([('name','=',period_folder),('parent_folder_id','=',month_folder_id.id)])
        # ~ if not period_folder_id:
            # ~ period_folder_id = Folder.create({
                # ~ 'name': period_folder,
                # ~ 'parent_folder_id': month_folder_id.id,
                # ~ 'company_id': self.company_id.id,
            # ~ })
        # ~ return period_folder_id.id

    def data_zipfile(self):
        """ Function doc """
        if self.file_zip:
            datafile = base64.b64decode(self.file_zip)
            input_file = io.BytesIO(datafile)
            if not zipfile.is_zipfile(input_file):
                raise UserError(_('Only zip files are supported.'))
            try:
                # ~ with zipfile.ZipFile(input_file, "r") as z:
                return zipfile.ZipFile(input_file)
            except:
                raise UserError(_('File Content Document is required.'))

    @api.multi
    def read_document(self, create_incedents=False, create_perceptions=False, create_deductions=False):
        datafile = base64.b64decode(self.file_ids.datas)
        book = open_workbook(file_contents=datafile)
        incedents = []
        perceptions = []
        zip_namelist = []
        deductions = []
        if self.file_zip and self.create_document:
            zf = self.data_zipfile()
            zip_namelist += zf.namelist()
        if datafile:
            book = open_workbook(file_contents=datafile)
            sheet = book.sheet_by_index(0)
            col = 1
            for row in range(1, sheet.nrows):
                if sheet.cell_value(row, 1) == 'F':
                    employee_id = self.check_employee(pycompat.text_type(sheet.cell_value(row, 0)), row, col)
                    initial = pycompat.text_type(sheet.cell_value(row , 1))
                    key = pycompat.text_type(sheet.cell_value(row , 2))
                    type_leave = self.check_type_leave(initial+key,row, col)
                    duration = pycompat.text_type(sheet.cell_value(row , 3))
                    is_datetime = sheet.cell_value(row , 4) % 1 != 0.0
                    dt = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row , 4), book.datemode))
                    date_from = dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if is_datetime else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    data_date = self.check_days_date(employee_id.id, date_from, duration, type_leave)
                    
                    location_path = sheet.cell_value(row , 5)
                    if self.create_document:
                        name_document = '/%s' % location_path
                        filestore = [m for m in zip_namelist if m.endswith(name_document)]
                        if filestore:
                            ducument = zf.read(filestore[0])
                            ducument_data = base64.b64encode(ducument)
                            attachment_dict = {
                                'name': '%s %s' %(employee_id.complete_name, filestore[0]),
                                'res_model': 'hr.leave',
                                'partner_id': employee_id.address_home_id.id,
                                'owner_id': self.env.user.id,
                                # ~ 'folder_id': folder_id,
                                'type': 'binary',
                                'datas_fname': '%s %s' %(employee_id.complete_name, filestore[0]),
                                'datas': ducument_data,
                            }
                            
                            incedents.append(
                                    {'employee_id': employee_id.id, 
                                    'holiday_status_id': data_date.get('holiday_status_id'),
                                    'number_of_days': data_date.get('number_of_days'),
                                    'request_date_from': data_date.get('request_date_from'),
                                    'request_date_to': data_date.get('request_date_to'),
                                    'date_from': data_date.get('date_from'),
                                    'date_to': data_date.get('date_to'),
                                    'request_date_from_period': data_date.get('request_date_from_period'),
                                    'request_unit_half': data_date.get('request_unit_half'),
                                    'document_ids': [(0, 0, attachment_dict)],
                                    'holiday_type': data_date.get('holiday_type')})
                        else:
                            raise UserError(_('No se encontro el archivo con el nombre %s, en el archivo .ZIP en la Fila %s,') % (location_path, row))
                    else:
                        incedents.append(
                                    {'employee_id': employee_id.id, 
                                    'holiday_status_id': data_date.get('holiday_status_id'),
                                    'number_of_days': data_date.get('number_of_days'),
                                    'request_date_from': data_date.get('request_date_from'),
                                    'request_date_to': data_date.get('request_date_to'),
                                    'date_from': data_date.get('date_from'),
                                    'date_to': data_date.get('date_to'),
                                    'request_date_from_period': data_date.get('request_date_from_period'),
                                    'request_unit_half': data_date.get('request_unit_half'),
                                    'holiday_type': data_date.get('holiday_type')})
                if sheet.cell_value(row, 1) == 'P':
                    employee_id = self.check_employee(pycompat.text_type(sheet.cell_value(row , 0)), row, col)
                    initial = pycompat.text_type(sheet.cell_value(row , 1))
                    key = pycompat.text_type(sheet.cell_value(row , 2))
                    rule_input_id = self.check_rule_input(initial+key,row, col)
                    value = sheet.cell_value(row , 3)
                    is_float = value % 1 != 0.0
                    amount = pycompat.text_type(value) if is_float else pycompat.text_type(int(value))
                    # Add date for type perception double and triple overtime
                    date_overtime = None
                    if key in ('003','005'):
                        if not sheet.cell_value(row , 4):
                            raise UserError(_('Está agregando Horas Extras, Es Requerido Indicar la Fecha. Fila %s, Clave %s.') % (row, key))
                        is_datetime = sheet.cell_value(row , 4) % 1 != 0.0
                        dt = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row , 4), book.datemode))
                        date_overtime = dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if is_datetime else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            
                    perceptions.append(
                                    {'employee_id': employee_id, 
                                    'input_id': rule_input_id,
                                    'amount': amount,
                                    'date_overtime': date_overtime,
                                    'type': 'perception',}
                                    )
                if sheet.cell_value(row, 1) == 'D':
                    employee_id = self.check_employee(pycompat.text_type(sheet.cell_value(row , 0)), row, col)
                    initial = pycompat.text_type(sheet.cell_value(row , 1))
                    key = pycompat.text_type(sheet.cell_value(row , 2))
                    rule_input_id = self.check_rule_input(initial+key,row, col)
                    value = sheet.cell_value(row , 3)
                    is_float = value % 1 != 0.0
                    amount = pycompat.text_type(value) if is_float else pycompat.text_type(int(value))
                    deductions.append(
                                            {'employee_id': employee_id, 
                                            'input_id': rule_input_id,
                                            'amount': amount,
                                            'type': 'deductions',}
                                            )
        if create_incedents:
            return incedents
        if create_perceptions:
            return perceptions
        if create_deductions:
            return deductions

    def check_days_date(self, employee, request_date_from, number_of_days, type_leave):
        request_date_from_period = 'am'
        if not number_of_days or float(number_of_days) < 0:
            raise UserError(_('Negative or empty values ​​are not allowed for the number of days.'))
        if not employee:
            raise UserError(_('The employee is required.'))
        employee_id = self.env['hr.employee'].search([('id','=', employee)])
        if not employee_id:
            raise UserError(_('No employees found for the key %s.') % employee)

        dates = {}
        calendar = employee_id.resource_calendar_id or self.env.user.company_id.resource_calendar_id
        request_date_from = datetime.strptime(fields.Date.from_string(request_date_from).strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
        tz = self.env.user.tz if self.env.user.tz else 'UTC'  # custom -> already in UTC
        
        domain = [('calendar_id', '=', calendar.id or self.env.user.company_id.resource_calendar_id.id)]
        attendances = self.env['resource.calendar.attendance'].search(domain, order='dayofweek, day_period DESC')

        # find first attendance coming after first_day
        attendance_from = next((att for att in attendances if int(att.dayofweek) >= request_date_from.weekday()), attendances[0])
        hour_from = float_to_time(attendance_from.hour_from)
        
        request_date_from = timezone(tz).localize(datetime.combine(request_date_from.date(), hour_from)).astimezone(UTC).replace(tzinfo=None)
        request_date_to = request_date_from + timedelta(hours=calendar.hours_per_day or HOURS_PER_DAY)
        
        # find last attendance coming before last_day
        attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= request_date_to.weekday()), attendances[-1])
        hour_to = float_to_time(attendance_to.hour_to)
        request_date_from = timezone(tz).localize(datetime.combine(request_date_from.date(), hour_from)).astimezone(UTC).replace(tzinfo=None)
        # if ist half day
        if float(number_of_days) == 0.5 and request_date_from_period:
            if request_date_from_period == 'am':
                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_from.hour_to)
            else:
                hour_from = float_to_time(attendance_to.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)
            
            # ~ half_day = calendar.hours_per_day / 2 or HOURS_PER_DAY / 2
            request_date_from = timezone(tz).localize(datetime.combine(request_date_from.date(), hour_from)).astimezone(UTC).replace(tzinfo=None)
            request_date_to = timezone(tz).localize(datetime.combine(request_date_to.date(), hour_to)).astimezone(UTC).replace(tzinfo=None)
        if float(number_of_days) == 1:
            request_date_to = request_date_from + timedelta(hours=calendar.hours_per_day or HOURS_PER_DAY)
        if float(number_of_days) > 1:
            request_date_to = request_date_from + timedelta(days=float(number_of_days))
        
        dates['request_date_from'] = request_date_from.date()
        dates['request_date_to'] = request_date_to.date()
        dates['date_from'] = request_date_from
        dates['date_to'] = request_date_to
        dates['request_date_from_period'] = request_date_from_period if number_of_days == 0.5 else None
        dates['holiday_type'] = 'employee'
        dates['request_unit_half'] = True if number_of_days == 0.5 else False
        dates['number_of_days'] = number_of_days
        dates['holiday_status_id'] = type_leave
        return dates

    @api.multi
    def check_rule_input(self, value, row, col):
        rule_input = self.env['hr.rule.input']
        if not value:
            raise UserError('The keys field is empty in row %s, complete all the fields in the file.' % str(row+1))
        else:
            rule_input_id = rule_input.search([('code', '=', str(value))])
            if not rule_input_id:
                raise UserError('No se encontraron entradas con del código %s, en fila %s.' % (str(value), str(row+1)))
            if len(rule_input_id) > 1:
                raise UserError('Tiene más de una entrada con el mismo código, esto no es permitido. Verifique! Código %s, en fila %s.' % (str(value), str(row+1)))
            else:
                return rule_input_id.id

    @api.multi
    def check_type_leave(self, value, row, col):
        leave_type = self.env['hr.leave.type']
        if not value:
            raise UserError('The keys field is empty in row %s, complete all the fields in the file.' % str(row+1))
        else:
            leave_type_id = leave_type.search([('code', '=', str(value))])
            if not leave_type_id:
                raise UserError('No results were found for the fault %s, in row %s.' % (str(value), str(row+1)))
            else:
                return leave_type_id.id

    @api.multi
    def check_employee(self, value, row, col):
        value = value.split('.')
        employee = self.env['hr.employee']
        if not value:
            raise UserError('The employee number field is empty in row %s, complete all the fields in the file.' % str(row+1))
        else:
            employee_id = employee.search([('enrollment', '=', str(value[0]))])
            if not employee_id:
                raise UserError('No results found for employee number %s, in row %s.' % (str(value), str(row+1)))
            else:
                return employee_id

    @api.multi
    def import_data(self):
        vals_incedents = self.read_document(create_incedents=True)
        # ~ result_incedents = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in vals_incedents)]
        if vals_incedents:
            for incedents in vals_incedents:
                leave_id = self.env['hr.leave'].create(incedents).sudo()
                leave_id.document_ids.write({'res_id': leave_id.id})

        vals_perceptions = self.read_document(create_perceptions=True)
        result_perceptions = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in vals_perceptions)]
        if result_perceptions:
             for perceptions in result_perceptions:
                self.env['hr.inputs'].create(perceptions)
                
        vals_deductions = self.read_document(create_deductions=True)
        result_deductions = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in vals_deductions)]
        if result_deductions:
             for deductions in result_deductions:
                self.env['hr.inputs'].create(deductions)
