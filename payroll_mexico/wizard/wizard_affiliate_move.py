# -*- coding: utf-8 -*-

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class hrEmployeeAffiliateExportTxt(models.TransientModel):
    _name = "hr.employee.affiliate.export.txt"
    _description = 'Exportar TXT Movimientos Afiliatorios'

    #Columns
    txt_file = fields.Binary('Descargar')
    file_name = fields.Char('Descargar')


class hrEmployeeAffiliateReport(models.TransientModel):
    _name = "hr.employee.affiliate.movements.report"
    _description = 'Reporte Movimientos Afiliatorios'

    #Columns
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=True)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    date_from = fields.Date(string="Date From", required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string="Date To", required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),)
    department_ids = fields.Many2many('hr.department', string='Departamento')
    job_ids = fields.Many2many('hr.job', string='Puesto de trabajo')

    @api.multi
    def report_print(self, data):
        self.ensure_one()
        domain = [
            ('date','>=', self.date_from),('date','<=', self.date_to),
            ('employee_id.group_id','=', self.group_id.id),
            ('employee_id.employer_register_id','=', self.employer_register_id.id),
        ]
        if self.department_ids:
            domain = [
                ('employee_id.department_id','in', self.department_ids.ids),
            ]
        if self.job_ids:
            domain = [
                ('employee_id.job_id','in', self.job_ids.ids),
            ]
        move_ids = self.env['hr.employee.affiliate.movements'].search(domain)
        if not move_ids:
            raise ValidationError(_('No se encontró información con los datos proporcionados.'))
        count_high = 0
        count_change = 0
        count_low = 0
        moves = {}
        employee_ids = []
        datas = []
        for move in move_ids:
            if move.type == '08':
                count_high += 1
            if move.type == '07':
                count_change += 1
            if move.type == '02':
                count_low += 1
            if move.employee_id.id not in employee_ids:
                employee_ids.append(move.employee_id.id)
            datas.append({
                'enrollment': move.employee_id.enrollment,
                'type_move': dict(move._fields['type']._description_selection(move.env)).get(move.type).upper(),
                'ssnid': move.employee_id.ssnid,
                'move_date': move.date,
                'employee_name': move.employee_id.complete_name.upper(),
                'reason_liquidation': move.reason_liquidation, 
                'rfc': move.employee_id.rfc,
                'sdi': move.salary,
                'type_employee': dict(move.employee_id._fields['type_worker']._description_selection(move.employee_id.env)).get(move.employee_id.type_worker).upper(),
                'date_admission': move.contract_id.date_start,
                'date_end': move.contract_id.date_end,
            })
        moves['total_employee'] = len(employee_ids)
        moves['count_high'] = count_high
        moves['count_change'] = count_change
        moves['count_low'] = count_low
        moves['group'] = self.group_id.name
        moves['date_from'] = self.date_from
        moves['date_to'] = self.date_to
        moves['datas'] = sorted(datas, key=lambda k: "%s %s" % (k['move_date'], k['enrollment']))
        data={
            'move_data': moves
        }
        return self.env.ref('payroll_mexico.action_affiliate_movements_report').with_context(from_transient_model=True).report_action(self, data=data)
