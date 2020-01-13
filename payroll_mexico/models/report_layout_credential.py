# -*- coding: utf-8 -*-

import datetime
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.addons.payroll_mexico.pyfiscal.generate_company import GenerateRfcCompany


class View(models.Model):
    _name = "report.layout.credential"
    _description = 'Report Layout'

    view_id = fields.Many2one('ir.ui.view', 'Document Template', required=True)
    image = fields.Char(string="Preview image src")
    pdf = fields.Char(string="Preview pdf src")