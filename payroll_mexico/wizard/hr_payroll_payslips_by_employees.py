# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    
    def _default_estructure(self):
        payslip_run=self.env['hr.payslip.run'].search([('id','in',self.env.context.get('active_ids', []))])
        return [[6,False,payslip_run.estructures_id.ids]]
        
    estructures_id = fields.Many2many('hr.payroll.structure', 
                                      'payslip_employee_structure_rel', 
                                      'payslip_employee_id', 
                                      'structure_id', 
                                      'Structures', 
                                      required=False, 
                                      readonly=True, 
                                      default=lambda self: self._default_estructure())
    
    
    @api.onchange('estructures_id')
    def onchange_estructure(self):
        payslip_run_id=self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
        employee_ids = self.env['hr.contract'].search([('group_id','=',payslip_run_id.group_id.id),
                                                        ('state','in',['open']),
                                                        ('structure_type_id','in',self.estructures_id.mapped('structure_type_id').ids),]).mapped('employee_id')
        return {'domain':{'employee_ids':[('id','in',employee_ids.ids)]}}
        
    # ~ @api.onchange('estructure_id','contracting_regime')
    # ~ def onchange_estructure(self):
        # ~ payslip_run_id=self.env[self.env.context['active_model']].browse(self.env.context['active_id'])
        # ~ res = []
        # ~ if payslip_run_id.payroll_type=='O':
            # ~ self._cr.execute('''select id,contract_id, employee_id from hr_payslip
                                # ~ where group_id = %s and contracting_regime = '%s' and struct_id = %s and payroll_type = 'O'
                                # ~ and (date_from BETWEEN CAST ('%s' AS DATE) AND CAST ('%s' AS DATE)
                                # ~ or date_to BETWEEN CAST ('%s' AS DATE) AND CAST ('%s' AS DATE)) ''' % (payslip_run_id.group_id.id,
                                                                                                       # ~ payslip_run_id.contracting_regime,
                                                                                                       # ~ payslip_run_id.estructure_id.id,
                                                                                                       # ~ payslip_run_id.date_start,
                                                                                                       # ~ payslip_run_id.date_end,
                                                                                                       # ~ payslip_run_id.date_start,
                                                                                                       # ~ payslip_run_id.date_end))
            # ~ res = self._cr.fetchall()
            # ~ res = list(set([i[1] for i in res]))
        # ~ active_id = self.env.context.get('active_id')
        # ~ if active_id:
            # ~ payslip_run = self.env['hr.payslip.run'].browse(active_id)
            # ~ payslip_run_employees = payslip_run.mapped('slip_ids').mapped('employee_id').ids
        # ~ contract=self.env['hr.contract']
        # ~ structure_type_id=self.estructure_id.structure_type_id.id
        # ~ if payslip_run:
            # ~ # a contract is valid if it ends between the given dates
            # ~ clause_1 = ['&', ('date_end', '<=', payslip_run.date_end), ('date_end', '>=', payslip_run.date_start)]
            # ~ # OR if it starts between the given dates
            # ~ clause_2 = ['&', ('date_start', '<=', payslip_run.date_end), ('date_start', '>=', payslip_run.date_start)]
            # ~ # OR if it starts before the date_from and finish after the date_end (or never finish)
            # ~ clause_3 = ['&', ('date_start', '<=', payslip_run.date_start), '|', ('date_end', '=', False), ('date_end', '>=', payslip_run.date_end)]
        # ~ domain=[
            # ~ ('structure_type_id','=',structure_type_id),
            # ~ ('employee_id.group_id','=',payslip_run.group_id.id),
            # ~ ('contracting_regime','=',self.contracting_regime),
            # ~ ('id','not in',res)
            # ~ ,'|', '|'] + clause_1 + clause_2 + clause_3
        # ~ if payslip_run.contracting_regime == '02':
            # ~ domain.append(('employer_register_id','=',payslip_run.employer_register_id.id))
        # ~ employees=contract.search_read(domain,['employee_id','state'])
        # ~ employee_ids=[]
        # ~ for employee in employees:
            # ~ if employee['state'] in ['open']:
                # ~ if employee['employee_id'][0] not in payslip_run_employees:
                    # ~ employee_ids.append(employee['employee_id'][0])
        # ~ return {'domain':{'employee_ids':[('id','in',employee_ids)]}}
        
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
                                                             # ~ 'payroll_type',
                                                             'payroll_month',
                                                             'payroll_of_month',
                                                             'payroll_period',
                                                             'table_id',
                                                             # ~ 'employer_register_id',
                                                             'payment_date',
                                                             ])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        for estructure in self.estructures_id:
            estructure_id=estructure.id
            structure_type_id=estructure.structure_type_id.id
            for employee in self.env['hr.employee'].browse(data['employee_ids']):
                contract=self.env['hr.contract'].search([('structure_type_id','=',structure_type_id),('employee_id','=',employee.id),('group_id','=',payslip_run.group_id.id),('state','in',['open']),])
                if contract:
                    contract = contract[0]
                    payslip = payslips.search([('contract_id','=',contract.id),('employee_id','=',employee.id),('payslip_run_id','=',payslip_run.id)])
                    if not payslip:
                        run_data['payroll_type'] = estructure.payroll_type
                        run_data['employer_register_id'] = contract.employer_register_id.id
                        slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=contract.id, struct_id=estructure, run_data=run_data )
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
                            'company_id': slip_data['value'].get('company_id'),
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
