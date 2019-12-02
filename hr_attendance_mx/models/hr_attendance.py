# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from datetime import date, datetime, time
from pytz import timezone, UTC

from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def sundays_worked(self, check_in, check_out, employee_id):
        """This function returns the number of sundays worked."""
        domain = [
            ('check_in', '<=', check_out),
            ('check_out', '>', check_in),
            ('employee_id', '=', employee_id),
        ]
        attendances = self.search(domain, order='check_in')
        sundays = []
        for sunday in attendances:
            if sunday.check_in.isoweekday() in [7]:
                sundays.append(sunday.id)
        return len(sundays)

    def search_holidays(self, date_from, date_to, company_id):
        today = datetime.now()
        public_holidays = self.env['hr.public.holidays'].search([('year','=',today.year),('company_id','=',company_id)])
        days_public = public_holidays.days_public_ids.filtered(lambda d: d.date >= date_from.date() and d.date <= date_to.date()).mapped('date')
        return days_public

    def holidays_worked(self, check_in, check_out, employee_id):
        """This function returns the number of holidays worked."""
        check_in = fields.Datetime.from_string(check_in).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_out = fields.Datetime.from_string(check_out).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_in = datetime.strptime(check_in, DEFAULT_SERVER_DATETIME_FORMAT)
        check_out = datetime.strptime(check_out, DEFAULT_SERVER_DATETIME_FORMAT)
        if employee_id:
            employee = self.env['hr.employee'].search([('id','=', employee_id)])
            if not employee:
                raise exceptions.UserError(_('No employee found.'))
            dayss = employee.get_work_days_data(check_in, check_out)['days']
            rage_holidays = self.search_holidays(check_in, check_out, employee.company_id.id or self.env.user.company_id)
            domain = [
                ('check_in', '<=', check_out),
                ('check_out', '>', check_in),
                ('employee_id', '=', employee_id),
            ]
            holidays = []
            attendances = self.search(domain, order='check_in')
            for holiday in attendances:
                if holiday.check_in.date() in rage_holidays:
                    holidays.append(holiday.id)
            return len(holidays)

    def rest_days_worked(self, check_in, check_out, employee_id):
        """This function returns the number of rest days worked."""
        check_in = fields.Datetime.from_string(check_in).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_out = fields.Datetime.from_string(check_out).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_in = datetime.strptime(check_in, DEFAULT_SERVER_DATETIME_FORMAT)
        check_out = datetime.strptime(check_out, DEFAULT_SERVER_DATETIME_FORMAT)
        if employee_id:
            employee = self.env['hr.employee'].search([('id','=', employee_id)])
            if not employee:
                raise exceptions.UserError(_('No employee found.'))
            dayss = employee.get_work_days_data(check_in, check_out)['days']
            rage_holidays = self.search_holidays(check_in, check_out, employee.company_id.id or self.env.user.company_id)
            domain = [
                ('check_in', '<=', check_out),
                ('check_out', '>', check_in),
                ('employee_id', '=', employee_id),
            ]
            holidays = []
            attendances = self.search(domain, order='check_in')
            for holiday in attendances:
                if holiday.check_in.date() in rage_holidays:
                    holidays.append(holiday.id)
            return len(holidays)

    def search_sundays_worked(self):
        """This is function set values for test function sundays_worked()"""
        today = datetime.now()
        month_start = "%s-%s-01" % (today.year, today.month)
        month_end = "%s-%s-%s" % (today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        check_in = fields.Datetime.from_string(month_start).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        check_out = fields.Datetime.from_string(month_end).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        print ('Start %s, End %s' %(check_in, check_out))
        days_worked = self.holidays_worked(check_in, check_out, self.employee_id.id)
        return days_worked
