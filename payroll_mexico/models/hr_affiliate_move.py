# -*- coding: utf-8 -*-

import io
import base64

from datetime import date, datetime, time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class HrEmployeeAffiliateMove(models.Model):
    _name = "hr.employee.affiliate.move"
    _description = "Movimientos Afiliatorios"

    #Columns
    employer_register_id = fields.Many2one('res.employer.register', "Registro patronal", required=True)
    type_move = fields.Selection([
        ('1', 'Altas y/o Reingresos'),
        ('2', 'Bajas'),
        ('3', 'Modificaciones'),
        ], string='Movimiento afiliatorio', default="1", required=True)
    date_from = fields.Date(
        'Start Date', required=True, index=True, copy=False,
        default=date.today())
    date_to = fields.Date(
        'End Date', required=True, index=True, copy=False,
        default=date.today())
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Open'),
            ('done', 'Done'),
            ('cancel', 'Cancel'),
        ], string='Status', index=True, readonly=True, default='draft',
        copy=False)

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
        content = 'prueba\tprueba\n'
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
        self.filtered(lambda mov: mov.state not in ['open','done']).write({'state': 'open'})

