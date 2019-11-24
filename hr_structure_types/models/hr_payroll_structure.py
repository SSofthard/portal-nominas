# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrPayrollStructure(models.Model):
     _inherit = 'hr.payroll.structure'

     
     structure_type_id = fields.Many2one('hr.structure.types',string="Structure Types")
    

