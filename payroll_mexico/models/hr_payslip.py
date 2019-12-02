# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class HrInputs(models.Model):
    _name = 'hr.inputs'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, states={'paid': [('readonly', True)]})
    amount = fields.Float('Amount', states={'paid': [('readonly', True)]}, digits=(16, 2))
    
    
    input_id = fields.Many2one('hr.rule.input', string='Input', required=True, states={'paid': [('readonly', True)]})
    
    
    state = fields.Selection([
        ('approve', 'Approved'),
        ('paid', 'Reported on payroll')], string='Status', readonly=True, default='approve')
        
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', related= 'input_id.type', readonly=True, states={'paid': [('readonly', True)]}, store=True)
    group_id = fields.Many2one('hr.group', "Group", related= 'employee_id.group_id', readonly=True, states={'paid': [('readonly', True)]}, store=True)



class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input'
    
    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|',('code', operator, name),('name', operator, name)]
        rule_input = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(rule_input).name_get()
    
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', required=True)

