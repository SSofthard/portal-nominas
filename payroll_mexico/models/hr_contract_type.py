# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

class ContractType(models.Model):

    _inherit = 'hr.contract.type'

    report_id = fields.Many2one(
                                'ir.actions.report',
                                domain=[('model','=','hr.contract')],
                                string="Report",)

