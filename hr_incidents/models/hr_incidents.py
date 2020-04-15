# -*- coding: utf-8 -*-

import datetime
import logging

from pytz import timezone, UTC, utc
from datetime import datetime, time, timedelta, date
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.resource.models.resource import float_to_time, datetime_to_string, string_to_datetime, HOURS_PER_DAY
from odoo.addons.resource.models.resource import Intervals


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"
    
    unpaid = fields.Boolean('Es se paga?', default=False)
    request_unit = fields.Selection([
        ('day', 'Días'), ('hour', 'Horas')],
        default='day', string='Tomar ausencias en', required=True)
    time_type = fields.Selection([
        ('leave', 'Ausentismo'),
        ('other', 'Other'),
        ('inability', 'Incapacidad'),], 
        default='leave', string="Tipo de licencia",
        help="Si esto debe calcularse como vacaciones o como tiempo de trabajo (por ejemplo: formación)")
    allocation_type = fields.Selection([
        ('fixed', 'Arreglado por HR'),
        ('fixed_allocation', 'Solucionado por solicitud de asignación de recursos humanos'),
        ('no', 'Sin asignación')],
        default='fixed', string='Modo',
        help='\tCorregido por HR: asignado por HR y no se puede omitir; los usuarios pueden solicitar hojas;'
             '\tSolucionado por solicitud de asignación de recursos humanos +: asignado por recursos humanos y los usuarios pueden solicitar permisos y asignaciones;'
             '\tSin asignación: sin asignación por defecto, los usuarios pueden solicitar permisos libremente;')
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

class irAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    leave_id = fields.Many2one('hr.leave', invisible=True)

class HolidaysRequest(models.Model):
    _inherit = "hr.leave"
    
    @api.multi
    def _document_count(self):
        for each in self:
            document_ids = self.env['ir.attachment'].sudo().search([('leave_id', '=', each.id)])
            each.document_count = len(document_ids)

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [
            ('leave_id', '=', self.id)]
        return {
            'name': _('Documents Incidents'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_leave_id': '%s'}" % self.id
        }
    
    date_to = fields.Datetime(
        'End Date', readonly=True, copy=False, required=False,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    group_id = fields.Many2one('hr.group', "Group", readonly=True, related= 'employee_id.group_id', store=True)
    time_type = fields.Selection("Selection", related= 'holiday_status_id.time_type')
    # Translate fields
    request_unit_half = fields.Boolean('Half Day')
    type_inhability_id = fields.Many2one('hr.leave.inhability', "Type inhability")
    inhability_classification_id = fields.Many2one('hr.leave.classification', "Classification")
    inhability_category_id = fields.Many2one('hr.leave.category', "Category")
    inhability_subcategory_id = fields.Many2one('hr.leave.subcategory', "Subcategory")
    folio = fields.Char('Folio')
    document_count = fields.Integer(compute='_document_count', string='# Documents')
    
    
    

    @api.multi
    @api.onchange('type_inhability_id')
    def onchange_type_inhability_id(self):
        self.inhability_classification_id = False
        domain = {'inhability_classification_id': [('id', 'in', self.type_inhability_id.classification_ids.ids)]}
        return {'domain': domain}
        
    @api.multi
    @api.onchange('inhability_classification_id')
    def onchange_inhability_classification_id(self):
        self.inhability_category_id = False
        domain = {'inhability_category_id': [('id', 'in', self.inhability_classification_id.category_ids.ids)]}
        return {'domain': domain}
        
    @api.multi
    @api.onchange('inhability_category_id')
    def onchange_inhability_category_id(self):
        self.inhability_subcategory_id = False
        domain = {'inhability_subcategory_id': [('id', 'in', self.inhability_category_id.subcategory_ids.ids)]}
        return {'domain': domain}

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
        request_date_from = datetime.strptime(fields.Date.from_string(request_date_from).strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
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

class ResUsers(models.Model):
    _inherit = "res.users"
    
    group_id = fields.Many2one('hr.group', "Group", required=False)
    

class CalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    time_type = fields.Selection(selection_add=[('inability', 'Incapacidad')])

# ~ def string_to_datetime(value):
    # ~ """ Convert the given string value to a datetime in UTC. """
    # ~ return utc.localize(fields.Datetime.from_string(value))

# ~ def datetime_to_string(dt):
    # ~ """ Convert the given datetime (converted in UTC) to a string value. """
    # ~ return fields.Datetime.to_string(dt.astimezone(utc))

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    def _leave_intervals(self, start_dt, end_dt, resource=None, domain=None):
        """ Return the leave intervals in the given datetime range.
            The returned intervals are expressed in the calendar's timezone.
        """
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()

        # for the computation, express all datetimes in UTC
        resource_ids = [resource.id, False] if resource else [False]
        if domain is None:
            domain = [('time_type', 'in', ['leave','inability'])]
        domain = domain + [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('date_from', '<=', datetime_to_string(end_dt)),
            ('date_to', '>=', datetime_to_string(start_dt)),
        ]

        # retrieve leave intervals in (start_dt, end_dt)
        tz = timezone((resource or self).tz)
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)
        result = []
        for leave in self.env['resource.calendar.leaves'].search(domain):
            dt0 = string_to_datetime(leave.date_from).astimezone(tz)
            dt1 = string_to_datetime(leave.date_to).astimezone(tz)
            result.append((max(start_dt, dt0), min(end_dt, dt1), leave))

        return Intervals(result)
