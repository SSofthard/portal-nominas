# -*- coding: utf-8 -*-

import io
import base64

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class payrollDispersionTxt(models.TransientModel):
    _name = "payroll.dispersion.txt"
    _description = 'Exportar TXT Movimientos Afiliatorios'

    #Columns
    txt_file = fields.Binary('Descargar')
    file_name = fields.Char('Descargar')


class payrollDispersionTxtWizard(models.TransientModel):
    _name = "payroll.dispersion.txt.wizard"
    _description = 'Reporte Movimientos Afiliatorios'

    #Columns
    account_type = fields.Selection([
                                    ('001','Cuenta'),
                                    ('040','CLABE'),
                                    ('003','Tarjeta de débito'),
                                     ], "Tipo de cuenta", required=False)
    bank_id = fields.Many2one('res.bank', "Bank", required=False)


    @api.multi
    def report_print(self):
        '''
        Este metodo es para imprimir el txt de los movimientso afiliatorios
        '''
        output = io.BytesIO()
        payslip_run_id = self.env.context.get('active_id')
        payslip_run = self.env['hr.payslip.run'].browse([payslip_run_id])
        f_name = 'Dispersion %s' % (payslip_run.name)
        slip_ids = payslip_run.slip_ids
        if self.bank_id:
            slip_ids = slip_ids.filtered(
                    lambda slip: slip.employee_id.mapped('bank_account_ids').filtered(
                        lambda account: account.predetermined).bank_id.id == self.bank_id.id)
        if self.account_type:
            slip_ids = slip_ids.filtered(
            lambda slip: slip.employee_id.mapped('bank_account_ids').filtered(
                lambda account: account.predetermined).account_type == self.account_type)
        content = ''
        if not slip_ids:
            raise UserError('No existen registros para los filtros definidos')
        for payslip in slip_ids:
            bank_account = payslip.employee_id.bank_account_ids.filtered(lambda account: account.predetermined)
            content+='%s\tAR\t%s\t%s\t%s\t%s\t%s\t\t\tx\n%s\tAC\t\t\t\t\t\t%s\t%s\t%s\t%s\n' % (
                payslip.employee_id.barcode.ljust(8),
                payslip.employee_id.complete_name.ljust(36),
                payslip.employee_id.rfc.ljust(13),
                payslip.employee_id.personal_phone.ljust(15) if payslip.employee_id.personal_phone else ''.ljust(15),
                'R Romo',
                payslip.employee_id.work_email.ljust(20),
                payslip.employee_id.barcode.ljust(8),
                bank_account.account_type,
                'PESOS',
                bank_account.reference.ljust(4),
                bank_account.bank_account.ljust(18)
            )
        data = base64.encodebytes(bytes(content, 'utf-8'))
        export_id = self.env['payroll.dispersion.txt'].create(
            {'txt_file': data, 'file_name': f_name + '.txt'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payroll.dispersion.txt',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': export_id.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.multi
    def report_print_payments(self):
        '''
        Este metodo es para imprimir el txt de los movimientso afiliatorios
        '''
        output = io.BytesIO()
        payslip_run_id = self.env.context.get('active_id')
        payslip_run = self.env['hr.payslip.run'].browse([payslip_run_id])
        f_name = 'Dispersion %s' % (payslip_run.name)
        slip_ids = payslip_run.slip_ids
        if self.bank_id:
            slip_ids = slip_ids.filtered(
                    lambda slip: slip.employee_id.mapped('bank_account_ids').filtered(
                        lambda account: account.predetermined).bank_id.id == self.bank_id.id)
        if self.account_type:
            slip_ids = slip_ids.filtered(
            lambda slip: slip.employee_id.mapped('bank_account_ids').filtered(
                lambda account: account.predetermined).account_type == self.account_type)
        content = ''
        if not slip_ids:
            raise UserError('No existen registros para los filtros definidos')
        count = 0
        for payslip in slip_ids:
            company_bank_account = payslip.company_id.bank_account_ids.filtered(lambda account: account.predetermined)
            bank_account = payslip.employee_id.bank_account_ids.filtered(lambda account: account.predetermined)
            operation = ''
            if bank_account.account_type == '001':
                operation = '02'
            if bank_account.account_type == '040':
                operation = '04'
            content+='%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                operation,
                payslip.employee_id.barcode.ljust(13),
                company_bank_account.bank_account.ljust(10) if company_bank_account else ''.ljust(10),
                bank_account.bank_account.ljust(20),
                payslip.line_ids.filtered(lambda line: line.category_id.code == 'NET').total,
                payslip.payment_date.strftime('%d%m%y'),
                'pago',
                payslip.company_id.rfc.ljust(13),
                payslip.amount_tax,
                payslip.payment_date.strftime('%d%m%Y'),
                'x',
                '0',
            )
        data = base64.encodebytes(bytes(content, 'utf-8'))
        export_id = self.env['payroll.dispersion.txt'].create(
            {'txt_file': data, 'file_name': f_name + '.txt'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payroll.dispersion.txt',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': export_id.id,
            'views': [(False, 'form')],
            'target': 'new',
        }