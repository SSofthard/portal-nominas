# -*- coding: utf-8 -*-

import babel
from odoo import api, fields, models, tools, _
from datetime import date, datetime, time


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    structure_type_id = fields.Many2one(
                                    'hr.structure.types',
                                    related="contract_id.structure_type_id",
                                    string="Structure Types")
    
    @api.multi
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False, struct_id=False, run_data=False, ):
        #defaults
        res = {
            'value': {
                'line_ids': [],
                #delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                #delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in self.worked_days_line_ids.ids],
                #'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
                'payroll_type': run_data['payroll_type'],
                'payroll_month': run_data['payroll_month'],
                'payroll_of_month': run_data['payroll_of_month'],
                'payroll_period': run_data['payroll_period'],
                'table_id': run_data['table_id'][0],
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        employee = self.env['hr.employee'].browse(employee_id)
        locale = self.env.context.get('lang') or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
            'company_id': employee.company_id.id,
        })
        if contract_id:
            #set the list of contract for which the input have to be filled
            contract_ids = [contract_id]
        else:
            #if we don't give the contract, then the input to fill should be for all current contracts of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        #computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to, run_data['payroll_period'])
        # ~ input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            # ~ 'input_line_ids': input_line_ids,
        })
        return res
                                    


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    #Columns
    group_id = fields.Many2one('hr.group', string="Empresa",readonly=True, states={'draft': [('readonly', False)]})
