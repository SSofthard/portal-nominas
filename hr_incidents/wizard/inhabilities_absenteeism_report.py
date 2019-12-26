# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import time
import datetime
import calendar
import pytz
import dateutil
import base64
import xlsxwriter

from xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell
from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo.tools.mimetypes import guess_mimetype
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, pycompat
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY


class InhabilityAbsenteeismReport(models.TransientModel):
    _name = "hr.leave.inhability.absenteeism.wizard"
    _description = "Inabilities & Absenteeism"

    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id)
    group_id = fields.Many2one('hr.group', "Group", required=True)
    employer_register_id = fields.Many2one('res.employer.register', "Employer Register", required=False)
    department_ids = fields.Many2many('hr.department', 'hr_leave_inhability_dept_rel', 'inhability_id', 'dept_id', string='Department(s)')
    job_ids = fields.Many2many('hr.job', 'hr_leave_inhability_job_rel', 'inhability_id', 'job_id', string='Job Position')
    date_from = fields.Date(
        'Start Date', index=True, copy=False, required=True,
        default=date.today())
    date_to = fields.Date(
        'End Date', index=True, copy=False, required=True,
        default=date.today())
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free'),
        ], string='Contracting Regime', default="2")

    @api.multi
    def report_print(self, data):
        leaves = {}
        employee_data = {}
        
        self.ensure_one()
        domain = [('employee_id.group_id','=',self.group_id.id),('request_date_from','>=',self.date_from),('request_date_to','<=',self.date_to)]
        if self.department_ids:
            domain += [('employee_id.department_id','in',self.department_ids.ids)]
        if self.job_ids:
            domain += [('employee_id.department_id','in',self.job_ids.ids)]
        if self.employer_register_id:
            domain += [('employee_id.employer_register_id','=',self.employer_register_id.id)]
        if self.contracting_regime:
            domain += [('contract_id.contracting_regime','=',self.contracting_regime)]
        leaves_ids = self.env['hr.leave'].search(domain)
        if not leaves_ids:
            raise ValidationError(_('No se encontraron resultados, para los parámetros dados.'))
        employees_ids = leaves_ids.mapped('employee_id')
        for employee in employees_ids:
            leaves_data = []
            for leave in leaves_ids:
                if employee.id == leave.employee_id.id:
                    leaves_data.append({
                        'type_inhability': leave.type_inhability_id.code,
                        'folio': leave.folio,
                        'duration': leave.number_of_days,
                        'request_date_from': leave.request_date_from,
                        'request_date_to': leave.request_date_to,
                        'holiday_status_id': dict(leave._fields['time_type']._description_selection(self.env)).get(leave.holiday_status_id.time_type),
                        'type_inhability_id': leave.type_inhability_id.name or '',
                        'inhability_classification_id': leave.inhability_classification_id.name or '',
                        'inhability_category_id': leave.inhability_category_id.name or '',
                        'inhability_subcategory_id': leave.inhability_subcategory_id.name or '',
                    })
            employee_data[employee.id] = {
                'enrollment': employee.enrollment,
                'ssnid': employee.ssnid,
                'name': employee.name_get()[0][1],
                'rfc': employee.rfc,
                'curp': employee.curp,
                'date_admission': self.env['hr.contract'].search([('employee_id','=',employee.id),('contracting_regime','=','2')], limit=1).date_start or '',
                'leave': leaves_data,
            }
        
        leaves['date_from'] = self.date_from
        leaves['date_to'] = self.date_to
        leaves['employer_register_id'] = self.employer_register_id.employer_registry.upper() if self.employer_register_id else ''
        leaves['company'] = self.employer_register_id.company_id.business_name
        leaves['rfc'] = self.employer_register_id.company_id.rfc
        leaves['total_employees'] = len(employees_ids)
        leaves['employee_data'] = employee_data
        data={
            'leaves_data':leaves
        }
        return self.env.ref('hr_incidents.action_report_inhability_absenteeism').with_context(from_transient_model=True).report_action(self, data=data)

    @api.multi
    def get_line_for_report(self):
        leaves = {}
        employee_data = {}
        
        self.ensure_one()
        domain = [('employee_id.group_id','=',self.group_id.id),('request_date_from','>=',self.date_from),('request_date_to','<=',self.date_to)]
        if self.department_ids:
            domain += [('employee_id.department_id','in',self.department_ids.ids)]
        if self.job_ids:
            domain += [('employee_id.department_id','in',self.job_ids.ids)]
        if self.employer_register_id:
            domain += [('employee_id.employer_register_id','=',self.employer_register_id.id)]
        if self.contracting_regime:
            domain += [('contract_id.contracting_regime','=',self.contracting_regime)]
        leaves_ids = self.env['hr.leave'].search(domain)
        if not leaves_ids:
            raise ValidationError(_('No se encontraron resultados, para los parámetros dados.'))
        employees_ids = leaves_ids.mapped('employee_id')
        leaves_data = []
        for employee in employees_ids:
            
            for leave in leaves_ids:
                if employee.id == leave.employee_id.id:
                    leaves_data.append({
                        'employee_id': employee.id,
                        'enrollment': employee.enrollment,
                        'ssnid': employee.ssnid,
                        'name': employee.name_get()[0][1],
                        'rfc': employee.rfc,
                        'curp': employee.curp,
                        'date_admission': self.env['hr.contract'].search([('employee_id','=',employee.id),('contracting_regime','=','2')], limit=1).date_start or '',
                        # ~ 'leave': leaves_data,
                        'type_inhability': leave.type_inhability_id.code,
                        'folio': leave.folio,
                        'duration': leave.number_of_days,
                        'request_date_from': leave.request_date_from,
                        'request_date_to': leave.request_date_to,
                        'holiday_status_id': dict(leave._fields['time_type']._description_selection(self.env)).get(leave.holiday_status_id.time_type),
                        'type_inhability_id': leave.type_inhability_id.name or '',
                        'inhability_classification_id': leave.inhability_classification_id.name or '',
                        'inhability_category_id': leave.inhability_category_id.name or '',
                        'inhability_subcategory_id': leave.inhability_subcategory_id.name or '',
                    })
            employee_data[employee.id] = {
                'enrollment': employee.enrollment,
                'ssnid': employee.ssnid,
                'name': employee.name_get()[0][1],
                'rfc': employee.rfc,
                'curp': employee.curp,
                'date_admission': self.env['hr.contract'].search([('employee_id','=',employee.id),('contracting_regime','=','2')], limit=1).date_start or '',
                'leave': leaves_data,
            }
        
        # ~ leaves['date_from'] = self.date_from
        # ~ leaves['date_to'] = self.date_to
        # ~ leaves['employer_register_id'] = self.employer_register_id.employer_registry.upper() if self.employer_register_id else ''
        # ~ leaves['company'] = self.employer_register_id.company_id.business_name
        # ~ leaves['rfc'] = self.employer_register_id.company_id.rfc
        # ~ leaves['total_employees'] = len(employees_ids)
        # ~ leaves['employee_data'] = employee_data
        # ~ data={
            # ~ 'leaves_data':leaves
        # ~ }
        return leaves_data

    def prepare_header(self):
        header = [
                {'name': 'Matrícula del trabajador', 'larg': 10, 'col': {}},
                {'name': 'N.S.S.', 'larg': 10, 'col': {}},
                {'name': 'Nombre del trabajador', 'larg': 40, 'col': {}},
                {'name': 'R.F.C.', 'larg': 10, 'col': {}},
                {'name': 'CURP', 'larg': 10, 'col': {}},
                {'name': 'Fecha de Ingreso', 'larg': 15, 'col': {}},
                {'name': 'Tipo de Incidencia', 'larg': 5, 'col': {}},
                {'name': 'Folio', 'larg': 10, 'col': {}},
                {'name': 'Duración', 'larg': 5, 'col': {}},
                {'name': 'Fecha Inicial', 'larg': 15, 'col': {}},
                {'name': 'Fecha Final', 'larg': 15, 'col': {}},
                {'name': 'Rama', 'larg': 20, 'col': {}},
                {'name': 'Sub Rama', 'larg': 20, 'col': {}},
                {'name': 'Tipo', 'larg': 20, 'col': {}},
                {'name': 'Sub Tipo', 'larg': 20, 'col': {}},
            ]
        return header

    @api.multi
    def action_print_report_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        company = self.env.user.company_id
        num_format = company.currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'text_wrap': True, 'bold': True, 'border': 1, 'top': 1, 'font_size': 8, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#CCCCFF', 'font_color':'#3341BE', 'font_name':'MS Sans Serif'})
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
        
        f_name = 'Reporte de Incapacidades y Ausentismos: Del %s al %s' %(self.date_from, self.date_to)
        print_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), fields.Datetime.now()).strftime(('%s %s') % (date_format, time_format)),
        sheet = workbook.add_worksheet(f_name)
        
        row = 5
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
            sheet.merge_range('C4:D4','', report_format)
            sheet.merge_range('E4:F4','', report_format)
            sheet.write(0, 0, _('Nombre de la Empresa: %s') % company.name, report_format)
            sheet.write(1, 0, _('Fecha y hora de la generación del Reporte: %s') % print_time, report_format)
            sheet.write(2, 0, _('Título de Reporte: %s') %f_name, report_format)
            sheet.write(3, 0, _('Registro patronal: %s') % company.rfc, report_format)
            sheet.write(3, 2, _('Razón Social: %s') % company.business_name, report_format)
            sheet.write(3, 4, _('R.F.C.: %s') % company.rfc, report_format)
        
        if f_name:
            _header_sheet(sheet)
            
            all_lines = self.get_line_for_report()
            if all_lines:
                for j, h in enumerate(self.prepare_header()):
                    sheet.write(4, j, h['name'], header_format)
                    sheet.set_column(4, j, h['larg'])
                    row = 4
                    row += 1
                    start_row = row
                    employees = []
                    for i, line in enumerate(all_lines):
                        if line.get('employee_d', '') not in employees:
                            employees.append(line.get('employee_d', ''))
                        i += row
                        sheet.write(i, 0, line.get('enrollment', ''), report_format2) #Matrícula del trabajador
                        sheet.write(i, 1, line.get('ssnid', '') or '-', report_format) #NSS
                        sheet.write(i, 2, line.get('name', '') or '-', report_format2) # Nombre del trabajador
                        sheet.write(i, 3, line.get('rfc', '') or '-', report_format2) #RFC
                        sheet.write(i, 4, line.get('curp', '') or '-', report_format2) #CURP
                        sheet.write(i, 5, get_date_format(line.get('date_admission', '')) or '-', report_format2) #Fecha de Ingreso
                        sheet.write(i, 6, line.get('type_inhability', '') or '-', report_format2) #Tipo de Incidencia
                        sheet.write(i, 7, line.get('folio', '') or '-', report_format2) #Folio
                        sheet.write(i, 8, line.get('duration', '') or '-', report_format2) #Duración
                        sheet.write(i, 9, get_date_format(line.get('request_date_from', '')) or '-', report_format2) # Fecha Inicial
                        sheet.write(i, 10, get_date_format(line.get('request_date_to', '')) or '-', report_format2) #Fecha Final
                        sheet.write(i, 11, line.get('holiday_status_id', '') or '-', report_format2) #Rama
                        sheet.write(i, 12, line.get('type_inhability_id', '') or '-', report_format2) #Sub Rama
                        sheet.write(i, 13, line.get('inhability_classification_id', '') or '-', report_format2) #Tipo
                        sheet.write(i, 14, line.get('inhability_category_id', '') or '-', report_format2) #Sub Tipo
                        
                    row = i
                    start_range = xl_rowcol_to_cell(i+2, 0)
                    end_range = xl_rowcol_to_cell(i+2, 1)
                    merg_range = "{:s}:{:s}".format(start_range, end_range)
                    sheet.merge_range(merg_range,'', report_format)
                    sheet.write(i+2, 0, _('Total de trabajadores: %s') % len(employees), formula_format)
                    
        sheet.set_row(4, 40)
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
