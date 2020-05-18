# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError
from odoo.tools import pycompat

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    
    @api.depends('assign_date','last_assign_date')
    def _compute_assign_hours(self):
        for ticket in self:
            if not ticket.create_date:
                continue;
            time_difference = datetime.datetime.now() - fields.Datetime.from_string(ticket.create_date)
            time_difference2 = datetime.datetime.now() - fields.Datetime.from_string(ticket.last_assign_date or ticket.create_date)
            ticket.assign_hours = (time_difference.seconds) / 3600 + time_difference.days * 24
            ticket.last_assign_hours = (time_difference2.seconds) / 3600 + time_difference2.days * 24

    @api.depends('close_date','last_close_hours')
    def _compute_close_hours(self):
        for ticket in self:
            if not ticket.create_date:
                continue;
            time_difference = datetime.datetime.now() - fields.Datetime.from_string(ticket.create_date)
            time_difference2 = datetime.datetime.now() - fields.Datetime.from_string(ticket.last_assign_date or ticket.create_date)
            ticket.last_close_hours = (time_difference2.seconds) / 3600 + time_difference2.days * 24
            
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Category")
    group_id = fields.Many2one('hr.group', "Grupo", store=True, required=False)
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', copy=False,
                               index=True, domain="[('team_ids', '=', team_id),('ticket_type_ids','in',ticket_type_id)]")
    last_assign_date = fields.Datetime(string='Last assignment date', track_visibility='onchange')
    last_assign_hours = fields.Integer(string='Last assignment time (hours)', compute='_compute_assign_hours')
    last_close_date = fields.Datetime(string='Closing date of last assignment', track_visibility='onchange')
    last_close_hours = fields.Integer(string='Last assignment open time (hours)', compute='_compute_close_hours', store=True)
    
    def send_reminder_email_cron(self):
        tiket_ids = self.search([('stage_id.is_close','=',False)])
        for tiket in tiket_ids:
            tiket.send_reminder_email()
        return
    
    @api.multi
    def send_reminder_email(self):
        for ticket in self:
            if int(ticket.last_assign_hours) >= int(ticket.team_id.reminder_time) and not ticket.stage_id.is_close:
                post_kwargs = {'auto_delete_message': True, 
                               'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'), 
                               'notif_layout': 'mail.mail_notification_light',
                               }
                template_id = self.env['ir.model.data'].xmlid_to_res_id('helpdesk_mexico.assigned_ticket_reminder_request_email_template')
                ticket.message_post_with_template(template_id,**post_kwargs)
                Mail = self.env['mail.mail'].search([('model','=','helpdesk.ticket'),('res_id','=',ticket.id),('state','=','outgoing')])
                Mail.send()
        return
    
    @api.multi
    def write(self, vals):
        # we set the assignation date (assign_date) to now for tickets that are being assigned for the first time
        # same thing for the closing date
        now = datetime.datetime.now()
        assigned_tickets = closed_tickets = self.browse()
        if vals.get('user_id'):
            assigned_tickets = self.filtered(lambda ticket: not ticket.assign_date)
            vals['last_assign_date'] = now
        if vals.get('stage_id') and self.env['helpdesk.stage'].browse(vals.get('stage_id')).is_close:
            closed_tickets = self.filtered(lambda ticket: not ticket.close_date)
            vals['last_close_date'] = now
        res = super(HelpdeskTicket, self - assigned_tickets - closed_tickets).write(vals)
        res &= super(HelpdeskTicket, assigned_tickets - closed_tickets).write(dict(vals, **{
            'assign_date': now,
        }))
        res &= super(HelpdeskTicket, closed_tickets - assigned_tickets).write(dict(vals, **{
            'close_date': now,
        }))
        res &= super(HelpdeskTicket, assigned_tickets & closed_tickets).write(dict(vals, **{
            'assign_date': now,
            'close_date': now,
        }))

        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])

        return res
    
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

class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"
    
    reminder_time = fields.Integer('Reminder time (Hours)', default=5)
