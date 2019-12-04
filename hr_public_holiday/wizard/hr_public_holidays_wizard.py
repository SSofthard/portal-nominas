# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import datetime
import time
import pytz
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class hrPublicHolidaysWizard(models.TransientModel):
    _name = "hr.public.holidays.wizard"
    
    #Columns
    name = fields.Char(string="Name days public holidays",required=True)
    date_from = fields.Date("Start date", required=True)
    date_end = fields.Date("End date", required=True)
    country_id = fields.Many2one('res.country', string = 'Country')
    state_ids = fields.Many2many('res.country.state', 'hr_holiday_public_state_wizard_rel', 'line_id', 'state_id', string= 'States')
    
    @api.onchange('country_id')
    def onchange_country_id(self):
        '''
        This method changes the value of the "country_id" field to the value of the "country_id" field of the "hr.public.holidays" object
        :return:
        '''
        holiday_id = self.env['hr.public.holidays'].browse(self.env.context.get('active_id'))
        self.country_id = holiday_id.country_id
        
    @api.multi
    @api.constrains('date_from','date_end')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        holiday_id = self.env['hr.public.holidays'].browse(self.env.context.get('active_id'))
        if self.date_end < self.date_from:
            raise UserError(_("End Date Should be greater than Start Date"))
        if self.date_from < holiday_id.date_from or self.date_from > holiday_id.date_end:
            raise ValidationError(_("The start date must be between the dates of this year."))
        elif self.date_end < holiday_id.date_from or self.date_end > holiday_id.date_end:
            raise ValidationError(_("The final date must be between the dates of this year."))
     
        
    def mark_as_done(self):
        '''
        This method is used to create multiple records on "hr.days.public.holidays" within a date range. "
        :return:
        '''
        holiday_id = self.env.context.get('active_id')
        list_dates = [self.date_from + timedelta(days=d) for d in range((self.date_end - self.date_from).days + 1)] 
        day_holiday_id = self.env['hr.days.public.holidays']
        for line in list_dates:
            day_holiday_id.create({'public_holidays_id': holiday_id,
                                'name': self.name,
                                'date': line,
                                'country_id': self.country_id.id,
                                'state_ids':[[6, False,self.state_ids.ids]],
                                'days': line.strftime("%A")
                                })
                                
