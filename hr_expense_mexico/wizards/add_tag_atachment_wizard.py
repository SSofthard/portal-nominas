# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AddTagAtachmentWizard(models.TransientModel):
    _name = 'wizard.attachment.tag'


    def _getfacetdefault(self):
        '''Este medoto busca por defecto el id de la facet de documentos Status, la busca mediante el id externo'''
        return self.env.ref('documents.documents_internal_status_folder').id


    #Columns
    tag_ids = fields.Many2many(comodel_name='documents.tag')
    facet_id = fields.Many2one(comodel_name='documents.facet', default=lambda self: self._getfacetdefault())

    @api.multi
    def add_document_tag(self):
        '''
        Este medoto agrega las estiquetas seleccionadas al documento
        :return:
        '''
        self.env[self.env.context['active_model']].browse(self.env.context['active_id']).tag_ids=self.tag_ids
        return True