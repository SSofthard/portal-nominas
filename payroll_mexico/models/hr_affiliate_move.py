# -*- coding: utf-8 -*-

import io
import base64

from datetime import date, datetime, time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class irAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    affiliate_move_id = fields.Many2one('hr.employee.affiliate.move', invisible=True)


class HrEmployeeAffiliateMove(models.Model):
    _name = "hr.employee.affiliate.move"
    _description = "Movimientos Afiliatorios"

    @api.multi
    def _document_count(self):
        for each in self:
            document_ids = self.env['ir.attachment'].sudo().search([('employee_id', '=', each.id)])
            each.document_count = len(document_ids)

    @api.multi
    def document_view(self):
        self.ensure_one()
        domain = [('affiliate_move_id', '=', self.id)]
        return {
            'name': _('Documentos Movimientos Afiliatorios'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click para Crear Nuevos Documentos
                        </p>'''),
            'limit': 80,
            'context': "{'default_affiliate_move_id': '%s'}" % self.id
        }

    #Columns
    employer_register_id = fields.Many2one('res.employer.register', "Registro patronal",
    required=True, readonly=True, states={'draft': [('readonly', False)]})
    type_move = fields.Selection([
        ('1', 'Altas y/o Reingresos'),
        ('2', 'Bajas'),
        ('3', 'Modificaciones'),
        ], string='Movimiento afiliatorio', default="1", required=True,
        readonly=True, states={'draft': [('readonly', False)]},)
    date_from = fields.Date(
        'Start Date', required=True, index=True, copy=False,
        default=date.today(),
        readonly=True, states={'draft': [('readonly', False)]},)
    date_to = fields.Date(
        'End Date', required=True, index=True, copy=False,
        default=date.today(),
        readonly=True, states={'draft': [('readonly', False)]},)
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Open'),
        ], string='Status', index=True, readonly=True, default='draft', copy=False)
    movements_ids = fields.Many2many('hr.employee.affiliate.movements',
        'hr_employee_affiliate_movements_rel', 'move_id', 'affiliate_movements_id',
        string='Líneas de Movimientos Afiliatorios',
        readonly=True, states={'draft': [('readonly', False)]},)
    document_count = fields.Integer(compute='_document_count', string='# Documentos')

    @api.onchange('movements_ids')
    def _onchange_movements_ids(self):
        for move in self:
            for movements in move.movements_ids:
                movements.filtered(lambda mov: mov.state == 'draft').write({'state': 'generated'})
            print (move.movements_ids)
            print (move.movements_ids)
            print (move.movements_ids)
            print (move.movements_ids)
    
    # ~ @api.multi
    # ~ def unlink(self):
        # ~ for move in self:
            # ~ for movements in move.movements_ids:
                # ~ movements.write({'state': 'draft'})
        # ~ if self.filtered(lambda r: r.invoice_id and r.invoice_id.state != 'draft'):
            # ~ raise UserError(_('You can only delete an invoice line if the invoice is in draft state.'))
        # ~ return super(AccountInvoiceLine, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        for move in self:
            type_move = u'{0}'.format(dict(move._fields['type_move']._description_selection(self.env)).get(move.type_move)),
            name = '%s %s %s-%s' %(
                type_move,
                move.employer_register_id.employer_registry,
                move.date_from,
                move.date_to,)
            result.append((move.id, name))
        return result

    @api.multi
    def action_print_txt(self):
        '''
        Este metodo es para imprimir el txt de los movimientso afiliatorios
        '''
        output = io.BytesIO()
        print ('imprimir txt')
        print ('imprimir txt')
        print ('imprimir txt')
        print ('imprimir txt')
        f_name = 'Movimientos Afiliatorios: %s - %s' % (self.date_from, self.date_to)
        content = ''
        for move in self.movements_ids:
            
            content = '%s\t%s\t%s\t%s' %(self.employer_register_id.employer_registry,
                move.employee_id.ssnid if move.employee_id.ssnid else 'JJJ',
                move.employee_id.last_name if move.employee_id.last_name else 'JJJ',
                move.employee_id.mothers_last_name if move.employee_id.mothers_last_name else 'JJJ',)
        print (type(content))
        data = base64.encodebytes(bytes(content, 'utf-8'))
        export_id = self.env['hr.employee.affiliate.export.txt'].create(
            {'txt_file': data, 'file_name': f_name + '.txt'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.affiliate.export.txt',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': export_id.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_move_open(self):
        self.filtered(lambda mov: mov.state == 'draft').write({'state': 'open'})

