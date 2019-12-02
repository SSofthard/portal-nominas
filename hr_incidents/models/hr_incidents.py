# -*- coding: utf-8 -*-

import datetime
import logging

from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"
    
    code = fields.Char('Code', required=True)
    color_name = fields.Selection([
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('lightgreen', 'Light Green'),
        ('lightblue', 'Light Blue'),
        ('lightyellow', 'Light Yellow'),
        ('magenta', 'Magenta'),
        ('lightcyan', 'Light Cyan'),
        ('black', 'Black'),
        ('lightpink', 'Light Pink'),
        ('brown', 'Brown'),
        ('violet', 'Violet'),
        ('lightcoral', 'Light Coral'),
        ('lightsalmon', 'Light Salmon'),
        ('lavender', 'Lavender'),
        ('wheat', 'Wheat'),
        ('ivory', 'Ivory'),
        ('orange', 'Orange'),
        ('golden', 'Golden'),
        ('fuchsia', 'Fuchsia'),
        ], string='Color in Report', required=True, default='red',
        help='This color will be used in the leaves summary located in Reporting > Leaves by Department.')

    _sql_constraints = [('code_unique', 'unique(Code)', "the code must be unique")]
    
    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            code = record.code
            if code:
                name = "[%(code)s] %(name)s" % {
                    'code': code,
                    'name': name,
                }
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('code', operator, name)]
        code = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(code).name_get()


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"
    
    date_to = fields.Datetime(
        'End Date', readonly=True, copy=False, required=False,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    group_id = fields.Many2one('hr.group', "Group", readonly=True, related= 'employee_id.group_id', store=True)
        
    @api.multi
    def action_approve(self):
        if not self.request_date_to:
            raise UserError(_('You must enter the end date.'))
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        return True
    
    def request_parameters(self, employee, request_date_from, number_of_days, request_date_from_period):
        if not number_of_days or number_of_days < 0:
            raise UserError(_('Negative or empty values ​​are not allowed for the number of days.'))
        if not employee:
            raise UserError(_('The employee is required.'))
        employee_id = self.env['hr.employee'].search([('id','=', employee)])
        if not employee_id:
            raise UserError(_('No employees found for the key %s.') % employee)

        dates = {}
        calendar = employee_id.resource_calendar_id or self.env.user.company_id.resource_calendar_id
        request_date_from = datetime.strptime(request_date_from, DEFAULT_SERVER_DATE_FORMAT)
        tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'UTC'  # custom -> already in UTC
        
        domain = [('calendar_id', '=', calendar.id or self.env.user.company_id.resource_calendar_id.id)]
        attendances = self.env['resource.calendar.attendance'].search(domain, order='dayofweek, day_period DESC')

        # find first attendance coming after first_day
        attendance_from = next((att for att in attendances if int(att.dayofweek) >= request_date_from.weekday()), attendances[0])
        hour_from = float_to_time(attendance_from.hour_from)
        
        request_date_from = timezone(tz).localize(datetime.combine(request_date_from.date(), hour_from)).astimezone(UTC).replace(tzinfo=None)
        request_date_to = request_date_from + timedelta(hours=calendar.hours_per_day or HOURS_PER_DAY)
        
        # find last attendance coming before last_day
        attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= request_date_to.weekday()), attendances[-1])
        hour_to = float_to_time(attendance_to.hour_to)
        request_date_from = timezone(tz).localize(datetime.combine(request_date_from.date(), hour_from)).astimezone(UTC).replace(tzinfo=None)
        # if ist half day
        if number_of_days == 0.5 and request_date_from_period:
            if request_date_from_period == 'am':
                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_from.hour_to)
            else:
                hour_from = float_to_time(attendance_to.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)
            
            # ~ half_day = calendar.hours_per_day / 2 or HOURS_PER_DAY / 2
            request_date_from = timezone(tz).localize(datetime.combine(request_date_from.date(), hour_from)).astimezone(UTC).replace(tzinfo=None)
            request_date_to = timezone(tz).localize(datetime.combine(request_date_to.date(), hour_to)).astimezone(UTC).replace(tzinfo=None)
        if number_of_days == 1:
            request_date_to = request_date_from + timedelta(hours=calendar.hours_per_day or HOURS_PER_DAY)
        if number_of_days > 1:
            request_date_to = request_date_from + timedelta(days=number_of_days)
        
        dates['request_date_from'] = request_date_from.date()
        dates['request_date_to'] = request_date_to.date()
        dates['date_from'] = request_date_from
        dates['date_to'] = request_date_to
        dates['request_date_from_period'] = request_date_from_period
        return dates
    
    
    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """
        if self.env.context.get('import_file'):
            request_parameters = self.request_parameters(values.get('employee_id'),values.get('request_date_from'),values.get('number_of_days'),values.get('request_date_from_period'))
            values['request_date_from'] = request_parameters.get('request_date_from')
            values['request_date_to'] = request_parameters.get('request_date_to')
            values['date_from'] = request_parameters.get('date_from')
            values['date_to'] = request_parameters.get('date_to')
            values['request_date_from_period'] = request_parameters.get('request_date_from_period') if request_parameters.get('request_date_from_period') else None
        return super(HolidaysRequest, self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(values)
