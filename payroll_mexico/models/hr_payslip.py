# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class HrInputs(models.Model):
    _name = 'hr.inputs'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, states={'paid': [('readonly', True)]})
    amount = fields.Float('Amount', states={'paid': [('readonly', True)]}, digits=(16, 2))
    
    
    input_id = fields.Many2one('hr.rule.input', string='Type', required=True, states={'paid': [('readonly', True)]})
    
    
    state = fields.Selection([
        ('approve', 'Approve'),
        ('paid', 'Paid')], string='Status', readonly=True, default='approve')
        
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', related= 'input_id.type', readonly=True, states={'paid': [('readonly', True)]}, store=True)
    group_id = fields.Many2one('hr.group', "Group", related= 'employee_id.group_id', readonly=True, states={'paid': [('readonly', True)]}, store=True)



class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input'
    
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', required=True)

