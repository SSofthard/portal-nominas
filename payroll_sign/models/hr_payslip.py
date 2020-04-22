# -*- coding: utf-8 -*-

import babel
import pytz
import base64
import qrcode
import logging
import zeep

from pytz import timezone
from datetime import date, datetime, time, timedelta
from dateutil import relativedelta as rdelta
from io import StringIO, BytesIO
from lxml import etree as ET
from .tool_convert_numbers_letters import numero_to_letras

from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.addons.payroll_mexico.cfdilib_payroll import cfdilib, cfdv32, cfdv33

from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    #Columns
    signed = fields.Boolean(string='Document Signed')



