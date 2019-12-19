# -*- coding: utf-8 -*-

from io import BytesIO
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


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class PayslipExcel(models.TransientModel):
    _name = "hr.payslip.run.excel"
    _description = "Reporte de Nómina Excel"

    #Columns
    payslip_run_id = fields.Many2one('hr.payslip.run', index=True, string='Nómina')

    @api.multi
    def print_report(self):
        self.ensure_one()
        payroll_dic = {}
        employees = []
        total = 0
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        company = self.payslip_run_id.mapped('slip_ids').mapped('company_id')
        payroll_dic['company_name'] = company.name
        date_start = '%s/%s/%s' %(self.payslip_run_id.date_start.strftime("%d"), self.payslip_run_id.date_start.strftime("%b").title(), self.payslip_run_id.date_start.strftime("%Y"))
        date_end = '%s/%s/%s' %(self.payslip_run_id.date_end.strftime("%d"), self.payslip_run_id.date_end.strftime("%b").title(), self.payslip_run_id.date_end.strftime("%Y"))
        payroll_dic['date_start'] = date_start
        payroll_dic['date_end'] = date_end
        payroll_dic['period'] = 'Periodo de Pago: Del %s al %s' %(date_start, date_end)
        f_name = payroll_dic.get('period') + '.xlsx'
        # ~ slip_ids = self.payslip_run_id.mapped('slip_ids')  #.filtered(lambda r: r.salary_rule_id == self.rule_id.id)
        # ~ for slip in slip_ids:
            # ~ total += sum(slip.line_ids.filtered(lambda r: r.salary_rule_id.id == self.rule_id.id).mapped('total'))
            # ~ for line in slip.line_ids:
                # ~ if line.salary_rule_id.id == self.rule_id.id:
                    # ~ employees.append({
                        # ~ 'enrollment': slip.employee_id.enrollment,
                        # ~ 'name': slip.employee_id.name_get()[0][1],
                        # ~ 'rfc': line.total,
                        # ~ 'curp': slip.contra,
                        # ~ 'curp': line.total,
                    # ~ })
        # ~ payroll_dic['employees'] = employees
        # ~ payroll_dic['total'] = total
        workbook.close()
        xlsx_data = output.getvalue()
        export_id = self.env['hr.payslip.run.export.excel'].create({ 'excel_file': base64.encodestring(xlsx_data),'file_name': f_name})
        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'hr.payslip.run.export.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class PayslipExportExcel(models.TransientModel):
    _name = "hr.payslip.run.export.excel"
    _description = 'Exportar Excel'

    excel_file = fields.Binary('Descargar')
    file_name = fields.Char('Descargar')
