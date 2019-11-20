# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Contract(models.Model):

    _inherit = 'hr.contract'

    code = fields.Char('Code', default="HOLA",required=True)
    type_id = fields.Many2one(string="Type Contract")
    productivity_bonus = fields.Float('Productivity bonus', required=False)
    attendance_bonus = fields.Float('Attendance bonus', required=False)
    punctuality_bonus = fields.Float('Punctuality Bonds', required=False)
    social_security = fields.Float('Social security', required=False)
    
    def print_contract(self):
        report=self.type_id.report_id
        return report.report_action(self, data={})

