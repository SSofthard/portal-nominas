# -*- coding: utf-8 -*-

import datetime
import logging

from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from datetime import datetime, time, timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"
    
    code = fields.Char('Code', required=True)

    _sql_constraints = [('code_unique', 'unique(Code)', "the code must be unique")]

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            code = record.code
            if code:
                name = "%(name)s %(code)s " % {
                    'name': name,
                    'code': code,
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

    @api.model
    def create(self, values):
        """ Override to avoid automatic logging of creation """
        holiday = super(HolidaysRequest, self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(values)
        request_date_from = values.get('request_date_from')
        date_from = values.get('date_from')
        duration = values.get('number_of_days')
        request_date_to = values.get('request_date_to')
        if duration == 1 and request_date_from:
            request_date_to = datetime.strptime(request_date_from, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=0.5)
            holiday.date_to = request_date_to
            request_date_to = fields.Date.from_string(request_date_to).strftime(DEFAULT_SERVER_DATE_FORMAT)
            holiday.request_date_to = request_date_to
        if duration > 1 and request_date_from:
            request_date_to = datetime.strptime(request_date_from, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=duration)
            holiday.date_to = request_date_to
            request_date_to = fields.Date.from_string(request_date_to).strftime(DEFAULT_SERVER_DATE_FORMAT)
            holiday.request_date_to = request_date_to
        return holiday
            
            
            
            
            
            
            
            
            
            
            
            
            
