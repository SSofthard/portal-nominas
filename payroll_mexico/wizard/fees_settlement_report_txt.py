# -*- coding: utf-8 -*-

from io import BytesIO
import time
import datetime
import xlwt

from xlsxwriter.workbook import Workbook
from xlwt import easyxf
import base64
import xlsxwriter
import itertools
from operator import itemgetter
import operator


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class PayslipExcel(models.TransientModel):
    _name = "hr.fees.settlement.report.txt"
    _description = 'Exportar txt'

    #Columns
    txt_file = fields.Binary('Descargar')
    file_name = fields.Char('Descargar')
