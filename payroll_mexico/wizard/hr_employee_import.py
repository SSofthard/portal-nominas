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
TYPE_CONTRACT = {'Con antigüedad': 'with_seniority', 'Sin antigüedad': 'without_seniority', 'No aplica': 'na'}


class HrEmployeeImport(models.TransientModel):
    _name = "hr.employee.import"
    _description = "Importar Empleados"

    file_ids = fields.Many2many(string='Layout de empleados', comodel_name='ir.attachment',required=True)
    file_name = fields.Char('Nombre del archivo', related='file_ids.name')
    create_contract = fields.Boolean(string='Create contract', default=True)

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
                contracts = {}
                contracts['row'] = row + 1
                for col in range(sheet.ncols):
                    if col <= 19 and col != 2 and sheet.cell_value(row,col) == '' or col == 60 and not sheet.cell_value(row,col):
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
                                contracts['department_id'] = department_id.id
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
                                contracts['job_id'] = job_id.id
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
                                contracts['company_id'] = company_id.id
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
                                contracts['type_salary'] = str(type_salary_50)
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
                                    contracts['employee'] = '%s %s' %(name, last_name)
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
                        if col in [60]:
                            payroll_period = dict(self.env['hr.employee']._fields.get('payroll_period').selection)
                            cell_value = self.float_to_string(sheet.cell_value(row,col))
                            value = self.check_selection1(cell_value.strip(), payroll_period)
                            if value:
                                lines['payroll_period'] = value
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), cell_value, str(row+1),list(payroll_period.keys())))
                    if bank_data:
                        lines['bank_account_ids'] = [(0, 0, bank_data)]
                    # Contracts Data
                    if self.create_contract:
                        if col in [50]:
                            monthly_salary = self.validate_float(sheet.cell_value(row,col))
                            if not monthly_salary:
                                msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                        if col in [61]:
                            value = self.float_to_string(sheet.cell_value(row,col)).strip()
                            domain = [('name','=', value)]
                            company_assimilated_id = self.check_field_many2one(domain, model='res.company')
                            if company_assimilated_id:
                                if len(company_assimilated_id) > 1:
                                    msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                                else:
                                    lines['company_id'] = company_id.id
                                    contracts['company_assimilated_id'] = company_assimilated_id.id
                            else:
                                msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                        if col in [62]:
                            type_contract = self.float_to_string(sheet.cell_value(row,col)).strip()
                            domain = [('code','=', type_contract)]
                            type_contract_id = self.check_field_many2one(domain, model='hr.contract.type')
                            if not type_contract_id:
                                msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                        if col in [63]:
                            with_antiquity = self.check_selection(sheet.cell_value(row,col), TYPE_CONTRACT)
                            if with_antiquity:
                                type_id = type_contract_id.filtered(lambda t: t.type == with_antiquity and t.report_id)
                                if not type_id:
                                    msg_not_found.append('TIPO DE CONTRATO Y %s con las claves ( %s y %s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), type_contract, sheet.cell_value(row,col), str(row+1)))
                                else:
                                    contracts['with_antiquity'] = with_antiquity
                                    contracts['type_id'] = type_id.id
                            else:
                                msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1),list(TYPE_CONTRACT.keys())))
                        if col in [64]:
                            try:
                                is_datetime_start = sheet.cell_value(row,col) % 1 != 0.0
                                dt_start = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row,col), book.datemode))
                                date_start = dt_start.strftime(DEFAULT_SERVER_DATE_FORMAT)
                                contracts['date_start'] = date_start
                            except:
                                msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                        if col in [65]:
                            if sheet.cell_value(row,col):
                                try:
                                    is_datetime_end = sheet.cell_value(row,col) % 1 != 0.0
                                    dt_end = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row,col), book.datemode))
                                    date_end = dt_end.strftime(DEFAULT_SERVER_DATE_FORMAT)
                                    contracts['date_end'] = date_end
                                except:
                                    msg_not_format.append('%s del valor (%s) en la fila %s (INGRESE FECHAS). \n' %(sheet.cell_value(head,col).upper(), sheet.cell_value(row,col), str(row+1)))
                        if col in [66]:
                            if with_antiquity == 'with_seniority':
                                try:
                                    is_datetime_prev = sheet.cell_value(row,col) % 1 != 0.0
                                    dt_prev = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row,col), book.datemode))
                                    date_prev = dt_prev.strftime(DEFAULT_SERVER_DATE_FORMAT)
                                    contracts['previous_contract_date'] = date_prev
                                except:
                                    msg_required.append('%s en la fila %s. \n' %(sheet.cell_value(head,col).upper(), str(row+1)))
                        if col in [67]:
                            structure_ss = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if structure_ss:
                                domain = [('name','=', structure_ss)]
                                structure_ss_id = self.check_field_many2one(domain, model='hr.structure.types')
                                if structure_ss_id:
                                    if len(structure_ss_id) > 1:
                                        msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                                    else:
                                        contracts['structure_ss_id'] = structure_ss_id.id
                                else:
                                    msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), structure_ss, str(row+1)))
                        if col in [68]:
                            structure_as = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if structure_as:
                                domain = [('name','=', structure_as)]
                                structure_as_id = self.check_field_many2one(domain, model='hr.structure.types')
                                if structure_as_id:
                                    if len(structure_as_id) > 1:
                                        msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                                    else:
                                        contracts['structure_as_id'] = structure_as_id.id
                                else:
                                    msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), structure_as, str(row+1)))
                        if col in [69]:
                            structure_free = self.float_to_string(sheet.cell_value(row,col)).strip()
                            if structure_free:
                                domain = [('name','=', structure_free)]
                                structure_free_id = self.check_field_many2one(domain, model='hr.structure.types')
                                if structure_free_id:
                                    if len(structure_free_id) > 1:
                                        msg_more.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), value, str(row+1)))
                                    else:
                                        contracts['structure_free_id'] = structure_free_id.id
                                else:
                                    msg_not_found.append('%s con la clave (%s) en la fila %s. \n' %(sheet.cell_value(head,col).upper(), structure_free, str(row+1)))
                        if col in [70]:
                            contracting_regime_dic = dict(self.env['hr.employee']._fields.get('contracting_regime').selection)
                            contracting_regime_value = self.float_to_string(sheet.cell_value(row,col))
                            if contracting_regime_value:
                                contracting_regime = self.check_selection1(contracting_regime_value.strip(), contracting_regime_dic)
                                if contracting_regime:
                                    contracts['contracting_regime'] = contracting_regime
                                else:
                                    msg_not_found.append('%s con la clave (%s) en la fila %s. POSIBLES VALORES %s \n' %(sheet.cell_value(head,col).upper(), contracting_regime_value, str(row+1),list(contracting_regime_dic.keys())))
                
                
                monthly_salary_emp = lines['monthly_salary'] if 'monthly_salary' in lines else 0
                wage_salaries_emp = lines['wage_salaries'] if 'wage_salaries' in lines else 0
                free_salary_emp = lines['free_salary'] if 'free_salary' in lines else 0
                contracts['monthly_salary'] = monthly_salary_emp
                contracts['wage_salaries'] = wage_salaries_emp
                contracts['free_salary'] = free_salary_emp
                lines['contract_ids'] = self._prepare_contract(contracts)
                
                # ~ lines['contract_ids'] = 'Aqui va todos los contratos'
                print (lines)
                # ~ print (monthly_salary_emp)
                # ~ print (wage_salaries_emp)
                # ~ print (free_salary_emp)
                print ('lines')
                
                employees.append(lines)
            
            monthly_salary = 0
            wage_salaries = 0
            free_salary = 0
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
    
    def _prepare_contract(self, contracts_rows):
        """ Function doc """
        # ~ contracts_rows['type_id'] = [(0, 0, bank_data)]
        contracts = []
        contract_data = {}
        if self.create_contract:
            print (contracts_rows)
            if contracts_rows['monthly_salary'] <= 0:
                raise UserError(_('Please indicate the Monthly Salary in row %s') %contracts_rows['row'])
            total_salaries = contracts_rows['wage_salaries'] + contracts_rows['free_salary']
            if total_salaries > contracts_rows['monthly_salary']:
                raise UserError(_(
                    'The amount of wages and salaries plus the free amount cannot exceed the monthly salary.'))
            # ~ if contracts_rows['type_salary'] == 'gross':
            if contracts_rows['wage_salaries'] > 0:
                contract_data = {
                    'name': '%s - Sueldos y Salarios' %contracts_rows['employee'],
                    'department_id': contracts_rows['department_id'],
                    'job_id': contracts_rows['job_id'],
                    'wage': contracts_rows['wage_salaries'],
                    'contracting_regime': '02',
                    'company_id': contracts_rows['company_id'],
                    'type_id':contracts_rows['type_id'],
                    'date_start': contracts_rows['date_start'],
                    'date_end': contracts_rows['date_end'],
                    # ~ 'bank_account_id': bank_account_id,
                    'structure_type_id': contracts_rows['structure_ss_id'],
                    'state': 'open',
                }
                contracts.append((0, 0, contract_data))
            if contracts_rows['wage_salaries'] < contracts_rows['monthly_salary'] and contracts_rows['free_salary'] <= 0:
                assimilated_salary = round(contracts_rows['monthly_salary'] - (contracts_rows['wage_salaries'] + contracts_rows['free_salary']), 2)
                contract_data = {
                    'name': '%s - Asimilado' %contracts_rows['employee'],
                    'department_id': contracts_rows['department_id'],
                    'job_id': contracts_rows['job_id'],
                    'wage': assimilated_salary,
                    'contracting_regime': contracts_rows['contracting_regime'],
                    'company_id': contracts_rows['company_assimilated_id'],
                    'type_id':contracts_rows['type_id'],
                    'date_start': contracts_rows['date_start'],
                    'date_end': contracts_rows['date_end'],
                    'structure_type_id': contracts_rows['structure_as_id'],
                    'state': 'open',
                }
                contracts.append((0, 0, contract_data))
            if contracts_rows['wage_salaries'] < contracts_rows['monthly_salary'] and contracts_rows['free_salary'] > 0:
                contract_data = {
                    'name': '%s - Libre' %contracts_rows['employee'],
                    'department_id': contracts_rows['department_id'],
                    'job_id': contracts_rows['job_id'],
                    'wage': contracts_rows['free_salary'],
                    'contracting_regime': '05',
                    # ~ 'company_id': contracts_rows['company_assimilated_id'],
                    'type_id':contracts_rows['type_id'],
                    'date_start': contracts_rows['date_start'],
                    'date_end': contracts_rows['date_end'],
                    # ~ 'bank_account_id': bank_account_id,
                    'structure_type_id': contracts_rows['structure_free_id'],
                    'state': 'open',
                }
                contracts.append((0, 0, contract_data))
            assimilated_salaryw = round(contracts_rows['monthly_salary'] - (contracts_rows['wage_salaries'] + contracts_rows['free_salary']), 2)
            if assimilated_salaryw < contracts_rows['monthly_salary'] and contracts_rows['free_salary']  > 0:
                contract_data = {
                    'name': '%s - Asimilado ss' %contracts_rows['employee'],
                    'department_id': contracts_rows['department_id'],
                    'job_id': contracts_rows['job_id'],
                    'wage': assimilated_salaryw,
                    'contracting_regime': contracts_rows['contracting_regime'],
                    'company_id': contracts_rows['company_assimilated_id'],
                    'type_id':contracts_rows['type_id'],
                    'date_start': contracts_rows['date_start'],
                    'date_end': contracts_rows['date_end'],
                    'structure_type_id': contracts_rows['structure_as_id'],
                    'state': 'open',
                }
                print (contract_data)
                contracts.append((0, 0, contract_data))
        return contracts
        
    
    @api.multi
    def clean_file_ids(self):
        self.ensure_one()
        self.file_ids = False
        return {"type":"ir.actions.do_nothing"}

    @api.multi
    def import_data(self):
        if not self.file_name:
            raise UserError('Do not load with without a file, or with a file with incorrect data.')
        employees = self.read_document()
        if employees:
             for emp in employees:
                self.env['hr.employee'].create(emp).sudo()
        return {'type': 'ir.actions.client', 'tag': 'reload', 'res_model':'hr.employee', 'context':"{'model': 'hr.employee'}"}
