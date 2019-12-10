# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TabExpenses(models.Model):
    _name = 'hr.tab.expenses'

    #Columns
    name = fields.Char('Description', readonly=False)
    expense_tab_lines = fields.One2many(inverse_name='tab_id', comodel_name='hr.tab.expenses.lines', string='Costos estimados')

    # attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')


class TabExpensesLines(models.Model):
    _name = 'hr.tab.expenses.lines'

    address_from = fields.Many2one(comodel_name='res.partner', string='Origen')
    address_to = fields.Many2one(comodel_name='res.partner', string='Destino')
    amount_per_day = fields.Float(string='Monto estimado por día')
    tab_id = fields.Many2one(comodel_name='hr.tab.expenses', string='Tabulador')