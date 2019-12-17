# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone

import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.osv import expression


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    settlement = fields.Boolean(string='Settlement')
    settlemen_date = fields.Date(string='Settlemen date', readonly=True, required=False,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)), states={'draft': [('readonly', False)]})
    reason_liquidation = fields.Selection([
            ('1', 'TERMINACIÓN DE CONTRATO'),
            ('2', 'SEPARACIÓN VOLUNTARIA'),
            ('3', 'ABANDONO DE EMPLEO'),
            ('4', 'DEFUNCIÓN'),
            ('5', 'AUSENTISMOS'),
            ('6', 'RESICIÓN DE CONTRATO'),
            ('7', 'JUBILACIÓN'),
            ('8', 'PENSIÓN'),
            ('9', 'ACEPTO OTRO EMPLEO # 42'),
            ('10', 'CLAUSURA'),
            ('11', 'OTROS'),
            ], 
            string='Reason for liquidation', 
            required=False,
            states={'draft': [('readonly', False)]})

class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    
    settlement = fields.Boolean(string='Settlement structure?')
