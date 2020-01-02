# -*- coding: utf-8 -*-

import io
import base64

from datetime import date, datetime, time, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError, UserError


class EmployeeAffiliateMovements(models.Model):
    _name = 'hr.employee.affiliate.movements'
    _rec_name = 'type'

    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    type = fields.Selection([
        ('08', 'Alta o Reingreso'),
        ('07', 'Cambio de salario'),
        ('02', 'Baja'),
    ], string='Type', index=True, default='08')
    date = fields.Date(string="Date")
    reason_liquidation = fields.Selection([
            ('1', 'TERMINACIÓN DE CONTRATO'),
            ('2', 'SEPARACIÓN VOLUNTARIA'),
            ('3', 'ABANDONO DE EMPLEO'),
            ('4', 'DEFUNCIÓN'),
            ('7', 'AUSENTISMOS'),
            ('8', 'RESICIÓN DE CONTRATO'),
            ('9', 'JUBILACIÓN'),
            ('A', 'PENSIÓN'),
            ('5', 'CLAUSURA'),
            ('6', 'OTROS')], 
            string='Reason for liquidation')
    wage = fields.Float('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    salary   = fields.Float('SDI', digits=(16, 2), help="SDI")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('approved', 'Approved'),
    ], string='State', default = 'draft')
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free'),
        ], string='Contracting Regime', related="contract_id.contracting_regime")

    def action_move_draft(self):
        self.filtered(lambda mov: mov.state == 'generated').write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for movements in self:
            if movements.state not in ['draft']:
                raise UserError(_('You cannot delete affiliate movements that are not in "Draft" status.'))
        return super(EmployeeAffiliateMovements, self).unlink()

class ChangeOfJob(models.Model):
    _name = 'hr.change.job'
    _rec_name = "id"
    _order = 'date_from desc'

    contract_id = fields.Many2one('hr.contract',string='Contracto',store=True, readonly=True)
    employee_id = fields.Many2one('hr.employee',string="Employee", readonly=True)
    date_from = fields.Date(string='Desde', readonly=True)
    date_to = fields.Date(string='Hasta', readonly=True)
    job_id = fields.Many2one('hr.job', string='Puesto de trabajo', readonly=True)
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free'),
        ], string='Contracting Regime', related="contract_id.contracting_regime")

class Contract(models.Model):
    _inherit = 'hr.contract'
    
    # Translate fields
    reported_to_secretariat = fields.Boolean('Social Secretariat',
        help='Green this button when the contract information has been transfered to the social secretariat.')
    
    @api.model
    def create(self, vals):
        res = super(Contract, self).create(vals)
        val = {
            'contract_id':res.id,
            'employee_id':res.employee_id.id,
            'type':'08',
            'date':res.previous_contract_date or res.date_start,
            'wage':res.wage,
            'salary':res.integral_salary,
        }
        self.env['hr.employee.affiliate.movements'].create(val)
        val_job = {
                'employee_id': res.employee_id.id,
                'contract_id': res.id,
                'job_id': res.job_id.id,
                'date_from': res.date_start,
                'date_to': False,
                
        }
        self.env['hr.change.job'].create(val_job)
        return res
        
    @api.multi
    def write(self, vals):
        affiliate_movements = self.env['hr.employee.affiliate.movements'].search([('contract_id','=',self.id),('type','=','08'),('contracting_regime','=','2')])
        res= super(Contract, self).write(vals)
        if self.contracting_regime != '2':
            if affiliate_movements:
                raise UserError(_('You cannot change the contracting regime of a contract with affiliated movement.'))
            else:
                affiliate_movements_other = self.env['hr.employee.affiliate.movements'].search([('contract_id','=',self.id),('type','=','08'),('contracting_regime','in',['1','3','4','5'])])
                val = {
                    'contract_id':self.id,
                    'employee_id':self.employee_id.id,
                    'type':'08',
                    'date':self.previous_contract_date or self.date_start,
                    }
                if affiliate_movements_other:
                    affiliate_movements_other.write(val)
                else:
                    val['wage'] = self.wage
                    val['salary'] = self.integral_salary
                    self.env['hr.employee.affiliate.movements'].create(val)
        else:
            val = {
                'contract_id':self.id,
                'employee_id':self.employee_id.id,
                'type':'08',
                'date':self.previous_contract_date or self.date_start,
                }
            if affiliate_movements:
                if affiliate_movements.state in ['approved']:
                    raise UserError(_('You cannot change the date of discharge of a contract with approved sharpening motion.'))
                affiliate_movements.write(val)
            else:
                val['wage'] = self.wage
                val['salary'] = self.integral_salary
                self.env['hr.employee.affiliate.movements'].create(val)
        return res

    @api.constrains('wage')
    def _check_wage(self):
        for contract in self:
            if contract.wage <= 0:
                raise ValidationError(_('You cannot create a contract with a salary less than or equal to zero.'))


class irAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    affiliate_move_id = fields.Many2one('hr.employee.affiliate.move', invisible=True)


class HrEmployeeAffiliateMove(models.Model):
    _name = "hr.employee.affiliate.move"
    _description = "Generar TXT Movimientos Afiliatorios"

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
        ('08', 'Altas y/o Reingresos'),
        ('07', 'Modificaciones'),
        ('02', 'Bajas'),
        ], string='Movimiento afiliatorio', required=True,
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
            ('waiting', 'Waiting Confirmation'),
            ('approved', 'Approved'),
        ], string='Status', index=True, readonly=True, default='draft', copy=False)
    movements_ids = fields.Many2many('hr.employee.affiliate.movements',
        'hr_employee_affiliate_movements_rel', 'move_id', 'affiliate_movements_id',
        string='Líneas de Movimientos Afiliatorios',
        readonly=True, states={'draft': [('readonly', False)]},)
    document_count = fields.Integer(compute='_document_count', string='# Documentos')

    def search_movements(self):
        return self.env['hr.employee.affiliate.movements'].search([
            ('type','=',self.type_move),
            ('state','=','draft'),
            ('employee_id.employer_register_id','=',self.employer_register_id.id),
            ('date','>=',self.date_from),
            ('date','<=',self.date_to),
            ]).ids

    @api.multi
    def get_movements(self):
        movements_ids = self.search_movements()
        if movements_ids:
            self.with_context(movements=True).movements_ids = [[6, 0, movements_ids]]
            self.movements_ids.with_context(movements=True).write({'state': 'generated'})
        else:
            raise UserError(_('No se encontró información con los datos proporcionados.'))

    @api.multi
    def name_get(self):
        result = []
        for move in self:
            type_move = dict(move._fields['type_move']._description_selection(move.env)).get(move.type_move)
            name = '%s %s %s-%s' %(
                move.employer_register_id.employer_registry,
                type_move,
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
        type_move = dict(self._fields['type_move']._description_selection(self.env)).get(self.type_move)
        f_name = 'Movimientos Afiliatorios de: %s %s - %s' % (type_move, self.date_from, self.date_to)
        content = ''
        for move in self.movements_ids.filtered(lambda mov: mov.state == 'generated'):
            if self.type_move == '08':
                # TXT Para movimientos afiliatorios de Alta o Reingreso
                content += '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s\n' %(self.employer_register_id.employer_registry.ljust(11),  # 1 Registro Patronal len(11)
                    move.employee_id.ssnid.ljust(11) if move.employee_id.ssnid else ' '.ljust(11),              # 2 Número de seguridad social len(11)
                    move.employee_id.last_name.ljust(27) if move.employee_id.last_name else ' '.ljust(27),      # 3 Primer apellido len(27)
                    move.employee_id.mothers_last_name.ljust(27) if move.employee_id.mothers_last_name else ' '.ljust(27),  # 4 Segundo apellido len(27)
                    move.employee_id.name.ljust(27) if move.employee_id.name else ' '.ljust(27),                # 5 Nombre(s) len(27)
                    str(move.salary).replace('.','').zfill(6),                                                  # 6 Salario base de cotización len(6)
                    ' '.ljust(6),                                                                               # 7 Filler len(6)
                    move.employee_id.type_worker if move.employee_id.type_worker else ' '.ljust(1),             # 8 Tipo de trabajador len(1)
                    move.employee_id.salary_type if move.employee_id.salary_type else ' '.ljust(1),             # 9 Tipo de salario len(1)
                    move.employee_id.working_day_week if move.employee_id.working_day_week else ' '.ljust(1),   # 10 Semana o jornada reducida len(1)
                    move.date.strftime('%d%m%Y'),                                                               # 11 Fecha de movimiento len(8) (DDMMAAAA)
                    '??'.ljust(3),                                                                              # 12 Unidad de medicina familiar len(3)
                    ' '.ljust(2),                                                                               # 13 Filler len(2)
                    move.type,                                                                                  # 14 Tipo de movimiento len(2)
                    'Guia?'.ljust(5),                                                                           # 15 Guía - Número asignado por la Subdelegación len(5)
                    move.employee_id.enrollment.ljust(10) if move.employee_id.enrollment else ' '.ljust(10),    # 16 Clave del trabajador len(10)
                    ' '.ljust(1),                                                                               # 17 Filler len(1)
                    move.employee_id.curp.ljust(18) if move.employee_id.curp else ' '.ljust(18),                # 18 Clave del trabajador len(18)
                    '9'.ljust(1),                                                                               # 19 Identificador del formato len(1)
                )
            if self.type_move == '07':
                # TXT Para movimientos afiliatorios de modificación de salarios
                content += '%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s\n' %(
                    self.employer_register_id.employer_registry.ljust(11),                                      # 1 Registro Patronal len(11)
                    move.employee_id.ssnid.ljust(11) if move.employee_id.ssnid else ' '.ljust(11),              # 2 Número de seguridad social len(11)
                    move.employee_id.last_name.ljust(27) if move.employee_id.last_name else ' '.ljust(27),      # 3 Primer apellido len(27)
                    move.employee_id.mothers_last_name.ljust(27) if move.employee_id.mothers_last_name else ' '.ljust(27),  # 4 Segundo apellido len(27)
                    move.employee_id.name.ljust(27) if move.employee_id.name else ' '.ljust(27),                # 5 Nombre(s) len(27)
                    str(move.salary).replace('.','').zfill(6),                                                  # 6 Salario base de cotización len(6)
                    ' '.ljust(7),                                                                               # 7 Filler len(6)
                    move.employee_id.salary_type if move.employee_id.salary_type else ' '.ljust(1),             # 8 Tipo de salario len(1)
                    move.employee_id.working_day_week if move.employee_id.working_day_week else ' '.ljust(1),   # 9 Semana o jornada reducida len(1)
                    move.date.strftime('%d%m%Y'),                                                               # 10 Fecha de movimiento len(8) (DDMMAAAA)
                    ' '.ljust(5),                                                                               # 11 Filler len(5)
                    move.type,                                                                                  # 12 Tipo de movimiento len(2)
                    'Guia?'.ljust(5),                                                                           # 13 Guía - Número asignado por la Subdelegación len(5)
                    move.employee_id.enrollment.ljust(10) if move.employee_id.enrollment else ' '.ljust(10),    # 14 Clave del trabajador len(10)
                    ' '.ljust(1),                                                                               # 15 Filler len(1)
                    move.employee_id.curp.ljust(18) if move.employee_id.curp else ' '.ljust(18),                # 16 Clave del trabajador len(18)
                    '9'.ljust(1),                                                                               # 17 Identificador del formato len(1)
                )
            if self.type_move == '02':
                # TXT Para movimientos afiliatorios de baja
                content += '%s%s%s%s%s%s%s%s%s%s%s%s%s%s\n' %(self.employer_register_id.employer_registry.ljust(11),  # 1 Registro Patronal len(11)
                    move.employee_id.ssnid.ljust(11) if move.employee_id.ssnid else ' '.ljust(11),              # 2 Número de seguridad social len(11)
                    move.employee_id.last_name.ljust(27) if move.employee_id.last_name else ' '.ljust(27),      # 3 Primer apellido len(27)
                    move.employee_id.mothers_last_name.ljust(27) if move.employee_id.mothers_last_name else ' '.ljust(27),  # 4 Segundo apellido len(27)
                    move.employee_id.name.ljust(27) if move.employee_id.name else ' '.ljust(27),                # 5 Nombre(s) len(27)
                    '0'.zfill(15),                                                                              # 6 Filler (Ceros) len(15)
                    move.date.strftime('%d%m%Y'),                                                               # 7 Fecha de movimiento len(8) (DDMMAAAA)
                    ' '.ljust(5),                                                                               # 8 Filler len(6)
                    move.type,                                                                                  # 9 Tipo de movimiento len(2)
                    'Guia?'.ljust(5),                                                                           # 10 Guía - Número asignado por la Subdelegación len(5)
                    move.employee_id.enrollment.ljust(10) if move.employee_id.enrollment else ' '.ljust(10),    # 11 Clave del trabajador len(10)
                    move.reason_liquidation,                                                                    # 12 Causa de la baja len(1)
                    ' '.ljust(18),                                                                              # 13 Filler len(18)
                    '9'.ljust(1),                                                                               # 14 Identificador del formato len(1)
                )
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

    def action_move_waiting(self):
        self.filtered(lambda mov: mov.state == 'draft').write({'state': 'waiting'})

    def action_move_draft(self):
        move_draft = self.filtered(lambda mov: mov.state == 'waiting')
        move_draft.write({'state': 'draft'})
        move_draft.movements_ids.write({'state': 'draft'})
        
    def action_move_approved(self):
        move_approved = self.filtered(lambda mov: mov.state == 'waiting')
        move_approved.write({'state': 'approved'})
        move_approved.movements_ids.filtered(lambda mov: mov.state == 'generated').write({'state': 'approved'})
        move_cut = move_approved.movements_ids.filtered(lambda mov: mov.state == 'draft')
        for cut in move_cut:
            move_approved.movements_ids = [(3,cut.id,0)]

    @api.multi
    def write(self, values):
        if not self.env.context.get('movements') and 'movements_ids' in values and self.state == 'draft':
            no_validate_move = [x for x in self.search_movements() if x not in values.get('movements_ids')[0][2]]
            self.env['hr.employee.affiliate.movements'].search([('id','in', no_validate_move)]).write({'state': 'draft'})
        return super(HrEmployeeAffiliateMove, self).write(values)
