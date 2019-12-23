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
            ('1','Assimilated to wages'),
            ('2','Wages and salaries'),
            ('3','Senior citizens'),
            ('4','Pensioners'),
            ('5','Free')], string='Contracting Regime', required=True,default="2")

    
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
        list_department = []
        list_date_end = []
        contract=self.env['hr.contract']
        if self.contracting_regime:
            domain_regime = [('contracting_regime','=',self.contracting_regime)]
            print ('domain_regime')
            print (domain_regime)
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        contract_ids=contract.search([('employee_id.group_id','=',self.group_id.id)] + domain_regime + domain_register + domain_work_center)
        for i in contract_ids:
            code = (i.employee_id.enrollment)
            name = (i.employee_id.name)
            imss = (i.employee_id.ssnid)
            curp = (i.employee_id.curp)
            rfc = (i.employee_id.rfc)
            department = (i.employee_id.department_id.name)
            date_end = (i.date_end)
            list_code.append(code)
            list_name.append(name)
            list_imss.append(imss)
            list_curp.append(curp)
            list_rfc.append(rfc)
            list_department.append(department)
            list_date_end.append(date_end)
        data['group'] = self.group_id.name
        data['regime'] = self.contracting_regime
        data['register'] = self.employer_register_id.employer_registry
        data['work_center'] = self.work_center_id.name
        data['code'] = list_code
        data['name'] = list_name
        data['imss'] = list_imss
        data['curp'] = list_curp
        data['rfc'] = list_rfc
        data['department'] = list_department
        data['date_end'] = list_date_end
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
