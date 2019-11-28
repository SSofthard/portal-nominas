# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrPerceptions(models.Model):
    _name = 'hr.perceptions'
    _rec_name= 'perception_type'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, states={'paid': [('readonly', True)]})
    perception_import = fields.Float('Import', states={'paid': [('readonly', True)]})
    type_id = fields.Many2one('hr.type.perceptions', string='Type perceptions', required=True, states={'paid': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve'),
        ('paid', 'Paid')], string='Status', readonly=True, default='draft')
    perception_type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Perceptions or Deductions', related= 'type_id.perception_type', readonly=True, states={'paid': [('readonly', True)]})

    @api.multi
    def button_approve(self):
        return self.write({'state': 'approve'})
        
    @api.multi
    def button_paid(self):
        return self.write({'state': 'paid'})

class HrPerceptions(models.Model):
    _name = 'hr.type.perceptions'
    _rec_name = 'code'
    
    name = fields.Char('Description')
    code = fields.Char('Code', required=True)
    perception_type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Perceptions type')
