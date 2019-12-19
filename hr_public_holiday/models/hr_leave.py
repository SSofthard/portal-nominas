# -*- coding: utf-8 -*- 

import logging
import math

from datetime import datetime, time, timedelta
from pytz import timezone, UTC

from odoo import api, fields, models
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _


class HolidaysRequest(models.Model):
    _inherit = ['hr.leave']

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to:
            list_dates = [self.date_from + timedelta(days=d) for d in range((self.date_to - self.date_from).days + 1)]
            number_day = 0
            for date in list_dates:
                equal_dates = self.env['hr.days.public.holidays'].search([('date', '=', date)])
                if equal_dates and equal_dates.date.weekday() != 5 and equal_dates.date.weekday() != 6:
                    number_day += 1
                    self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - number_day
                else:
                    self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id) - number_day
        else:
            self.number_of_days = 0
