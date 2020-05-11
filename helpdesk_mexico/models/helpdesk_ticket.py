# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError
from odoo.tools import pycompat

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Category")
    group_id = fields.Many2one('hr.group', "Grupo", store=True, required=False)
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', copy=False,
                               index=True, domain="[('team_ids', '=', team_id),('ticket_type_ids','in',ticket_type_id)]")
    
    
class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'
    
    ticket_type_ids = fields.Many2many('helpdesk.ticket.type', string='Ticket type')

class HelpdeskTicketTypeInherit(models.Model):
    _inherit = 'helpdesk.ticket.type'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('helpdesk.ticket.type', string='Parent')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('helpdesk.ticket.type', 'parent_id', 'Child Categories')
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name
    
    @api.multi
    def name_get(self):
        result = []
        for tickey_type in self:
            result.append((tickey_type.id, "%s" % (tickey_type.complete_name)))
        return result
