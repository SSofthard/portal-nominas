# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardExpiredContracts(models.TransientModel):
    _name = "wizard.expired.contracts"

    date_from = fields.Date('Vence Desde', required=False)
    date_to = fields.Date('Vence Hasta', required=False)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    
    @api.multi
    def report_print(self, data):
        date_from = self.date_from
        date_to = self.date_to
        domain_register = []
        domain_work_center = []
        domain_date = []
        list_group = []
        list_code = []
        list_name = []
        list_imss = []
        list_curp = []
        list_rfc = []
        list_job = []
        list_department = []
        list_code_contract = []
        list_type = []
        list_regime = []
        list_date_start = []
        list_date_end = []
        list_status = []
        contract=self.env['hr.contract']
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        if date_from and date_to:
            domain_date = [('date_end','>=',date_from),('date_end','<=',date_to)]
        contract_ids=contract.search([('employee_id.group_id','=',self.group_id.id)] + domain_register + domain_work_center + domain_date)
        if not contract_ids:
            raise UserError(_("No se encontró información con los datos proporcionados."))
        data={
            'contract_ids': contract_ids._ids,
            'date_from': date_from,
            'date_to': date_to,
            'register': self.employer_register_id.employer_registry ,
            'work_center': self.work_center_id.name,
            'group': self.group_id.name,
        }
        return self.env.ref('payroll_mexico.report_expired_contracts').report_action(self, data=data)
        
    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))
