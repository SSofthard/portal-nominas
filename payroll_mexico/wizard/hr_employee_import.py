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
MARITAL = {'Soltero': 'single', 'Casado': 'married', 'Cohabitante legal': 'cohabitant', 'Viudo': 'widower', 'Divorciado': 'divorced'}
BLOOD_TYPE = {'O-': 'O-', 'O+': 'O+', 'A-': 'A-', 'A+': 'A+', 'B-': 'B-', 'B+': 'B+', 'AB-': 'AB-', 'AB+': 'AB+'}
CERTIFICATE = {'Licenciado': 'bachelor', 'Máster': 'master', 'Otro': 'other'}
TYPE_SALARY = {'Bruto': 'gross', 'Neto': 'net'}


class HrEmployeeImport(models.TransientModel):
    _name = "hr.employee.import"
    _description = "Importar Empleados"

    file_ids = fields.Many2many(string='Layout de empleados', comodel_name='ir.attachment',required=True)
    file_name = fields.Char('Nombre del archivo', related='file_ids.name')

    @api.onchange('file_ids')
    def onchange_file_ids(self):
        if self.file_ids:
            self.read_document()

    def float_to_string(self, value):
        if isinstance(value, float):
            return str(value).split('.')[0]
        else:
            return value

    def validate_string(self, value):
        if isinstance(value, str):
            return value

    def validate_float(self, value):
        if not isinstance(value, str):
            return value

    def check_selection(self, value, selection):
        if value in selection.keys():
            return selection.get(value.strip())
        else:
            return ''
            
    def check_selection1(self, value, selection):
        if value in selection.keys():
            return value.strip()

    def check_selection2(self, value, selection):
        if int(value) in selection.keys():
            return int(value)

    def check_field_many2one(self, domain, model):
        res_id = self.env[model].search(domain)
        return res_id

    @api.multi
    def read_document(self, create_incedents=False, create_perceptions=False, create_deductions=False):
        if self.file_ids and len(self.file_ids) > 1:
            raise ValidationError(_('Warning! \n'
                'You can only load one excel file. Please, to remove the files, press Remove file button.'))
        datafile = base64.b64decode(self.file_ids.datas)
        # ~ incedents = []
        # ~ perceptions = []
        employees = []
        msg_required = ['Los siguientes campos son mandatorios: \n']
        msg_not_found = ['\nNo se encontrarron resultados para: \n']
        msg_not_format = ['\nFormato incorrecto, en las columnas: \n']
        msg_more = ['\nSe encontraron dos o más coincidencias, en las columnas: \n']
        if datafile:
            book = open_workbook(file_contents=datafile)
            sheet = book.sheet_by_index(0)
            head = 0
            col = 0
            for row in range(1, sheet.nrows):
                lines = {}
                bank_data = {}
                for col in range(sheet.ncols):
                    if col <= 19 and col != 2 and sheet.cell_value(row,col) == '':
                        msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                    lines['tz'] = self.env.user.tz
                    if col == 0 and sheet.cell_value(row,col):
                        name = self.validate_string(sheet.cell_value(row,col))
                        if name:
                            lines['name'] = name.strip()
                        else:
                            msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 1 and sheet.cell_value(row,col):
                        last_name = self.validate_string(sheet.cell_value(row,col))
                        if last_name:
                            lines['last_name'] = last_name.strip()
                        else:
                            msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 2 and sheet.cell_value(row,col):
                        value = self.validate_string(sheet.cell_value(row,col))
                        if value:
                            lines['mothers_last_name'] = value.strip()
                        else:
                            msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 3 and sheet.cell_value(row,col):
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('code','=', value)]
                        # ~ domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        group_id = self.check_field_many2one(domain, model='hr.group')
                        if group_id:
                            if len(group_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['group_id'] = group_id.id
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col == 4 and sheet.cell_value(row,col):
                        # ~ domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('code','=', value)]
                        work_center_id = self.check_field_many2one(domain, model='hr.work.center')
                        if work_center_id:
                            if len(work_center_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['work_center_id'] = work_center_id.id
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col == 5 and sheet.cell_value(row,col):
                        value = self.validate_string(sheet.cell_value(row,col))
                        if value:
                            lines['work_email'] = value.strip()
                        else:
                            msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col == 6 and sheet.cell_value(row,col):
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('code','=', value)]
                        department_id = self.check_field_many2one(domain, model='hr.department')
                        if department_id:
                            if len(department_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['department_id'] = department_id.id
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col == 7 and sheet.cell_value(row,col):
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('code','=', value)]
                        job_id = self.check_field_many2one(domain, model='hr.job')
                        if job_id:
                            if len(job_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['job_id'] = job_id.id
                                lines['job_title'] = self.env['hr.job'].search([('id','=',job_id.id)]).name
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col == 8 and sheet.cell_value(row,col):
                        # ~ domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('name','=', value)]
                        resource_calendar_id = self.check_field_many2one(domain, model='resource.calendar')
                        if resource_calendar_id:
                            if len(resource_calendar_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['resource_calendar_id'] = resource_calendar_id.id
                        else:
                            msg_not_found.append('%s con el nombre (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    # ~ if col == 9 and sheet.cell_value(row,col):
                        # ~ value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        # ~ domain = [('name','=', value)]
                        # ~ address_home_id = self.check_field_many2one(domain, model='res.partner')
                        # ~ if address_home_id:
                            # ~ if len(address_home_id) > 1:
                                # ~ msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            # ~ else:
                                # ~ lines['address_home_id'] = address_home_id.id
                        # ~ else:
                            # ~ msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col in [9] and sheet.cell_value(row,col):
                        # ~ domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('name','=', value)]
                        country_id = self.check_field_many2one(domain, model='res.country')
                        if country_id:
                            if len(country_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['country_id'] = country_id.id
                        else:
                            msg_not_found.append('%s con el nombre (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col == 10 and sheet.cell_value(row,col):
                        gender = self.check_selection(sheet.cell_value(row,col), GENDER)
                        if gender:
                            lines['gender'] = gender
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1),list(GENDER.keys())))
                    if col == 11 and sheet.cell_value(row,col):
                        marital = self.check_selection(sheet.cell_value(row,col), MARITAL)
                        if marital:
                            lines['marital'] = marital
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1),list(MARITAL.keys())))
                    if col == 12 and sheet.cell_value(row,col):
                        try:
                            is_datetime = sheet.cell_value(row,col) % 1 != 0.0
                            dt = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row,col), book.datemode))
                            birthday = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            lines['birthday'] = birthday
                        except:
                            msg_not_format.append('%s del valor (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    if col in [13] and sheet.cell_value(row,col):
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('name','=', value)]
                        # ~ domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        place_of_birth = self.check_field_many2one(domain, model='res.country.state')
                        if place_of_birth:
                            if len(place_of_birth) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['place_of_birth'] = place_of_birth.id
                        else:
                            msg_not_found.append('%s con el nombre (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col in [14] and sheet.cell_value(row,col):
                        # ~ domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('name','=', value)]
                        country_of_birth = self.check_field_many2one(domain, model='res.country')
                        if country_of_birth:
                            if len(country_of_birth) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['country_of_birth'] = country_of_birth.id
                        else:
                            msg_not_found.append('%s con el nombre (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col in [15] and sheet.cell_value(row,col):
                        # ~ domain = [('code','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('name','=', value)]
                        company_id = self.check_field_many2one(domain, model='res.company')
                        if company_id:
                            if len(company_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['company_id'] = company_id.id
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col in [16] and sheet.cell_value(row,col):
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('company_id','=',company_id.id), ('employer_registry','=', value)]
                        employer_register_id = self.check_field_many2one(domain, model='res.employer.register')
                        if employer_register_id:
                            if len(employer_register_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['employer_register_id'] = employer_register_id.id
                        else:
                            msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col in [17] and sheet.cell_value(row,col):
                        # ~ domain = [('name','=', self.float_to_string(sheet.cell_value(row,col)).strip())]
                        value = self.float_to_string(sheet.cell_value(row,col)).strip()
                        domain = [('name','=', value)]
                        payment_period_id = self.check_field_many2one(domain, model='hr.payment.period')
                        if payment_period_id:
                            if len(payment_period_id) > 1:
                                msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                            else:
                                lines['payment_period_id'] = payment_period_id.id
                        else:
                            msg_not_found.append('%s con el nombre (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                    if col in [18] and sheet.cell_value(row,col):
                        ssnid = self.float_to_string(sheet.cell_value(row,col)).strip()
                        if len(ssnid) == 11:
                            lines['ssnid'] = ssnid
                        else:
                            msg_not_format.append('%s del valor (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), ssnid, str(row+1)))
                    if col >= 19 and col <= 54 and not sheet.cell_value(row,col) == '':
                        if col in [19]:
                            rfc = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if len(rfc) == 13:
                                lines['rfc'] = rfc
                            else:
                                msg_not_format.append('%s del valor (%s) en la fila %s, debe contener 13 dígitos. \n' %(sheet.cell_value(head,col).upper(), rfc, str(row+1)))
                        if col in [20]:
                            curp = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if len(curp) == 18:
                                lines['curp'] = curp
                                domain = [('curp','=', curp)]
                                address_home_id = self.check_field_many2one(domain, model='res.partner')
                                if address_home_id:
                                    if len(address_home_id) > 1:
                                        msg_more.append('En DIRECCIÓN PRIVADA con la clave (%s) en la fila %s. \n' %(curp, str(row+1)))
                                    else:
                                        lines['address_home_id'] = address_home_id.id
                                else:
                                    msg_not_found.append('En DIRECCIÓN PRIVADA con la clave (%s) en la filawww %s. \n' %(curp, str(row+1)))
                            else:
                                msg_not_format.append('%s del valor (%s) en la fila %s, debe contener 18 dígitos. \n' %(sheet.cell_value(head,col).upper(), curp, str(row+1)))
                        if col in [21]:
                            mobile_phone = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                lines['mobile_phone'] = int(mobile_phone)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE SÓLO NÚMEROS). \n' %(sheet.cell_value(head,col).upper(), mobile_phone, str(row+1)))
                        if col in [22]:
                            work_phone = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                lines['work_phone'] = int(work_phone)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE SÓLO NÚMEROS). \n' %(sheet.cell_value(head,col).upper(), work_phone, str(row+1)))
                        if col in [23]: # Responsable
                            value = self.float_to_string(sheet.cell_value(row,col)).strip()
                            domain = [('enrollment','=', value)]
                            parent_id = self.check_field_many2one(domain, model='hr.employee')
                            if parent_id:
                                if len(parent_id) > 1:
                                    msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                                else:
                                    lines['parent_id'] = parent_id.id
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                        if col in [24]: # Es un director
                            manager = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                int_manager = int(manager)
                                if int_manager in [0,1]:
                                    lines['manager'] = int(manager)
                                else:
                                    msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), manager, str(row+1)))
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), manager, str(row+1)))
                        if col in [25]: # Nº identificación
                            lines['identification_id'] = self.float_to_string(sheet.cell_value(row,col)).strip()
                        if col in [26]: # Nº Pasaporte
                            lines['passport_id'] = self.float_to_string(sheet.cell_value(row,col)).strip()
                        if col in [27]: # Nº Pasaporte
                            value = self.validate_string(sheet.cell_value(row,col))
                            if value:
                                lines['personal_email'] = value.strip()
                            else:
                                msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [28]:
                            personal_movile_phone = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                lines['personal_movile_phone'] = int(personal_movile_phone)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE SÓLO NÚMEROS). \n' %(sheet.cell_value(head,col).upper(), personal_movile_phone, str(row+1)))
                        if col in [29]:
                            personal_phone = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                lines['personal_phone'] = int(personal_phone)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE SÓLO NÚMEROS). \n' %(sheet.cell_value(head,col).upper(), personal_phone, str(row+1)))
                        if col in [30]:
                            km_home_work = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                lines['km_home_work'] = int(km_home_work)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE SÓLO NÚMEROS). \n' %(sheet.cell_value(head,col).upper(), km_home_work, str(row+1)))
                        if col in [31]:
                            value = self.validate_string(sheet.cell_value(row,col))
                            if value:
                                lines['health_restrictions'] = value.strip()
                            else:
                                msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [32]:
                            value = self.validate_string(sheet.cell_value(row,col))
                            if value:
                                lines['emergency_contact'] = value.strip()
                            else:
                                msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [33]:
                            value = self.validate_string(sheet.cell_value(row,col))
                            if value:
                                lines['emergency_address'] = value.strip()
                            else:
                                msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [34]:
                            value = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                lines['emergency_phone'] = int(value)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE SÓLO NÚMEROS). \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                        if col in [35]:
                            # ~ value = dict(self.env['hr.employee']._fields.get('blood_type').selection)
                            blood_type = self.check_selection(sheet.cell_value(row,col), BLOOD_TYPE)
                            if blood_type:
                                lines['blood_type'] = blood_type
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1), list(BLOOD_TYPE.keys())))
                        if col in [36]:
                            lines['visa_no'] = self.float_to_string(sheet.cell_value(row,col)).strip()
                        if col in [37]:
                            lines['permit_no'] = self.float_to_string(sheet.cell_value(row,col)).strip()
                        if col in [38]:
                            try:
                                is_datetime = sheet.cell_value(row,col) % 1 != 0.0
                                dt = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row,col), book.datemode))
                                lines['visa_expire'] = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [39]:
                            certificate = self.check_selection(sheet.cell_value(row,col), CERTIFICATE)
                            if certificate:
                                lines['certificate'] = certificate
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1),list(CERTIFICATE.keys())))
                        if col in [40]:
                            value = self.validate_string(sheet.cell_value(row,col))
                            if value:
                                lines['study_field'] = value.strip()
                            else:
                                msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [41]:
                            value = self.validate_string(sheet.cell_value(row,col))
                            if value:
                                lines['study_school'] = value.strip()
                            else:
                                msg_not_format.append('%s valor (%s) en la fila %s NO PUEDE CONTENER SÓLO NÚMEROS. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [42]:
                            salary_type = dict(self.env['hr.employee']._fields.get('salary_type').selection)
                            cell_value = self.float_to_string(sheet.cell_value(row,col))
                            value = self.check_selection1(cell_value.strip(), salary_type)
                            if value:
                                lines['salary_type'] = value
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), cell_value, str(row+1),list(salary_type.keys())))
                        if col in [43]:
                            working_day_week = dict(self.env['hr.employee']._fields.get('working_day_week').selection)
                            cell_value = self.float_to_string(sheet.cell_value(row,col))
                            value = self.check_selection1(cell_value.strip(), working_day_week)
                            if value:
                                lines['working_day_week'] = value
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), cell_value, str(row+1),list(working_day_week.keys())))
                        if col in [44]:
                            type_worker = dict(self.env['hr.employee']._fields.get('type_worker').selection)
                            cell_value = self.float_to_string(sheet.cell_value(row,col))
                            value = self.check_selection1(cell_value.strip(), type_worker)
                            if value:
                                lines['type_worker'] = value
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), cell_value, str(row+1),list(type_worker.keys())))
                        if col in [45]:
                            umf = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if len(umf) == 3:
                                lines['umf'] = umf
                            else:
                                msg_not_format.append('%s del valor (%s) en la fila %s. INGRESE LA CLAVE DE TRES DÍGITOS \n' %(sheet.cell_value(head,col).upper(), umf, str(row+1)))
                        if col in [46]:
                            payment_holidays_bonus = dict(self.env['hr.employee']._fields.get('payment_holidays_bonus').selection)
                            cell_value = self.float_to_string(sheet.cell_value(row,col))
                            try:
                                value = self.check_selection2(int(cell_value), payment_holidays_bonus)
                                lines['payment_holidays_bonus'] = value
                            except:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), cell_value, str(row+1),list(payment_holidays_bonus.keys())))
                        if col in [47]: # Pagar días festivos?
                            pay_holiday = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                int_pay_holiday = int(pay_holiday)
                                if int_pay_holiday in [0,1]:
                                    lines['pay_holiday'] = int_pay_holiday
                                else:
                                    msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), pay_holiday, str(row+1)))
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), pay_holiday, str(row+1)))
                            
                        if col in [48]: # Pagar días festivos?
                            pay_extra_hours = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                int_pay_extra_hours = int(pay_extra_hours)
                                if int_pay_extra_hours in [0,1]:
                                    lines['pay_extra_hours'] = int_pay_extra_hours
                                else:
                                    msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), pay_extra_hours, str(row+1)))
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), pay_extra_hours, str(row+1)))
                        if col in [49]:
                            type_salary_50 = self.check_selection(sheet.cell_value(row,col), TYPE_SALARY)
                            if type_salary_50:
                                lines['type_salary'] = str(type_salary_50)
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' 
                                    %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1),list(TYPE_SALARY.keys())))
                        if col in [50]:
                            monthly_salary = self.validate_float(sheet.cell_value(row,col))
                            if monthly_salary:
                                lines['monthly_salary'] = float(monthly_salary)
                            else:
                                msg_not_format.append('%s del valor (%s) en la fila %s. INGRESE VALORES NUMÉRICOS \n' 
                                    %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [51]:
                            wage_salaries = self.validate_float(sheet.cell_value(row,col))
                            if wage_salaries:
                                lines['wage_salaries'] = wage_salaries
                            else:
                                msg_not_format.append('%s del valor (%s) en la fila %s. INGRESE VALORES NUMÉRICOS \n' 
                                    %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [52]:
                            free_salary = self.validate_float(sheet.cell_value(row,col))
                            if free_salary:
                                lines['free_salary'] = free_salary
                            else:
                                msg_not_format.append('%s del valor (%s) en la fila %s. INGRESE VALORES NUMÉRICOS \n' 
                                    %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                    #Cuentas bancarias
                    if col >= 53 and not sheet.cell_value(row,col) == '':
                        if col == 53:
                            value = self.float_to_string(sheet.cell_value(row,col)).strip()
                            domain = [('name','=', value)]
                            bank_id = self.check_field_many2one(domain, model='res.bank')
                            if bank_id:
                                if len(bank_id) > 1:
                                    msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                                else:
                                    bank_data['bank_id'] = bank_id.id
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                        if col == 54:
                            value = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                if value and len(value) in [10,11,18]:
                                    bank_data['bank_account'] = value
                                    bank_data['reference'] = value[0:4]
                                    bank_data['beneficiary'] = '%s %s' %(name, last_name)
                                    bank_data['predetermined'] = True
                                else:
                                    msg_not_format.append('%s del valor (%s) en la fila %s.  debe contener 10, 11 ó 18 dígitos\n' 
                                        %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s.  debe contener 10, 11 ó 18 dígitos\n' 
                                    %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col == 55:
                            location_branch = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if location_branch:
                                bank_data['location_branch'] = location_branch
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col == 56:
                            deceased = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                int_deceased = int(deceased)
                                if int_deceased in [0,1]:
                                    lines['deceased'] = int_deceased
                                else:
                                    msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), deceased, str(row+1)))
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), deceased, str(row+1)))
                        if col == 57:
                            syndicalist = self.float_to_string(sheet.cell_value(row,col)).strip()
                            try:
                                int_syndicalist = int(syndicalist)
                                if int_syndicalist in [0,1]:
                                    lines['syndicalist'] = int_syndicalist
                                else:
                                    msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), syndicalist, str(row+1)))
                            except:
                                msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE 1 ó 0). \n' %(sheet.cell_value(head,col).upper(), syndicalist, str(row+1)))
                        if col == 58:
                            title = self.float_to_string(sheet.cell_value(row,col)).strip()
                            domain = [('name','=', title)]
                            title_id = self.check_field_many2one(domain, model='res.partner.title')
                            if title_id:
                                if len(title_id) > 1:
                                    msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), title, str(row+1)))
                                else:
                                    lines['title'] = title_id.id
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), title, str(row+1)))
                        if col in [59]:
                            type_working_day = dict(self.env['hr.employee']._fields.get('type_working_day').selection)
                            cell_value = self.float_to_string(sheet.cell_value(row,col))
                            value = self.check_selection1(cell_value.strip(), type_working_day)
                            if value:
                                lines['type_working_day'] = value
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), cell_value, str(row+1),list(type_working_day.keys())))
                    if bank_data:
                        lines['bank_account_ids'] = [(0, 0, bank_data)]
                employees.append(lines)
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
                msg_raise="".join(msgs)
                raise  ValidationError(_(msg_raise))
            return employees

    @api.multi
    def clean_file_ids(self):
        self.ensure_one()
        self.file_ids = False
        return {"type":"ir.actions.do_nothing"}

    @api.multi
    def import_data(self):
        if not self.file_name:
            raise UserError('Do not load with without a file, or with a file with incorrect data..')
        employees = self.read_document()
        if employees:
             for emp in employees:
                self.env['hr.employee'].create(emp).sudo()
        return {'type': 'ir.actions.client', 'tag': 'reload', 'res_model':'hr.employee', 'context':"{'model': 'hr.employee'}"}
