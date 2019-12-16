# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class EmployeeChangeHistoryWizard(models.TransientModel):
    _name = "hr.employee.change.history.wizard"
    
    # ~ def _default_employee_id(self):
        # ~ employee_id=self.env['hr.employee'].search([('id','in',self.env.context.get('active_ids', []))])
        # ~ return employee_id
    
    #Columns
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    currency_id = fields.Many2one(string="Currency", related='contract_id.currency_id')
    job_id = fields.Many2one('hr.job', index=True, string='Job Position')
    wage = fields.Monetary('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    date_from = fields.Date(string="Start Date")
    type = fields.Selection([
        ('wage', 'Wage'),
        ('job', 'Job Position'),
    ], string='Change History', index=True,
        help="""* Type changue'
                \n* If the changue is wage, the type is \'Wage\'.
                \n* If the changue is job then type is set to \'Job Position\'.""")
    
    def apply_change(self):
        print ('jeison')
        print ('jeison')
        print ('jeison')
        print ('jeison')
        # ~ result = self.employee_id.generate_contracts(self.type_id,self.date_start)
        # ~ return {
            # ~ 'name': _('Contract'),
            # ~ 'domain': [('id','in',result)],
            # ~ 'res_model': 'hr.contract',
            # ~ 'type': 'ir.actions.act_window',
            # ~ 'view_id': False,
            # ~ 'view_mode': 'kanban,tree,form',
            # ~ 'view_type': 'form',
            # ~ 'limit': 80,
        # ~ }
