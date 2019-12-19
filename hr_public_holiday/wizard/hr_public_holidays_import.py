# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import datetime
import calendar
import pytz
import dateutil
import base64


from pytz import timezone, UTC
from datetime import datetime, time, timedelta, date
from datetime import datetime
from xlrd import open_workbook
from dateutil.relativedelta import relativedelta


from datetime import date
from datetime import datetime, time as datetime_time, timedelta

from odoo.tools.mimetypes import guess_mimetype
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, pycompat
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class hrPublicHolidaysImport(models.TransientModel):
    _name = "hr.public.holidays.import"
    _description = "Holiday Calendar Import"
    
    #Columns
    file_ids = fields.Many2many(string='Calendar File', comodel_name='ir.attachment',required=True)
    file_name = fields.Char('File name', related='file_ids.name', required=True)
    
    @api.onchange('file_ids')
    def onchange_file_ids(self):
        if self.file_ids:
            self.read_document()
    
    @api.multi
    def read_document(self):
        datafile = base64.b64decode(self.file_ids.datas)
        calendar = []
        calendar_line = []
        vals = []
        if datafile:
            book = open_workbook(file_contents=datafile)
            sheet = book.sheet_by_index(0)
            country_id = self.env.user.company_id.country_id
            name = ''
            year = ''
            states = ''
            for row in range(1, sheet.nrows):
                for col in range(sheet.ncols):
                    if not (sheet.cell_value(row, col)) == '' and col <= 4:
                        if col == 2:
                            dt = datetime(*xlrd.xldate.xldate_as_tuple(sheet.cell_value(row , col), book.datemode))
                            dates = dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            year = pycompat.text_type(sheet.cell_value(row, 0))
                            date_holiday = self.check_date(dates, year)
                            calendar_line.append((0,0,
                                            {'name': name, 
                                            'date': date_holiday,
                                            'days': self.env['hr.days.public.holidays'].get_week_string(date_holiday),
                                            'state_ids': self.check_states(sheet.cell_value(row, 3).split(',')),
                                            'country_id': country_id.id}))
                        if col == 1:
                            name = pycompat.text_type(sheet.cell_value(row, col))
                        if col == 0:
                            
                            year = pycompat.text_type(int(sheet.cell_value(row, col)))
                            self.check_year(year, self.env.user.company_id.id)
                            calendar.append({'year': year, 
                                    'company_id': self.env.user.company_id.id,
                                    'date_from': '%s-01-01' %year,
                                    'date_end': '%s-12-31' %year,
                                    'days_public_ids': calendar_line,
                                    'country_id': country_id.id,})
        return calendar
        
    def check_states(self, codes):
        states = []
        for code in codes:
            if not (code == 'TODOS'):
                if code:
                    state_id = self.env['res.country.state'].search([('code','=', code),('country_id','=', self.env.user.company_id.country_id.id)])
                    if not state_id:
                        raise UserError(_("Not found state for code %s.") %(code))
                    else:
                        states.append(state_id.id)
            else:
                states += self.env['res.country.state'].search([('country_id','=', self.env.user.company_id.country_id.id)]).ids
        return [(6, 0, states)]

        if self.env['hr.public.holidays'].search([('year','=', year),('company_id','=', company)]):
            self.file_ids = False
            raise UserError(_("The year %s is already registered for the company %s.") %(year, company))

    def check_year(self, year, company):
        if self.env['hr.public.holidays'].search([('year','=', year),('company_id','=', company)]):
            self.file_ids = False
            raise UserError(_("The year %s is already registered for the company %s.") %(year, company))

    def check_date(self, dates, year):
        dates = datetime.strptime(dates, DEFAULT_SERVER_DATE_FORMAT)
        return dates.date()
            
    @api.multi
    def import_data(self):
        vals = self.read_document()
        if vals:
            for val in vals:
                self.env['hr.public.holidays'].create(val)
