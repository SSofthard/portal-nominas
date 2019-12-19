# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardExpiredContracts(models.TransientModel):
    _name = "wizard.expired.contracts"

    date_from = fields.Date('Desde', required=True)
    date_to = fields.Date('Hasta', required=True)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    group_id = fields.Many2one('hr.group', "Grupo", required=False)
    
    @api.multi
    def report_print(self, data):
        print ("funciona")
        date_from = self.date_from
        date_to = self.date_to
        domain = []
        domain_work_center = []
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
        if self.group_id:
            domain = [('employee_id.group_id', '=', self.group_id.id)]
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        contract_ids=contract.search([('date_end','>=',date_from),('date_end','<=',date_to)] + domain + domain_work_center + domain_register)
        for i in contract_ids:
            group = (i.employee_id.group_id.name)
            code = (i.employee_id.enrollment)
            name = (i.employee_id.name)
            imss = (i.employee_id.ssnid)
            curp = (i.employee_id.curp)
            rfc = (i.employee_id.rfc)
            job = (i.employee_id.job_id.name)
            department = (i.employee_id.department_id.name)
            code_contract = (i.code)
            type_contract = (i.type_id.name)
            regime = dict(i._fields['contracting_regime']._description_selection(self.env)).get(i.contracting_regime)
            date_start = (i.date_start)
            date_end = (i.date_end)
            status = dict(i._fields['state']._description_selection(self.env)).get(i.state)
            list_group.append(group)
            list_code.append(code)
            list_name.append(name)
            list_imss.append(imss)
            list_curp.append(curp)
            list_rfc.append(rfc)
            list_job.append(job)
            list_department.append(department)
            list_code_contract.append(code_contract)
            list_type.append(type_contract)
            list_regime.append(regime)
            list_date_start.append(date_start)
            list_date_end.append(date_end)
            list_status.append(status)
        data['date_from'] = date_from
        data['date_to'] = date_to
        data['group'] = self.group_id.name
        data['register'] = self.employer_register_id.employer_registry
        data['work_center'] = self.work_center_id.name
        data['code'] = list_code
        data['name'] = list_name
        data['imss'] = list_imss
        data['curp'] = list_curp
        data['rfc'] = list_rfc
        data['job'] = list_job
        data['department'] = list_department
        data['code_contract'] = list_code_contract
        data['type'] = list_type
        data['regime'] = list_regime
        data['date_start'] = list_date_start
        data['date_end'] = list_date_end
        data['status'] = list_status
        print ("funciona")
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
