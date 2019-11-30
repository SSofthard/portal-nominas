# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class hrEmployeeContract(models.TransientModel):
    _name = "hr.employee.contract"
    
    def _default_employee_id(self):
        employee_id=self.env['hr.employee'].search([('id','in',self.env.context.get('active_ids', []))])
        return employee_id
    
    #Columns
    employee_id = fields.Many2one('hr.employee', string='Employees', default=_default_employee_id)
    type_id = fields.Many2one('hr.contract.type', string="Employee Category", required=True, default=lambda self: self.env['hr.contract.type'].search([], limit=1))
    date_start = fields.Date('Start Date', required=True, default=fields.Date.today,
        help="Start date of the contract.")
    
    def generate_contract(self):
        result = self.employee_id.generate_contracts(self.type_id,self.date_start)
        return {
            'name': _('Contract'),
            'domain': [('id','in',result)],
            'res_model': 'hr.contract',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
        }
