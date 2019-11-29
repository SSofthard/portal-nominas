# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    estructure_id = fields.Many2one('hr.payroll.structure', 'Estructure')
    
    @api.onchange('estructure_id')
    def onchange_estructure(self):
        contract=self.env['hr.contract']
        structure_type_id=self.estructure_id.structure_type_id.id
        domain=[('structure_type_id','=',structure_type_id)]
        employees=contract.search_read(domain,['employee_id','state']) 
        employee_ids=[]
        for employee in employees:
            if employee['state'] in ['open']:
                employee_ids.append(employee['employee_id'][0])
        return {'domain':{'employee_ids':[('id','in',employee_ids)]}}
        
    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        from_date = run_data.get('date_start')
        to_date = run_data.get('date_end')
        if not data['employee_ids']:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        estructure_id=self.estructure_id.id
        structure_type_id=self.estructure_id.structure_type_id.id
        for employee in self.env['hr.employee'].browse(data['employee_ids']):
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
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
                'credit_note': run_data.get('credit_note'),
                'company_id': employee.company_id.id,
            }
            payslips += self.env['hr.payslip'].create(res)
        payslips.compute_sheet()
        return {'type': 'ir.actions.act_window_close'}
