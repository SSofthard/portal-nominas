# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class LaboralInhability(models.Model):
    _name = "hr.leave.inhability"
    _description = 'Inhability type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    classification_ids = fields.One2many('hr.leave.classification', 'inhability_id', string='Inhability classification',)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [('code_unique', 'unique(Code)', "the code must be unique")]

class LeaveClassification(models.Model):
    _name = "hr.leave.classification"
    _description = 'Inhability classification'

    inhability_id = fields.Many2one('hr.leave.inhability', string='Inhability', index=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    category_ids = fields.One2many('hr.leave.category', 'classification_id', string='Inhability categories',)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [('code_unique', 'unique(Code)', "the code must be unique")]


class LeaveCategory(models.Model):
    _name = "hr.leave.category"
    _description = 'Inhability subcategories'

    classification_id = fields.Many2one('hr.leave.classification', string='classification', index=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='code', required=True)
    subcategory_ids = fields.One2many('hr.leave.subcategory', 'category_id', string='Inhability Subcategories',)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [('code_unique', 'unique(Code)', "the code must be unique")]


class LeaveSubcategory(models.Model):
    _name = "hr.leave.subcategory"
    _description = 'Inhability subcategories'

    category_id = fields.Many2one('hr.leave.category', string='Category', index=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='code', required=True)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [('code_unique', 'unique(Code)', "the code must be unique")]


