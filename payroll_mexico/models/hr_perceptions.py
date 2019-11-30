# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class HrPerceptions(models.Model):
    _name = 'hr.perceptions'
    _rec_name= 'perception_type'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, states={'paid': [('readonly', True)]})
    perception_import = fields.Float('Import', states={'paid': [('readonly', True)]}, digits=(16, 2))
    type_id = fields.Many2one('hr.type.perceptions', string='Type', required=True, states={'paid': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve'),
        ('paid', 'Paid')], string='Status', readonly=True, default='draft')
    perception_type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Perceptions or Deductions', related= 'type_id.perception_type', readonly=True, states={'paid': [('readonly', True)]}, store=True)
    group_id = fields.Many2one('hr.group', "Group", related= 'employee_id.group_id', readonly=True, states={'paid': [('readonly', True)]}, store=True)

    @api.multi
    def button_approve(self):
        return self.write({'state': 'approve'})
        
    @api.multi
    def button_paid(self):
        return self.write({'state': 'paid'})

class HrPerceptions(models.Model):
    _name = 'hr.type.perceptions'
    
    name = fields.Char('Description')
    prefix = fields.Char('Prefix')
    code = fields.Char('Code', required=True)
    perception_type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Perceptions or Deductions')
    
    @api.onchange('perception_type')
    def onchange_perception_type(self):
        for record in self:
            if record.perception_type == 'perception':
                record.prefix = 'P'
            if record.perception_type == 'deductions':
                record.prefix = 'D'
                
    @api.onchange('pre','code')
    def onchange_code(self):
        for record in self:
            if record.prefix:
                record.code = record.prefix + record.code
            
    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('code', operator, name)]
        code = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(code).name_get()

    _sql_constraints = [
        ('code','UNIQUE (prefix,code)', 'The code must be unique.')]
