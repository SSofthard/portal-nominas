# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Contract(models.Model):

    _inherit = 'hr.contract'

    structure_type_id = fields.Many2one('hr.payroll.structure.types',string="Structure Types")

