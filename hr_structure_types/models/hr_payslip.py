# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date, datetime, time


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    structure_type_id = fields.Many2one(
                                    'hr.structure.types',
                                    related="contract_id.structure_type_id",
                                    string="Structure Types")
                                    


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    #Columns
    group_id = fields.Many2one('hr.group', string="Empresa")
