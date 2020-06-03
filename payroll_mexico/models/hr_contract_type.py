# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

class ContractType(models.Model):

    _inherit = 'hr.contract.type'

    code = fields.Char('Code', required=True)
    key = fields.Char('Code Layout', required=False, readonly=True)
    report_id = fields.Many2one('ir.actions.report',domain=[('model','=','hr.contract')],string="Report",)
    type = fields.Selection([
        ('with_seniority', 'With Seniority'),
        ('without_seniority', 'Without Seniority'),
        ('na', 'No aplica'),
    ],default="na")

    def _get_name(self):
        if self.type in ['with_seniority','without_seniority']:
            if self.type == 'with_seniority':
                value = _('With Seniority')
            if self.type == 'without_seniority':
                value = _('Without Seniority') 
            name = "%s ‒ %s" % (self.name, value)
        else:
            name = "%s" % (self.name)
        return name

    @api.multi
    def name_get(self):
        res = []
        for ct in self:
            name = ct._get_name()
            res.append((ct.id, name))
        return res

    @api.multi
    def set_key(self):
        types_ids = self.search([('key','=',False)])
        for type in types_ids:
            type.key = self.env['ir.sequence'].next_by_code('hr.contract.type')

    @api.model
    def create(self, vals):
        vals['key'] = self.env['ir.sequence'].next_by_code('hr.contract.type')
        result = super(ContractType, self).create(vals)
        return result
