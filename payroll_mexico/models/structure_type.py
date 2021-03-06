# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StructureTypes(models.Model):
    _name = 'hr.structure.types'

    name = fields.Char(string='Name',required=True)
    country_id = fields.Many2one(
                                'res.country',
                                default=lambda self: self.env['res.company']._company_default_get().country_id,
                                string="Country",
                                required=True)
    company_id = fields.Many2one(
                            'res.company',
                            string = "Company",
                            default=lambda self: self.env['res.company']._company_default_get(),
                            required=True)
    structure_ids=fields.One2many(
                                'hr.payroll.structure',
                                'structure_type_id',
                                string="Structure")


class HrPayrollStructure(models.Model):
     _inherit = 'hr.payroll.structure'

     #Columns
     structure_type_id = fields.Many2one('hr.structure.types',string="Structure Types")
