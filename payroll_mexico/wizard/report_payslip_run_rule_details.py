# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


class PayslipRunRuleDetails(models.TransientModel):
    _name = "hr.payslip.run.rule.details"
    _description = "Detalles de las reglas de negocio"

    #Columns
    payslip_run_id = fields.Many2one('hr.payslip.run', index=True, string='Nomina')
    rule_id = fields.Many2one('hr.salary.rule', index=True,  required=True, string='Regla de negocio')

    @api.multi
    @api.onchange('payslip_run_id')
    def onchange_payslip_run_id(self):
        self.rule_id = False
        rule_ids = self.payslip_run_id.mapped('slip_ids').mapped('line_ids').mapped('salary_rule_id').ids
        domain = {'rule_id': [('id', 'in', rule_ids)]}
        return {'domain': domain}

    @api.multi
    def print_report(self):
        self.ensure_one()
        payroll_dic = {}
        employees = []
        total = 0
        company = self.payslip_run_id.mapped('slip_ids').mapped('company_id')
        payroll_dic['rfc'] = company.rfc
        payroll_dic['rule'] = self.rule_id.name
        payroll_dic['date_start'] = '%s/%s/%s' %(self.payslip_run_id.date_start.strftime("%d"), self.payslip_run_id.date_start.strftime("%b").title(), self.payslip_run_id.date_start.strftime("%Y"))
        payroll_dic['date_end'] = '%s/%s/%s' %(self.payslip_run_id.date_end.strftime("%d"), self.payslip_run_id.date_end.strftime("%b").title(), self.payslip_run_id.date_end.strftime("%Y"))
        slip_ids = self.payslip_run_id.mapped('slip_ids')  #.filtered(lambda r: r.salary_rule_id == self.rule_id.id)
        for slip in slip_ids:
            total += sum(slip.line_ids.filtered(lambda r: r.salary_rule_id.id == self.rule_id.id).mapped('total'))
            for line in slip.line_ids:
                if line.salary_rule_id.id == self.rule_id.id:
                    employees.append({
                        'enrollment': slip.employee_id.enrollment,
                        'name': slip.employee_id.name_get()[0][1],
                        'total': line.total,
                    })
        payroll_dic['employees'] = employees
        payroll_dic['total'] = total
        data={
            'payroll_data':payroll_dic
            }
        return self.env.ref('payroll_mexico.action_report_rule_details').report_action(self, data)
