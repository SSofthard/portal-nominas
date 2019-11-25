# -*- coding: utf-8 -*-

import datetime
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round

class HolidaysType(models.Model):
    _inherit = "hr.leave.type"
    
    code = fields.Char('Code', required=True)

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
