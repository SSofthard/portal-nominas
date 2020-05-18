# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError, AccessError
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
    
    def send_escalation_notification_mail(self):
        company = self.env['res.company'].search([('id','=',self.env.user.company_id.id)])
        url = self.env['ir.config_parameter'].search([('key','=','web.base.url')]).value
        team_ids = self.env['helpdesk.team'].search([])
        for team in team_ids:
            body_html = '<table border="0" width="100%" cellpadding="0" bgcolor="#ededed" style="padding: 20px; background-color: #ededed; border-collapse:separate;" summary="o_mail_notification">\
                                <tbody>\
                                    <tr>\
                                        <td align="center" style="min-width: 590px;">\
                                            <table width="590" border="0" cellpadding="0" bgcolor="#875A7B" style="min-width: 590px; background-color: #414141; padding: 20px; border-collapse:separate;">\
                                                <tbody>\
                                                    <tr>\
                                                        <td valign="middle" align="left">\
                                                            <span style="font-size:16px; color:white; font-weight: bold;">Solicitudes de Servicio</span>\
                                                        </td>\
                                                        <td valign="middle" align="right">\
                                                        <img style="padding:0px;margin:0px;height:48px;color:white;" src="/logo.png?company='+str(company.id)+'" alt="'+company.name+'" class="CToWUd">\
                                                    </td>\
                                                    </tr>\
                                                </tbody>\
                                            </table>\
                                        </td>\
                                    </tr>\
                                    <tr>\
                                    <td align="center" style="min-width: 590px;">\
                                        <table width="590" border="0" cellpadding="0" bgcolor="#ffffff" style="min-width: 590px; background-color: rgb(255, 255, 255); padding: 20px; border-collapse:separate;">\
                                            <tbody>\
                                                <tr>\
                                                <td valign="top" style="font-family:Arial,Helvetica,sans-serif; color: #555; font-size: 14px;">\
                                                    <div>\
                                                        Estimado(s),<br><br>\
                                                        Las solicitudes que se muestran a continuación se encuentran en espera de atencion por parte de los Analistas del Equipo <strong>'+str(team.name)+'</strong> con tiempos que superan las '+str(team.reminder_time_escalation)+' Horas.<br><br>'
            
            tiket_ids = self.search([('stage_id.is_close','=',False),('team_id','=',team.id)])
            head = True
            cont = 0
            for ticket in tiket_ids:
                if int(ticket.last_assign_hours) >= int(ticket.team_id.reminder_time_escalation):
                    cont += 1
                    if head:
                        head = False
                        body_html += '<table class="table table-hover" border="0" width="100%" summary="o_mail_notification">\
                                     <thead style="color:#FFFFFF; padding: 20px; background-color: #414141; border-collapse:separate;">\
                                     <tr>\
                                     <th>N°</th>\
                                     <th>Solicitud</th>\
                                     <th>Usuario Asignado</th>\
                                     <th>Horas</th>\
                                     </tr>\
                                     </thead>'
                    body_html += '<tbody style="padding: 20px; border-collapse:separate;">\
                                 <tr>\
                                 <td style="text-align:center">'+str(cont)+'</td>\
                                 <td style="text-align:center">'+ticket.name+'</td>'
                    if ticket.user_id:
                        body_html += '<td style="text-align:center">'+ticket.user_id.name+'</td>\
                                     <td style="text-align:center">'+str(ticket.last_assign_hours)+'</td>'
                    else:
                        body_html += '<td style="text-align:center">No Asignado</td>\
                                     <td style="text-align:center">'+str(ticket.last_assign_hours)+'</td>'
                    body_html += '</tr>'
            body_html += '</tbody>\
                         </table><br><br>\
                        Gracias,<br><br>\
                        <center>\
                        <a href="'+url+'" style="background-color: #d7b65d; padding: 20px; text-decoration: none; color: #fff; border-radius: 5px; font-size: 16px;" >Portal de Gestión de Nómina</a>\
                        </center>\
                        </div>\
                        </td>\
                        </tr></tr>\
                        <tr>\
                        <td align="center" style="min-width: 590px;">\
                            <table width="590" border="0" cellpadding="0" bgcolor="#875A7B" style="min-width: 590px; background-color: #414141; padding: 20px; border-collapse:separate;">\
                            <tbody><tr>\
                            <td valign="middle" align="left" style="color: #fff; padding-top: 10px; padding-bottom: 10px; font-size: 12px;">\
                                '+company.name.upper()+'<br><p></p><p>\
                              </p></td>\
                              </tr>\
                              </tbody></table>\
                            </td>\
                          </tr>\
                        </tbody>\
                        </table>\
                        </td></tr>\
                        </tbody>\
                        </table>\
                        </body>\
                        </html>'
            if team.users_notification_ids:
                list_recipient = []
                for user in team.users_notification_ids:
                    list_recipient.append(user.partner_id.id)
                mail_validate = self.env['mail.mail'].create({
                                        'recipient_ids':[[6, False, list_recipient]],
                                        'subject':'Notificación! Solicitudes de servicio sin atención.',
                                        'body_html':body_html,
                                        })
                mail_validate.send()
        return
        
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
    
    @api.multi
    def unlink(self):
        raise UserError(_("Cannot delete service request records."))
        return super(HelpdeskTicket, self).unlink()
    
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
    reminder_time_escalation = fields.Integer('Reminder time (Hours)', default=5)
    users_notification_ids = fields.Many2many('res.users', 'helpdesk_team_user','team_id', 'user_id', string='Notification to Users', domain=lambda self: [('groups_id', 'in', self.env.ref('helpdesk.group_helpdesk_user').id)])
