# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExpensesPayment(models.Model):
    _name = 'hr.expense.payment'
    _inherit = 'account.payment'

    #Columns
    sheet_id = fields.Many2one(comodel_name='hr.expense.sheet', string='Expense sheet')
    # states = fields.Selection([('draft','Borrador'),('send','Enviado'),('cancelled', 'Cancelado')])
