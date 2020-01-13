# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta
from pytz import utc

from odoo import api, fields, models
from odoo.tools import float_utils


# This will generate 16th of days
ROUNDING_FACTOR = 16


class ResourceMixin(models.AbstractModel):
    _inherit = 'resource.mixin'

    def get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None, contract = False):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        public_holidays_obj = self.env['hr.days.public.holidays']
        if contract:
            state = contract.employee_id.group_id.state_id
            public_holidays_days = public_holidays_obj.search([('state_ids', 'in', state._ids)]).mapped('date')
        else:
            public_holidays_days = public_holidays_obj.search([]).mapped('date')
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id
        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600
        sunday_hours = defaultdict(float,{day:day_hours[day] for day in filter(lambda day: day.weekday() == 6, day_hours)})
        public_day_hours = defaultdict(float)
        for public_holiday in public_holidays_days:
            if day_hours.get(public_holiday):
                public_day_hours[public_holiday]=day_hours.get(public_holiday)
        # public_holidays_hours = defaultdict(float,
        #                            {day: day_hours[day] for day in filter(lambda day: day, day_hours)})
        public_days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[public_day] / day_total[public_day]) / ROUNDING_FACTOR
            for public_day in public_day_hours
        )

        sundays = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[sunday] / day_total[sunday]) / ROUNDING_FACTOR
            for sunday in sunday_hours
            )
        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'public_days': public_days,
            'public_days_hours': sum(public_day_hours.values()),
            'days': days,
            'sundays': sundays,
            'sundays_hours': sum(sunday_hours.values()),
            'hours': sum(day_hours.values()),
        }

