# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class HrPerceptionsWizard(models.Model):
    _name = 'hr.perceptions.wizard'
    
    #Columns
    group_id = fields.Many2one('hr.group', "Group", store=True, required=True)
    perception_type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Perceptions or Deductions', store=True, required=True)
    all_or_only = fields.Selection([
        ('all', 'All'),
        ('only', 'Only')], string='All or Only', store=True, default='all')
    type_id = fields.Many2one('hr.type.perceptions', string='Type')
    employee_id = fields.Many2one('hr.employee', string='Employees')
    
    
    
    def report_print(self, data):
        print ('Hola mundo')
        print ('Hola mundo')
        print ('Hola mundo')
        print ('Hola mundo')
        return self.env.ref('hr_perceptions.report_hr_perceptions_wizard').report_action(self, data=data)
