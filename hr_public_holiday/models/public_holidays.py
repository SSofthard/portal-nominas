# -*- coding: utf-8 -*-

import calendar 
import pytz
import time
import locale

from datetime import date, datetime , timedelta

from odoo import models,fields,api, _
from odoo.exceptions import UserError, ValidationError


class publicHolidays(models.Model): 
    _name = "hr.public.holidays"
    _inherit = ['mail.thread']
    _rec_name = 'year'
    
    @api.model
    def _get_default_partner_country_id(self):
        '''
        This method places by default the country of the company in the country_id field.
        :return:
        '''
        return self.env['res.company']._company_default_get('hr.public.holidays').country_id.id
        
    #Columns
    state =  fields.Selection([('draft','Draft'),('done','Done')], string='State', default='draft')
    year = fields.Integer("Year", required=True, default=date.today().year, states={'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id, required=True, states={'done': [('readonly', True)]})
    date_from = fields.Date(string='Start date', store=True, required=True, states={'done': [('readonly', True)]})
    date_end = fields.Date(string='End date', store=True, required=True, states={'done': [('readonly', True)]})
    days_public_ids = fields.One2many('hr.days.public.holidays','public_holidays_id', string='Day public', states={'done': [('readonly', True)]})
    country_id = fields.Many2one('res.country', default=_get_default_partner_country_id, string = 'Country', required=True, states={'done': [('readonly', True)]})
    
    @api.onchange('year','date_from','date_end')
    def onchange_date(self):
        '''
        This method places the start and end date of the year in the "date_from" and "date_end" fields respectively.
        :return:
        '''
        if self.year:
            date_from = date (self.year, 1, 1)
            self.date_from = date_from
            date_end = date (self.year, 12, 31)
            self.date_end = date_end
            

    @api.multi
    def button_approve(self):
        '''
        This method is used in the "Approve" button to set the status of "Draft" to "Done"
        :return:
        '''
        return self.write({'state': 'done'})
        
    @api.multi
    def button_draft(self):
        '''
        This method is used to return the record to draft status.
        :return:
        '''
        return self.write({'state': 'draft'})
    
    @api.multi
    def action_payroll_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_public_holiday', 'public_holiday_email_template2')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hr.public.holidays' ,
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    @api.multi
    def send_mail(self,employee_ids):
        '''
        This function force email send without open windows
        '''
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference('hr_public_holiday', 'public_holiday_email_template2')[1]
        email_to = ''
        for ph in self:
            for employee in employee_ids:
                email_to +=  employee.work_email+','
            email_act = ph.action_payroll_send()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_to=email_to)
                ph.with_context(email_ctx).message_post_with_template(template_id)
        return True
    
        
class publicHolidays(models.Model): 
    _name = "hr.days.public.holidays"

    #Columns
    name = fields.Char(string="Name days public holidays",required=True)
    date = fields.Date(string='Date', required=True)
    days = fields.Selection([
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday')
    ], string='Weekday',)
    public_holidays_id = fields.Many2one('hr.public.holidays',string="Public Holidays")
    state_ids = fields.Many2many('res.country.state', 'hr_holiday_public_state_rel', 'line_id', 'state_id', string= 'States')
    country_id = fields.Many2one('res.country', string = 'Country')
    
    _sql_constraints = [('date_uniq', 'UNIQUE (date, public_holidays_id)', 'The date must be unique.')]
    
    @api.multi
    @api.onchange('country_id')
    def onchange_country_id(self):
        '''
        This method changes the value of the "country_id" field to the value of the "country_id" field of the "hr.public.holidays" object
        :return:
        '''
        country = self.public_holidays_id.country_id
        if country:
            self.country_id = country
        
    @api.onchange('date','days')
    def onchange_day(self):
        '''
        This method if the user chooses a date in the "date" field, in the "days" field the name of the day will be placed and validates that the date is
        between the range of the "date_from" and "date_end" fields of the "hr.public.holidays" object
        :return:
        '''
        if self.date:
            self.days = self.get_week_string(self.date)
            if self.date < self.public_holidays_id.date_from or self.date > self.public_holidays_id.date_end:
                raise UserError(_("The date must be between the dates of this year."))

    def get_week_string(self, dates):
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        return calendar.day_name[dates.weekday()]
