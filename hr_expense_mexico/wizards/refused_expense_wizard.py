# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RefusedExpenseWizard(models.TransientModel):
    _name = 'refused.expense.wizard'


    #Columns
    description = fields.Text(string='Reason of refuse')

    @api.multi
    def save(self):
        '''
        Este medoto agrega las estiquetas seleccionadas al documento
        :return:
        '''
        self.env[self.env.context['active_model']].browse(self.env.context['active_id']).write({'state':'refused',
                                                                                                'description':('Rechazado por: %s'%self.description),
                                                                                                'date_checking': fields.Date.context_today(self)
                                                                                                })