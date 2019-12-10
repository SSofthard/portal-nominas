# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Expenses(models.Model):
    _inherit = 'hr.expense'



    # def _compute_attachment_number(self):
    #     '''
    #     Herencia para que se ejecute el metodo compute de el campo numero de documentos y se agregue el estado por defecto de cada uno
    #     :return:
    #     '''
    #     super(Expenses,self)._compute_attachment_number()
    #     attachment_data = self.env['ir.attachment'].search(
    #         [('res_model', '=', 'hr.expense'), ('res_id', 'in', self.ids)])
    #     new_attachment = attachment_data.filtered(lambda x: not len(x.tag_ids))
    #     for attachment in new_attachment:
    #         attachment.tag_ids = self.env.ref('documents.documents_hr_status_tc')

    #Columns
    name = fields.Char('Description', readonly=False)
    employee_id = fields.Many2one(readonly=False)
    other_classification = fields.Char('Other classification', readonly=False)
    completed = fields.Boolean(string='Completed')
    classification = fields.Selection([('1', 'Alimentos'),('2   ','Transporte'),('3','Hospedaje'),('4','Translados por movilidad'), ('other','Other')],string='Classification', required=True)
    date_invoice = fields.Datetime(string = 'Date invoice')
    date_checking = fields.Datetime(string = 'Date Checking')
    state = fields.Selection([('draft', 'Borrador'),('pending_checking', 'Pending Checking'),('approved','Approved'),('refused','Refused')], track_visibility=True, default='pending_checking',  compute=False)
    subtotal_amount = fields.Monetary('Subtotal')
    total_amount = fields.Monetary('Subtotal', compute=False)
    amount_tax = fields.Monetary('Taxes', default= '16')
    document_type = fields.Selection([('invoice', 'Invoice'),('remission','Remission')], string='Document Type', required=True)
    date = fields.Date(string='Create Date', default= lambda self: fields.Date.context_today(self))
    product_id = fields.Many2one(required=False, comodel_name='product.product')
    unit_amount = fields.Float(required=False)
    # attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')

    @api.constrains('total_amount','amount_tax','subtotal_amount')
    def constrains_amount_total(self):
        if not self.total_amount > 0:
            raise UserError(_('El monto total del gasto debe ser mayor a 0.'))
        if self.document_type == 'invoice' and not self.subtotal_amount > 0:
            raise UserError(_('El monto subtotal del gasto debe ser mayor a 0.'))

    @api.constrains('sheet_id')
    def constrains_sheet_id(self):
        if self.sheet_id.state == 'closed':
            raise UserError(_('No puede agregar gastos a un informe de viaticos cerrado.'))

    @api.model
    def create(self,vals):
        res = super(Expenses,self).create(vals)
        res.write({'state':'pending_checking'})
        return res

    @api.multi
    def pass_to_pending_checking(self):
        self.write({'state':'pending_checking'})

    @api.multi
    def approve_expense(self):
        self.write({'state':'approved', 'date_checking': fields.Date.context_today(self)})

    @api.multi
    def refuset_expense(self):
        return {'type': 'ir.actions.act_window',
                'res_model': 'refused.expense.wizard',
                'view_mode': 'form',
                'target': 'new'}
                
    @api.onchange('subtotal_amount','total_amount')
    def onchange_total_amount(self):
        sub_total = self.subtotal_amount
        amount = self.amount_tax
        if sub_total:
            total =  sub_total * (amount / 100)
            self.total_amount = sub_total + total
    
    @api.multi
    def update_amount_tax(self):
        sub_total = self.subtotal_amount
        amount = self.amount_tax
        total =  sub_total * (amount / 100)
        self.total_amount = sub_total + total

class ExpensesClassification(models.Model):
    _name = 'hr.expense.classification'

    #Columns
    name = fields.Char(string = 'Name')
    
class ExpensesSheets(models.Model):
    _inherit = 'hr.expense.sheet'

    @api.multi
    def compute_amount(self):
        return self._compute_amount()

    @api.one
    @api.depends('expense_line_ids.state', 'payment_ids')
    def _compute_amount(self):
        '''
        Este metodd calcula los montos total y el monto de diferencia.
        :return:
        '''
        self.total_amount = sum(map(lambda x: x.total_amount, self.expense_line_ids.filtered(lambda x: x.state == 'approved')))
        self.amount_payment = sum(self.env['hr.expense.payment'].search([('sheet_id','=',self.id)]).mapped('amount'))
        payment_type = self.env['hr.expense.payment'].search([('sheet_id','=',self.id)]).mapped('payment_type')
        if len(payment_type):
            self.payment_type_res = self.env['hr.expense.payment'].search([('sheet_id','=',self.id)]).mapped('payment_type')[0]
            self.paid=True
        else:
            self.paid = False
        self.amount_difference = self.amount_delivered - self.total_amount
        if self.amount_difference > 0:
            self.operation_result = 'return'
        elif self.amount_difference < 0:
            self.operation_result = 'refund'
            self.amount_difference = self.amount_difference *(-1)
        else:
            self.operation_result = 'reconciled'


    def approve_amount_expense_sheets(self, amount_approve):
        '''

        :return:
        '''
        self.amount_delivered = amount_approve
        return super(ExpensesSheets,self).approve_expense_sheets()

    @api.multi
    def approve_expense_sheets(self):
        '''Se hereda el metodo para accionar un wizard y que el usuario agregue el monto de aprobacion para la solicitud'''
        return {'type': 'ir.actions.act_window',
                'res_model': 'expense.sheet.amount.approve.wizard',
                'view_mode': 'form',
                'target': 'new'}

    @api.multi
    def open_expense_sheets(self):
        '''Se hereda el metodo para accionar un wizard y que el usuario agregue el monto de aprobacion para la solicitud'''
        sequence = self.env['ir.sequence'].next_by_code('hr.expense.sheet.folio')
        return self.write({'state':'open', 'folio':sequence})

    @api.multi
    def close_expense_sheets(self):
        '''Se hereda el metodo para accionar un wizard y que el usuario agregue el monto de aprobacion para la solicitud'''
        return self.write({'state':'closed'})

    @api.multi
    def payment_expense_sheets(self):
        '''Se hereda el metodo para accionar un wizard y que el usuario agregue el monto de aprobacion para la solicitud'''
        self.write({'state':'done'})

    @api.multi
    def action_submit_sheet(self):
        self.write({'state': 'open'})
        self.activity_update()

    # Columns
    paid = fields.Boolean(compute='_compute_amount', string='Paid')
    payment_ids = fields.One2many(inverse_name='sheet_id', comodel_name='hr.expense.payment',string='Amount Payment')
    amount_payment = fields.Monetary(compute='_compute_amount', string='Amount Payment')
    payment_type_res = fields.Selection([('inbound','Inbound'),('outbound','Outbound')], compute='_compute_amount')
    folio = fields.Char(string='Folio', default='/', readonly=True)
    date_request = fields.Datetime(string='Date request')
    state = fields.Selection(selection_add=[('open','Open'),('closed','Closed'),('cancel', 'Canceled')], track_visibility=True)
    amount_delivered = fields.Monetary('Amount Delivered')
    amount_difference = fields.Monetary(compute='_compute_amount')
    operation_result = fields.Selection([ ('reconciled', 'Reconciled Amount'),('refund', 'Refund'), ('return', 'Return')],compute='_compute_amount')
    estimate_viatics = fields.Boolean(string='Do you want to estimate viatics?')
    is_older = fields.Boolean(string='Is older')
    note = fields.Text('Notes')
    address_origin_id = fields.Many2one('res.partner', string='Origin Address')
    address_dest_id = fields.Many2one('res.partner', string='Dest Address')
    total_by_day = fields.Monetary(string='Amount By Day', compute=False)

    @api.onchange('amount_delivered','is_older')
    def onchange_is_older(self):
        amount = self.amount_delivered
        if amount > self.total_by_day:
            self.is_older =  True
        else:
            self.is_older =  False

    @api.constrains('amount_delivered')
    def constrains_amount_delivered(self):
        if not self.amount_delivered > 0:
            raise UserError(_('El monto entregado debe ser mayor a 0.'))
            
class Partner(models.Model):
    _inherit = "res.partner"

    estimate_viatics = fields.Boolean(string='Do you want to estimate viatics?')
