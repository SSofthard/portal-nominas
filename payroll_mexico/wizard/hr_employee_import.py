# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import datetime
import calendar
import pytz
import dateutil
import base64


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

GENDER = {'Hombre': 'male', 'Mujer':'female'}
MARITAL = {'Soltero(a)': 'single', 'Casado(a)': 'married', 'Cohabitante legal': 'cohabitant', 'Viudo(a)': 'widower', 'Divorciado': 'divorced'}

class HrEmployeeImport(models.TransientModel):
    _name = "hr.employee.import"
    _description = "Importar Empleados"

    file_ids = fields.Many2many(string='Layout de empleados', comodel_name='ir.attachment',required=True)
    file_name = fields.Char('Nombre del archivo', related='file_ids.name', required=True)

    @api.onchange('file_ids')
    def onchange_file_ids(self):
        if self.file_ids:
            self.read_document()

    def float_to_string(self, value):
        if isinstance(value, float):
            return str(value).split('.')[0]
        else:
            return value

    def check_gender(self, value, selection):
        if value.strip() in selection.keys():
            return selection.get(value.strip())

    def check_field_many2one(self, domain, model):
        res_id = self.env[model].search(domain)
        return res_id.id

    @api.multi
    def read_document(self, create_incedents=False, create_perceptions=False, create_deductions=False):
        datafile = base64.b64decode(self.file_ids.datas)
        # ~ incedents = []
        # ~ perceptions = []
        employees = []
        msg_required = ['Los siguientes campos son mandatorios: \n']
        msg_not_found = ['\nNo se encontrarron resultados para: \n']
        msg_not_format = ['\nFormato incorrecto: \n']
        if datafile:
            book = open_workbook(file_contents=datafile)
            sheet = book.sheet_by_index(0)
            head = 0
            col = 0
            for row in range(1, sheet.nrows):
                lines = {}
                for col in range(sheet.ncols):
                    if col <= 19 and sheet.cell_value(row,col) == '':
                        msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                    if col == 0 and sheet.cell_value(row,col):
                        lines['name'] = sheet.cell_value(row,col).strip()
                    if col == 1 and sheet.cell_value(row,col):
                        lines['last_name'] = sheet.cell_value(row,col).strip()
                    if col == 2 and sheet.cell_value(row,col):
                        lines['mothers_last_name'] = sheet.cell_value(row,col).strip()
                    if col == 3 and sheet.cell_value(row,col):
                        domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        group_id = self.check_field_many2one(domain, model='hr.group')
                        if group_id:
                            lines['group_id'] = group_id
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 4 and sheet.cell_value(row,col):
                        domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        work_center_id = self.check_field_many2one(domain, model='hr.work.center')
                        if work_center_id:
                            lines['work_center_id'] = work_center_id
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 5 and sheet.cell_value(row,col):
                        lines['work_email'] = sheet.cell_value(row,col).strip()
                    if col == 6 and sheet.cell_value(row,col):
                        domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        department_id = self.check_field_many2one(domain, model='hr.department')
                        if department_id:
                            lines['department_id'] = department_id
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 7 and sheet.cell_value(row,col):
                        domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        job_id = self.check_field_many2one(domain, model='hr.job')
                        if job_id:
                            lines['job_id'] = job_id
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 8 and sheet.cell_value(row,col):
                        domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        resource_calendar_id = self.check_field_many2one(domain, model='resource.calendar')
                        if resource_calendar_id:
                            lines['resource_calendar_id'] = resource_calendar_id
                        else:
                            msg_not_found.append('%s con el nombre  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    # ~ if col == 9 and sheet.cell_value(row,col):
                        # ~ lines['tz'] = sheet.cell_value(row,col).strip()
                    if col in [10] and sheet.cell_value(row,col):
                        domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        country_id = self.check_field_many2one(domain, model='res.country')
                        if country_id:
                            lines['country_id'] = country_id
                        else:
                            msg_not_found.append('%s con el nombre  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 11 and sheet.cell_value(row,col):
                        gender = self.check_gender(sheet.cell_value(row,col), GENDER)
                        if gender:
                            lines['gender'] = gender
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 12 and sheet.cell_value(row,col):
                        marital = self.check_gender(sheet.cell_value(row,col), MARITAL)
                        if marital:
                            lines['marital'] = marital
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 13 and sheet.cell_value(row,col):
                        try:
                            is_datetime = sheet.cell_value(row,col) % 1 != 0.0
                            dt = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row,col), book.datemode))
                            birthday = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            lines['birthday'] = birthday
                        except:
                            msg_not_format.append('%s del valor  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [14] and sheet.cell_value(row,col):
                        domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        place_of_birth = self.check_field_many2one(domain, model='res.country.state')
                        if place_of_birth:
                            lines['place_of_birth'] = place_of_birth
                        else:
                            msg_not_found.append('%s con el nombre  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [15] and sheet.cell_value(row,col):
                        domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        country_of_birth = self.check_field_many2one(domain, model='res.country')
                        if country_of_birth:
                            lines['country_of_birth'] = country_of_birth
                        else:
                            msg_not_found.append('%s con el nombre  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [16] and sheet.cell_value(row,col):
                        domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        company_id = self.check_field_many2one(domain, model='res.company')
                        if company_id:
                            lines['company_id'] = company_id
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [17] and sheet.cell_value(row,col):
                        domain = [('company_id','=',company_id), ('employer_registry','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        employer_register_id = self.check_field_many2one(domain, model='res.employer.register')
                        if employer_register_id:
                            lines['employer_register_id'] = employer_register_id
                        else:
                            msg_not_found.append('%s con la clave  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [18] and sheet.cell_value(row,col):
                        domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        payment_period_id = self.check_field_many2one(domain, model='hr.payment.period')
                        if payment_period_id:
                            lines['payment_period_id'] = payment_period_id
                        else:
                            msg_not_found.append('%s con el nombre %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [19] and sheet.cell_value(row,col):
                        ssnid = self.float_to_string(sheet.cell_value(row,col)).strip()
                        if len(ssnid) == 11:
                            lines['ssnid'] = sheet.cell_value(row,col)
                        else:
                            msg_not_format.append('%s del valor  %s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), ssnid, str(row+1)))
                print ('lines')
                # ~ print (lines)
                print (len(lines))
                print ('lines')
                employees.append(lines)
                    # ~ employees.append({'name': name, 
                                    # ~ 'last_name': last_name,
                                    # ~ 'mothers_last_name': mothers_last_name,
                                    # ~ 'group_id': group_id,
                                    # ~ 'work_center_id': work_center_id,
                                    # ~ 'work_email': work_email,
                                    # ~ 'department_id': department_id,
                                    # ~ 'job_id': job_id,
                                    # ~ 'resource_calendar_id': resource_calendar_id,
                                    # ~ 'tz': 'America/Mexico_City',
                                    # ~ 'country_id': country_id,
                                    # ~ 'gender': gender,
                                    # ~ 'marital': marital,
                                    # ~ 'birthday': birthday,
                                    # ~ 'place_of_birth': place_of_birth,
                                    # ~ 'country_of_birth': country_of_birth,
                                    # ~ 'company_id': company_id,
                                    # ~ 'employer_register_id': employer_register_id,
                                    # ~ 'payment_period_id': payment_period_id,
                                    # ~ })
            msgs = []
            if len(msg_required) > 1:
                msgs += msg_required
            if len(msg_not_found) > 1:
                msgs += msg_not_found
            if len(msg_not_format) > 1:
                msgs += msg_not_format
            if len(msgs) > 3:
                msg_raise="".join(msgs)
                raise  ValidationError(_(msg_raise))
            return employees
            
    @api.multi
    def import_data(self):
        employees = self.read_document()
        
        print (employees)
        print (len(employees))
        # ~ result_incedents = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in vals_incedents)]
        if employees:
             for emp in employees:
                self.env['hr.employee'].create(emp).sudo()
        return {'model':'hr.employee','type': 'ir.actions.client', 'tag': 'reload'}
        # ~ vals_perceptions = self.read_document(create_perceptions=True)
        # ~ result_perceptions = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in vals_perceptions)]
        # ~ if result_perceptions:
             # ~ for perceptions in result_perceptions:
                # ~ self.env['hr.inputs'].create(perceptions)
                
        # ~ vals_deductions = self.read_document(create_deductions=True)
        # ~ result_deductions = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in vals_deductions)]
        # ~ if result_deductions:
             # ~ for deductions in result_deductions:
                # ~ self.env['hr.inputs'].create(deductions)
