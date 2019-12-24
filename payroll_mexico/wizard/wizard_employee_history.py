# -*- coding: utf-8 -*-

from odoo import fields, models, api


class wizardEmployeeHistory(models.TransientModel):
    _name = 'wizard.employee.history'

    date_from = fields.Date('Desde',required=True)
    date_to = fields.Date('Hasta',required=True)
    group_id = fields.Many2one('hr.group',"Grupo",required=True)
    work_center_id = fields.Many2one('hr.work.center',"Centro de trabajo",required=False)
    job_ids = fields.Many2many('hr.job','employee_history_job_rel','history_id','job_id',string='Puesto de trabajo')
    employer_register_id = fields.Many2one('res.employer.register',"Registro Patronal",required=False)
    contracting_regime = fields.Selection([
            ('1','Assimilated to wages'),
            ('2','Wages and salaries'),
            ('3','Senior citizens'),
            ('4','Pensioners'),
            ('5','Free')],string='Régimen de contratación',required=True,default="2")

    @api.multi
    def report_print(self,data):
        domain_group = []
        domain_work_center = []
        domain_job = []
        domain_register = []
        domain_regime = []
        date_from = self.date_from
        date_to = self.date_to
        list_employee = []
        list_job = []
        list_date = []
        list_date_end = []
        history=self.env['hr.employee.change.history']
        if self.group_id:
            domain_group = [('contract_id.employee_id.group_id', '=', self.group_id.id)]
        if self.work_center_id:
            domain_work_center = [('contract_id.employee_id.work_center_id', '=', self.work_center_id.id)]
        if self.job_ids:
            domain_job = [('job_id', 'in', self.job_ids.ids)]
        if self.employer_register_id:
            domain_register = [('contract_id.employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.contracting_regime:
            domain_regime = [('contract_id.contracting_regime', '=', self.contracting_regime)]
        history_ids=history.search([('date_from','>=',date_from),('date_from','<=',date_to)] + domain_group + domain_work_center + domain_job + domain_register + domain_regime)
        for i in history_ids:
            employee = i.contract_id.employee_id.name
            job = i.contract_id.employee_id.job_id.name
            date = i.date_from
            date_end = i.contract_id.date_end
            list_employee.append(employee)
            list_job.append(job)
            list_date.append(date)
            list_date_end.append(date_end)
            print ('i')
            print (i)
            print ('i')
        data['group']= self.group_id.name
        data['work_center']= self.work_center_id.name
        data['job_ids']= self.job_ids.name
        data['register']= self.employer_register_id.employer_registry
        data['regime']= dict(self._fields['contracting_regime']._description_selection(self.env)).get(self.contracting_regime)
        data['date_from']= date_from
        data['date_to']= date_to
        data['employee']= list_employee
        data['job']= list_job
        data['date']= list_date
        data['date_end']= list_date_end
        return self.env.ref('payroll_mexico.report_employee_history').report_action(self, data=data)

    @api.multi
    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        This method validated that the final date is not less than the initial date
        :return:
        '''
        if self.date_to < self.date_from:
            raise UserError(_("The end date cannot be less than the start date "))
