# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

class InfonavitHistoryWizard(models.TransientModel):
    _name = "infonavit.change.history.wizard"

    #Columns
    date = fields.Date("Date", required=True)
    
    def apply_change(self):
        move_type = self.env.context.get('move_type', [])
        infonavit = self.env['hr.infonavit.credit.line'].search([('id','in',self.env.context.get('active_ids', []))])
        if self.date < infonavit.date:
            raise ValidationError(_('The date cannot be less than the date of registration of the INFONAVIT credit.'))
        if move_type == 'discontinued':
            infonavit.action_suspend(self.date)   
        if move_type == 'reboot':
            infonavit.action_reboot(self.date) 
        if move_type == 'low_credit':
            infonavit.action_close(self.date) 
        return 
