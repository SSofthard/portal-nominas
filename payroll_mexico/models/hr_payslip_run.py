# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    
    payroll_type = fields.Selection([
            ('ordinary_payroll', 'Ordinary Payroll'),
            ('extraordinary_payroll', 'Extraordinary Payroll')], 
            string='Payroll Type', 
            default="ordinary_payroll", 
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
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
            ('12', 'December')], 
            string='Payroll month', 
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_of_month = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6')], 
            string='Payroll of the month', 
            required=True, 
            default="1",
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_period = fields.Selection([
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('decennial', 'Decennial'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly')], 
            string='Payroll period', 
            default="biweekly",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    table_id = fields.Many2one('table.settings', string="Table Settings")
    subtotal_amount_untaxed = fields.Float(string='Base imponible', readonly=True)
    amount_tax = fields.Float(string='Impuestos', readonly=True)
    payslip_count = fields.Integer(compute='_compute_payslip_count', string="Payslip Computation Details")
    payroll_tax_run_count = fields.Integer(compute='_compute_payroll_tax_run_count', string="Payslip Computation Details")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('close', 'Close'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    @api.multi
    def _compute_payslip_count(self):
        slip_ids = self.mapped('slip_ids')
        list_tax = []
        for payslip in slip_ids:
            line_ids = payslip.line_ids
            list_tax += line_ids.ids
        self.payslip_count = len(list_tax)

    @api.multi
    def _compute_payroll_tax_run_count(self):
        list_tax = []
        slip_ids = self.mapped('slip_ids')
        for payslip in slip_ids:
            line_ids = payslip.line_ids.filtered(lambda o: o.salary_rule_id.payroll_tax == True)
            list_tax += line_ids.ids
        self.payroll_tax_run_count = len(list_tax)
    
    @api.multi
    def action_view_payslip(self):
        return {
            'name': _('Detalles de Nómina'),
            # ~ 'domain': domain,
            'res_model': 'hr.payslip.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
        }
        
        return action
        
    @api.multi
    def action_view_payroll_tax_run(self):
        list_tax = []
        slip_ids = self.mapped('slip_ids')
        for payslip in slip_ids:
            line_ids = payslip.line_ids.filtered(lambda o: o.salary_rule_id.payroll_tax == True)
            list_tax += line_ids.ids
        domain = [('id', 'in', list_tax)]
        return {
            'name': _('Base Imp. ISN'),
            'domain': domain,
            'res_model': 'hr.payslip.line',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
        }
        return action
    
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
        # lines_untaxed = self.slip_ids.mapped('line_ids').filtered(
        #     lambda line: line.salary_rule_id.type == 'perception' and line.salary_rule_id.payroll_tax)
        # self.subtotal_amount_untaxed = sum(lines_untaxed.mapped('amount'))
        self.slip_ids.compute_amount_untaxed()
        self.subtotal_amount_untaxed = sum(self.slip_ids.mapped('subtotal_amount_untaxed'))
        self.get_tax_amount()

    @api.multi
    def get_tax_amount(self):
        '''
        Este metodo calcula el monto de impuesto para la nomina
        '''

        self.amount_tax = self.env['hr.isn'].get_value_isn(self.group_id.state_id.id,
                                                           self.subtotal_amount_untaxed, self.date_start.year)
    @api.multi
    def close_payslip_run(self):
        '''
        En este metodo se correran los calculos de base imponible e impuestos
        '''
        self.recalculate_payroll()
        self.slip_ids.compute_amount_untaxed()
        self.compute_amount_untaxed()
        for payslip in self.slip_ids:
            payslip.state = 'done'
            amount = 0
            for line in payslip.line_ids:
                if line.salary_rule_id.type == 'deductions' and line.salary_rule_id.type_deduction == '011':
                    amount += line.total
            move_id = self.env['hr.credit.employee.account'].create_move(description=payslip.number,debit=amount,employee=payslip.employee_id)
            payslip.move_infonacot_id = move_id.id
            payslip.input_ids.write({'state':'paid'})
        return super(HrPayslipRun, self).close_payslip_run()
    
    @api.multi
    def draft_payslip_run(self):
        for payslip in self.slip_ids:
            payslip.state = 'draft'
            payslip.move_infonacot_id.unlink()
        return self.write({'state': 'draft'})
        
    @api.multi
    def cancel_payslip_run(self):
        for payslip in self.slip_ids:
            payslip.state = 'cancel'
            payslip.move_infonacot_id.unlink()
            payslip.input_ids.write({'payslip':False,'state':'approve'})
            payslip.input_ids = False
        return self.write({'state': 'cancel'})
    
    def recalculate_payroll(self):
        for payslip in self.slip_ids:
            worked_days_line_ids = payslip.get_worked_day_lines(payslip.contract_id, payslip.date_from, payslip.date_to)
            worked_days_lines = payslip.worked_days_line_ids.browse([])
            payslip.worked_days_line_ids = []
            for r in worked_days_line_ids:
                worked_days_lines += worked_days_lines.new(r)
            payslip.worked_days_line_ids = worked_days_lines
            payslip.compute_sheet()
        return 
