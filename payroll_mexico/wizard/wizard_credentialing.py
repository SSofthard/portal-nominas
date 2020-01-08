# -*- coding: utf-8 -*-

from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class hrEmployeeCredentialingWizard(models.TransientModel):
    _name = "hr.employee.credentialing.wizard"
    _description = 'Formulario de credencialización'

    #Columns
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    contracting_regime = fields.Selection([
        ('1', 'Assimilated to wages'),
        ('2', 'Wages and salaries'),
        ('3', 'Senior citizens'),
        ('4', 'Pensioners'),
        ('5', 'Free')], string='Regimen de contratación', required=True, default="2")
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Empleados a carnetizar')
    target_layout_id = fields.Many2one(comodel_name='ir.ui.view', string='Plantillas', domain="[('name','like','%credential%')]")

    @api.onchange('employer_register_id', 'contracting_regime', 'work_center_id','group_id')
    def onchange_fields_filters(self):
        contract = self.env['hr.contract']
        domain_employer_register = [('employer_register_id', '=', self.employer_register_id.id)] if self.employer_register_id else []
        domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)] if self.work_center_id else []
        domain= [
            ('state', '=', 'open'),
            ('employee_id.group_id', '=', self.group_id.id),
            ('contracting_regime', '=', self.contracting_regime)
        ]
        employees = contract.search_read(domain + domain_employer_register, ['employee_id', 'state'])
        employee_ids = []
        for employee in employees:
            employee_ids.append(employee['employee_id'][0])
        return {'domain': {'employee_ids': [('id', 'in', employee_ids)]}}


    def report_credentaling(self):
        '''

        '''
        vals = {
            'doc_ids':self.employee_ids._ids,
            'template_id':self.target_layout_id.key,
        }
        return self.env.ref('payroll_mexico.payroll_mexico_report_credentaling').report_action(self, data=vals)