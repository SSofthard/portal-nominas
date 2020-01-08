# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, SUPERUSER_ID, modules


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
