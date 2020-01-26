# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tables_id = fields.Many2one(
        'tablas.antiguedades', 'Tables',
        related='company_id.tables_id', readonly=False)


class Company(models.Model):
    _inherit = 'res.company'

    tables_id = fields.Many2one(
        'tablas.antiguedades', 'Antiguedades tables', readonly=False, invisible=True)
