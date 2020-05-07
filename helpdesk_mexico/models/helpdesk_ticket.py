# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError
from odoo.tools import pycompat

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    group_id = fields.Many2one('hr.group', "Grupo", store=True, required=False)
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', copy=False,
                               index=True, domain="[('team_ids', '=', team_id),('ticket_type_ids','in',ticket_type_id)]")
    
    
class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'
    
    ticket_type_ids = fields.Many2many('helpdesk.ticket.type', string='Ticket type')
