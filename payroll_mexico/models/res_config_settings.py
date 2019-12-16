# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_default_input_id(self, fields):
        '''
        Este metodo permite obtener el parametro que se tiene en la configuracion actual
        :param fields:
        :return:
        '''
        default_account_id = False
        if 'default_input_id' in fields:
            default_input_id = self.env['ir.values'].get_default('hr.holidays.prorate', 'input_id',
                                                                   company_id=self.env.user.company_id.id)
        return {
            'default_input_id': default_input_id
        }

    @api.multi
    def set_default_input_id(self):
        '''
        Este metodo permite setear el valor una vez que la configuracion es guardada
        :return:
        '''
        for wizard in self:
            ir_values = self.env['ir.values']
            if self.user_has_groups('base.group_configuration'):
                ir_values = ir_values.sudo()
            ir_values.set_default('hr.holidays.prorate', 'input_id', wizard.default_input_id.id,
                                  company_id=self.env.user.company_id.id)

    tables_id = fields.Many2one(
        'tablas.cfdi', 'Tables',
        related='company_id.tables_id', readonly=False)
    default_input_id = fields.Many2one(comodel_name='hr.rule.input', default_model='hr.holidays.prorate', string='Entrada predeterminada para vacaciones')

class Company(models.Model):
    _inherit = 'res.company'

    tables_id = fields.Many2one(
        'tablas.cfdi', 'CFDI tables', readonly=False, invisible=True)
