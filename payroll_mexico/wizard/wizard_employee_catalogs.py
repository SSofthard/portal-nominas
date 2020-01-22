# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class WizardEmployeeCatalogs(models.TransientModel):
    _name = "wizard.employee.catalogs"

    date_from = fields.Date('Desde', required=False)
    date_to = fields.Date('Hasta', required=False)
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    contracting_regime = fields.Selection([
        # ('01', 'Assimilated to wages'),
        ('02', 'Wages and salaries'),
        ('03', 'Senior citizens'),
        ('04', 'Pensioners'),
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
    ], string='Contracting Regime', required=True,default="02")

    
    @api.multi
    def report_print(self, data):
        date_to = self.date_to
        domain_register = []
        domain_work_center = []
        list_code = []
        list_name = []
        list_imss = []
        list_curp = []
        list_rfc = []
        list_job = []
        list_department = []
        list_date_start = []
        contract=self.env['hr.contract']
        if self.contracting_regime:
            domain_regime = [('contracting_regime','=',self.contracting_regime)]
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        contract_ids=contract.search([('employee_id.group_id','=',self.group_id.id)] + domain_regime + domain_register + domain_work_center)
        if not contract_ids:
            raise UserError(_('No se encontro informacion para estos criterios de busqueda'))
        for i in contract_ids:
            code = (i.employee_id.enrollment)
            name = (i.employee_id.name)
            imss = (i.employee_id.ssnid)
            curp = (i.employee_id.curp)
            rfc = (i.employee_id.rfc)
            job = (i.employee_id.job_id.name)
            department = (i.employee_id.department_id.name)
            date_start = (i.date_start)
            list_code.append(code)
            list_name.append(name)
            list_imss.append(imss)
            list_curp.append(curp)
            list_rfc.append(rfc)
            list_job.append(job)
            list_department.append(department)
            list_date_start.append(date_start)
        data['group'] = self.group_id.name
        data['regime'] = dict(self._fields['contracting_regime']._description_selection(self.env)).get(self.contracting_regime)
        data['register'] = self.employer_register_id.employer_registry
        data['work_center'] = self.work_center_id.name
        data['code'] = list_code
        data['name'] = list_name
        data['imss'] = list_imss
        data['curp'] = list_curp
        data['rfc'] = list_rfc
        data['job'] = list_job
        data['department'] = list_department
        data['date_start'] = list_date_start
        return self.env.ref('payroll_mexico.report_employee_catalogs').report_action(self, data=data)
        
        
        
    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))
