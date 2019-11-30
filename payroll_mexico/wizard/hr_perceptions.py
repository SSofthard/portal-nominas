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
    employee_ids = fields.Many2many('hr.employee', 'perceptions_emp_rel', 'perceptions_id', 'employee_id', string='Employees')

    @api.onchange('group_id')
    def search_employee(self):
         employee = self.env['hr.employee'].search([('group_id', '=', self.group_id.id)])
         print ('employee')
         print (employee)
         self.employee_ids = employee

    
    def report_print(self, data):
        print ('Hola mundo')
        print ('self.group_id.enrollment')
        print (stop)
        print ('Hola mundo')
        data= {
            'group':self.group_id.name,
            'perception_type':self.perception_type,
            'type_id':self.type_id.name,
            'all_or_only':self.all_or_only,
        }
        print ('Hola mundo')
        return self.env.ref('payroll_mexico.report_hr_perceptions_wizard').report_action(self, data=data)
