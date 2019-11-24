# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    structure_type_id = fields.Many2one(
                                        'hr.structure.types',
                                        string="Structure Types")
     

