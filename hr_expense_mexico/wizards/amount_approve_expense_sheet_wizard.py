# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ExpenseSheetAmountApproveWizard(models.TransientModel):
    _name = 'expense.sheet.amount.approve.wizard'


    def _getfacetdefault(self):
        '''Este medoto busca por defecto el id de la facet de documentos Status, la busca mediante el id externo'''
        return self.env.ref('documents.documents_internal_status_folder').id


    #Columns
    amount_approve = fields.Float(string='Amount Approve')

    @api.multi
    def set_amount_approve(self):
        '''
        Este medoto agrega las estiquetas seleccionadas al documento
        :return:
        '''
        self.env[self.env.context['active_model']].browse(self.env.context['active_id']).approve_amount_expense_sheets(self.amount_approve)