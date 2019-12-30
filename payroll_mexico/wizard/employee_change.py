# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, AccessError
from odoo import api, fields, models, _

class EmployeeChangeHistoryWizard(models.TransientModel):
    _name = "hr.employee.change.history.wizard"

    #Columns
    employee_id = fields.Many2one('hr.employee', index=True, string='Employee')
    contract_id = fields.Many2one('hr.contract', index=True, string='Contract')
    wage = fields.Float('Wage', digits=(16, 2), help="Employee's monthly gross wage.")
    date_from = fields.Date(string="Start Date", default=fields.Date.today())

    def apply_change(self):
        affiliate_movements = self.env['hr.employee.affiliate.movements'].search([('contract_id','=',self.contract_id.id),('type','=','07'),('state','in',['draft','generated']),('contracting_regime','in',['2'])])
        if affiliate_movements:
            raise ValidationError(_('There is already an affiliate movement for salary change in draft or generated status, please check and if you want to generate a new one, delete the current one.'))
        self.contract_id.wage = self.wage
        val = {
            'contract_id':self.contract_id.id,
            'employee_id':self.employee_id.id,
            'type':'07',
            'date': self.date_from,
            'wage':self.wage,
            'salary':self.contract_id.integral_salary,
            }
        self.env['hr.employee.affiliate.movements'].create(val)
        return True 

class EmployeeChangeJobWizard(models.TransientModel):
    _name = "hr.employee.change.job.wizard"

    #Columns
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    date_from = fields.Date(string="Fecha", default=fields.Date.today())
    job_id = fields.Many2one('hr.job', string='Puesto de trabajo')

    def change_job(self):
        self.contract_id.job_id = self.job_id.id
        self.employee_id.job_id = self.job_id.id
        history = self.env['hr.change.job'].search([('employee_id', '=', self.employee_id.id),('contract_id', '=', self.contract_id.id)], limit=1)
        history.write({'date_to': self.date_from})
        change_job = {
                'employee_id': self.employee_id.id,
                'contract_id': self.contract_id.id,
                'job_id': self.job_id.id,
                'date_from': self.date_from,
                'date_to': False,
        }
        self.env['hr.change.job'].create(change_job)
        return True 

class wizardEmployeeHistory(models.TransientModel):
    _name = 'wizard.employee.history'

    date_from = fields.Date('Desde',required=True)
    date_to = fields.Date('Hasta',required=True)
    group_id = fields.Many2one('hr.group',"Grupo",required=True)
    work_center_id = fields.Many2one('hr.work.center',"Centro de trabajo",required=False)
    job_ids = fields.Many2many('hr.job','employee_history_job_rel','history_id','job_id',string='Puesto de trabajo')
    select_job = fields.Selection([
                    ('all','Todos'),
                    ('some','Algunos')],string="Buscar por puesto de trabajo", default='all')
    employer_register_id = fields.Many2one('res.employer.register',"Registro Patronal",required=False)
    contracting_regime = fields.Selection([
            ('0',''),
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
        history=self.env['hr.change.job']
        if self.group_id:
            domain_group = [('employee_id.group_id', '=', self.group_id.id)]
        if self.work_center_id:
            domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)]
        if self.job_ids:
            domain_job = [('job_id', 'in', self.job_ids.ids)]
        if self.employer_register_id:
            domain_register = [('employee_id.employer_register_id', '=', self.employer_register_id.id)]
        if self.contracting_regime:
            domain_regime = [('contract_id.contracting_regime', '=', self.contracting_regime)]
        # ~ for i in self.job_ids:
        history_id=history.search( domain_group + domain_work_center + domain_job + domain_register + domain_regime)
        history_ids=history.search([('date_from','<=',date_from),('date_to','=',False)] + domain_group + domain_work_center + domain_job + domain_register + domain_regime)
        history_ids_date_to=history.search([('date_to','<=',date_to)] + domain_group + domain_work_center + domain_job + domain_register + domain_regime)
        history_ids_low=history.search([('date_to','>=',date_from),('date_to','<=',date_to)] + domain_group + domain_work_center + domain_job + domain_register + domain_regime)
        print ('history_id')
        print (history_id)
        data={
            'history_id': history_id._ids,
            'history_ids': history_ids._ids,
            'history_ids_date_to': history_ids_date_to._ids,
            'history_ids_low': history_ids_low._ids,
            'job_ids': ', '.join([x.name for x in self.job_ids]),
            'date_from': date_from,
            'date_to': date_to,
            'register': self.employer_register_id.employer_registry,
            'regime': dict(self._fields['contracting_regime']._description_selection(self.env)).get(self.contracting_regime),
            'work_center': self.work_center_id.name,
            'group': self.group_id.name,
        }
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
