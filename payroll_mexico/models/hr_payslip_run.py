# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    
    payroll_type = fields.Selection([
            ('ordinary_payroll', 'Ordinary Payroll'),
            ('extraordinary_payroll', 'Extraordinary Payroll')], string='Payroll Type', default="ordinary_payroll", required=True)
    payroll_month = fields.Selection([
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December')], string='Payroll month', required=True)
    payroll_of_month = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6')], string='Payroll of the month', required=True, default="1")
    payroll_period = fields.Selection([
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('decennial', 'Decennial'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly')], string='Payroll period', default="biweekly",required=True)
    table_id = fields.Many2one('table.settings', string="Table Settings")
    subtotal_amount_untaxed = fields.Float(string='Base imponible')
    amount_tax = fields.Float(string='Impuestos')
    
    @api.onchange('date_start', 'date_end')
    def onchange_date_start_date_end(self):
        if (not self.date_start) or (not self.date_end):
            return
        date_from = self.date_start
        date_to = self.date_end
        self.table_id = self.env['table.settings'].search([('year','=',int(date_from.year))],limit=1).id
        self.payroll_month = str(date_from.month)
        return

    @api.multi
    def compute_amount_untaxed(self):
        '''
        Este metodo calcula el monto de base imponible para la nomina a este monto se le calculara el impuesto
        '''
        lines_untaxed = self.slip_ids.mapped('line_ids').filtered(
            lambda line: line.salary_rule_id.type == 'perception' and line.salary_rule_id.payroll_tax)
        self.subtotal_amount_untaxed = sum(lines_untaxed.mapped('amount'))
        self.get_tax_amount()

    @api.multi
    def get_tax_amount(self):
        '''
        Este metodo calcula el monto de impuesto para la nomina
        '''

        self.amount_tax = self.env['hr.isn'].get_value_isn(self.group_id.state_id.id,
                                                           self.subtotal_amount_untaxed, self.date_start.year)

