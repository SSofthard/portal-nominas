# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class hrPublicHolidaysEmail(models.TransientModel):
    _name = "hr.public.holidays.email"
    
    #Columns
    employee_ids = fields.Many2many('hr.employee', 'employee_rel', 'category_id', 'emp_id', string='Employees')
    
    def send_mail(self):
        holiday_id = self.env['hr.public.holidays'].browse(self.env.context.get('active_id'))
        return holiday_id.send_mail(self.employee_ids)
