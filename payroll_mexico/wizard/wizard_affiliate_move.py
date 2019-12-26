# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class hrEmployeeAffiliateExportTxt(models.TransientModel):
    _name = "hr.employee.affiliate.export.txt"
    _description = 'Exportar txt'

    #Columns
    txt_file = fields.Binary('Descargar')
    file_name = fields.Char('Descargar')
