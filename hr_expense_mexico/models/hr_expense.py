# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Expenses(models.Model):
    _inherit = 'hr.expense'

    @api.onchange('validate_document')
    def onchange_validate_document(self):
        '''
        Este metodo agrega el adjunto a la categr'ia de documentos validados dentro de la gestion de documentos
        :return:
        '''
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.expense'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        print (attachment_data)
        print (attachment_data)
        print (attachment_data)
        print (attachment_data)
        print (attachment_data)


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
    validate_document = fields.Boolean(string='Validate Documents')
    completed = fields.Boolean(string='Completed')
    classification_id = fields.Many2one(comodel_name='hr.expense.classification')
    date_invoice = fields.Datetime(string = 'Date invoice')
    date_checking = fields.Datetime(string = 'Date Checking')
    state = fields.Selection(selection_add=[('pending_checking', 'Pending Checking'),('checked','Checked')], track_visibility=True)
    # attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')

class ExpensesClassification(models.Model):
    _name = 'hr.expense.classification'

    #Columns
    name = fields.Char(string = 'Name')

class ExpensesSheets(models.Model):
    _inherit = 'hr.expense.sheet'

    def approve_amount_expense_sheets(self, amount_approve):
        '''

        :return:
        '''
        self.amount_approved = amount_approve
        return super(ExpensesSheets,self).approve_expense_sheets()

    @api.multi
    def approve_expense_sheets(self):
        '''Se hereda el metodo para accionar un wizard y que el usuario agregue el monto de aprobacion para la solicitud'''
        return {'type': 'ir.actions.act_window',
                'res_model': 'expense.sheet.amount.approve.wizard',
                'view_mode': 'form',
                'target': 'new'}

    @api.multi
    def payment_expense_sheets(self):
        '''Se hereda el metodo para accionar un wizard y que el usuario agregue el monto de aprobacion para la solicitud'''
        self.write({'state':'done'})

    # Columns
    folio = fields.Char(string='Folio')
    date_request = fields.Datetime(string='Date request')
    state = fields.Selection(selection_add=[('denied', 'Denied')], track_visibility=True)
    amount_approved = fields.Monetary('Amount Approved')
