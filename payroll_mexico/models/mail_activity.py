# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.



from odoo import api, exceptions, fields, models, _


class MailActivity(models.Model):
    _inherit = 'mail.activity'
    
    user_id = fields.Many2one(
        'res.users', 'Assigned to',
        default=lambda self: self.env.user,
        # domain=lambda self: [('groups_id', 'in', [self.env.ref('payroll_mexico.group_payroll_manager').id,
        #                                          self.env.ref('payroll_mexico.group_payroll_analyst').id,
        #                                          self.env.ref('payroll_mexico.group_account_executive').id,
        #                                          self.env.ref('payroll_mexico.group_commercial_executive').id]
        #                                          )],
        index=True, required=True)
