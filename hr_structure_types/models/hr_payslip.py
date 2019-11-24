# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    structure_type_id = fields.Many2one(
                                    'hr.structure.types',
                                    related="contract_id.structure_type_id",
                                    string="Structure Types")
                                    
    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        super(HrPayslip,self).onchange_employee()
        self.struct_id=False 
