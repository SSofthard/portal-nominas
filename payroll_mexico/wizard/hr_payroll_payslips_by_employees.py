# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    
    def _default_estructure(self):
        payslip_run=self.env['hr.payslip.run'].search([('id','in',self.env.context.get('active_ids', []))])
        return payslip_run.estructure_id.id
        
    def _default_contracting_regime(self):
        payslip_run=self.env['hr.payslip.run'].search([('id','in',self.env.context.get('active_ids', []))])
        return payslip_run.contracting_regime

    estructure_id = fields.Many2one('hr.payroll.structure', 'Estructure', readonly=True, default=lambda self: self._default_estructure())
    contracting_regime = fields.Selection([
                                        ('02', 'Wages and salaries'),
                                        ('05', 'Free'),
                                        ('08', 'Assimilated commission agents'),
                                        ('09', 'Honorary Assimilates'),
                                        ('11', 'Assimilated others'),
                                        ('99', 'Other regime'),
                                        ], string='Contracting Regime',
                                        required=True, 
                                        readonly=True,
                                        default=lambda self: self._default_contracting_regime()
                                        )
    @api.onchange('estructure_id','contracting_regime')
    def onchange_estructure(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            payslip_run = self.env['hr.payslip.run'].browse(active_id)
            payslip_run_employees = payslip_run.mapped('slip_ids').mapped('employee_id').ids
        contract=self.env['hr.contract']
        structure_type_id=self.estructure_id.structure_type_id.id
        domain=[
            ('structure_type_id','=',structure_type_id),
            ('employee_id.group_id','=',payslip_run.group_id.id),
            ('contracting_regime','=',self.contracting_regime)
            ]
        if payslip_run.contracting_regime == '02':
            domain.append(('employer_register_id','=',payslip_run.employer_register_id.id))
        employees=contract.search_read(domain,['employee_id','state'])
        employee_ids=[]
        for employee in employees:
            if employee['state'] in ['open']:
                if employee['employee_id'][0] not in payslip_run_employees:
                    employee_ids.append(employee['employee_id'][0])
        return {'domain':{'employee_ids':[('id','in',employee_ids)]}}
        
    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        payslip_run = self.env['hr.payslip.run'].search([('id','=',active_id)])
        if active_id:
            [run_data] = payslip_run.browse(active_id).read(['date_start', 
                                                             'date_end', 
                                                             'credit_note',
                                                             # ~ 'struct_id',
                                                             'payroll_type',
                                                             'payroll_month',
                                                             'payroll_of_month',
                                                             'payroll_period',
                                                             'table_id',
                                                             'employer_register_id',
                                                             'payment_date',
                                                             ])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        estructure_id=self.estructure_id.id
        structure_type_id=self.estructure_id.structure_type_id.id
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            contract=self.env['hr.contract'].search([('contracting_regime','=',self.contracting_regime),('employee_id','=',employee.id),('state','in',['open']),])[0]
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=contract.id, struct_id=self.estructure_id, run_data=run_data )
            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id':estructure_id,
                'structure_type_id':structure_type_id,
                'contract_id': slip_data['value'].get('contract_id'),
                'payslip_run_id': active_id,
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'date_from': from_date,
                'date_to': to_date,
                'payment_date': run_data.get('payment_date'),
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
                'payroll_type':slip_data['value'].get('payroll_type'),
                'payroll_month':slip_data['value'].get('payroll_month'),
                'payroll_of_month':slip_data['value'].get('payroll_of_month'),
                'payroll_period':slip_data['value'].get('payroll_period'),
                'table_id':slip_data['value'].get('table_id'),
                'employer_register_id':slip_data['value'].get('employer_register_id'),
            }
            payslips += self.env['hr.payslip'].create(res)
            payslips.compute_sheet()
        payslip_run.set_tax_iva_honorarium()
        payslip_run.generated = True
        return {'type': 'ir.actions.act_window_close'}
