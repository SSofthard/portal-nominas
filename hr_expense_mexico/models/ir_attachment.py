# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _description = 'Document'
    _inherit = ['ir.attachment']

    @api.model_create_multi
    def create(self, vals_list):
        for vals_dict in vals_list:
            if vals_dict.get('res_model')=='hr.expense':
                vals_dict.update({'tag_ids':[(0, False, self.env.ref('documents.documents_hr_status_tc').id)]})
        return super(IrAttachment, self).create(vals_list)

