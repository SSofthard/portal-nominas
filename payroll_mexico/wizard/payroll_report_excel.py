# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PayslipExportExcel(models.TransientModel):
    _name = "hr.payslip.run.export.excel"
    _description = 'Exportar Excel'

    excel_file = fields.Binary('Descargar')
    file_name = fields.Char('Descargar')
