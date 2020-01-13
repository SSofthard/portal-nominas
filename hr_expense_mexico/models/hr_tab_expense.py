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

    address_from = fields.Many2one('res.partner', string='Origen', context="{'viatics_address': 1}")
    address_to = fields.Many2one('res.partner', string='Destino', context="{'viatics_address': 1}")
    address_from_complete = fields.Char(string='Origen', store=True)
    address_to_complete = fields.Char( string='Destino', store=True)
    amount_per_day = fields.Float(string='Monto estimado por día')
    tab_id = fields.Many2one(comodel_name='hr.tab.expenses', string='Tabulador')

    @api.onchange('address_from',)
    def onchange_address_from_complete(self):
        for record in self:
            name = str(record.address_from.street) + ' ' + str(record.address_from.street2) + ' ' + str(record.address_from.city) + ' ' + str(record.address_from.state_id.name) + ' ' + str(record.address_from.zip) + ' ' + str(record.address_from.country_id.name)
            if record.address_from:
                record.address_from_complete = name
                
    @api.onchange('address_to',)
    def onchange_address_to_complete(self):
        for record in self:
            name = str(record.address_to.street) + ' ' + str(record.address_to.street2) + ' ' + str(record.address_to.city) + ' ' + str(record.address_to.state_id.name) + ' ' + str(record.address_to.zip) + ' ' + str(record.address_to.country_id.name)
            if record.address_to:
                record.address_to_complete = name
        
