# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class wizardEmployeeHistory(models.TransientModel):
    _name = 'wizard.employee.history'

    date_from = fields.Date('Desde',required=True)
    date_to = fields.Date('Hasta',required=True)
    group_id = fields.Many2one('hr.group',"Grupo",required=True)
    work_center_id = fields.Many2one('hr.work.center',"Centro de trabajo",required=False)
    job_ids = fields.Many2many('hr.job','employee_history_job_rel','history_id','job_id',string='Puesto de trabajo')
    select_job = fields.Selection([
                    ('all','Todos'),
                    ('some','Algunos')],string="Buscar Puesto de trabajo")
    employer_register_id = fields.Many2one('res.employer.register',"Registro Patronal",required=False)
    contracting_regime = fields.Selection([
            ('1','Assimilated to wages'),
            ('2','Wages and salaries'),
            ('3','Senior citizens'),
            ('4','Pensioners'),
            ('5','Free')],string='Régimen de contratación',required=True,default="2")

    @api.onchange('select_job')
    def onchange_job(self):
        if self.select_job == 'all':
            self.job_ids = [(6,0,[x.id for x in self.job_ids])]
            print ('self.job_ids')
            print (self.job_ids)

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
        list_date_start = []
        history=self.env['hr.change.job']
        if self.group_id:
            domain_group = [('employee_id.group_id', '=', self.group_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        if self.job_ids:
            domain_job = [('employee_id.job_id', 'in', self.job_ids.ids),('job_current_id', 'in', self.job_ids.ids)]
            print ('domain_job')
            print (domain_job)
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.contracting_regime:
            domain_regime = [('contract_id.contracting_regime', '=', self.contracting_regime)]
        history_ids=history.search([('date_from','>=',date_from),('date_from','<=',date_to)] + domain_group + domain_work_center + domain_job + domain_register + domain_regime)
        if not history_ids:
            raise UserError(_('No se encontro informacion para estos criterios de busqueda'))
        active = 0 
        for i in history_ids:
            active += 1
            employee = i.employee_id.name
            job = i.employee_id.job_id.name
            date = i.date_from
            date_start = i.contract_id.date_start
            list_employee.append(employee)
            list_job.append(job)
            list_date.append(date)
            list_date_start.append(date_start)
            print ('i')
            print (i)
        data['group']= self.group_id.name
        data['work_center']= self.work_center_id.name
        data['job_ids']= ', '.join([x.name for x in self.job_ids])
        data['register']= self.employer_register_id.employer_registry
        data['regime']= dict(self._fields['contracting_regime']._description_selection(self.env)).get(self.contracting_regime)
        data['date_from']= date_from
        data['date_to']= date_to
        data['employee']= list_employee
        data['job']= list_job
        data['date']= list_date
        data['date_start']= list_date_start
        data['active']= active
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
