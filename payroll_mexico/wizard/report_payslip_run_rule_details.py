# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError


class PayslipRunRuleDetails(models.TransientModel):
    _name = "hr.payslip.run.rule.details"
    _description = "Detalles de las reglas de negocio"

    #Columns
    payslip_run_id = fields.Many2one('hr.payslip.run', index=True, string='Payslip Batches')
    rule_id = fields.Many2one('hr.salary.rule', index=True,  required=True, string='Business Rule')
    wage = fields.Boolean(string='Wages and salaries', help="Hiring wages and salaries.")
    free = fields.Boolean(string='Free', help="Hiring free.")
    assimilated = fields.Boolean(string='Assimilated to salary', help="Hiring Assimilated to salary.")

    @api.multi
    @api.onchange('payslip_run_id')
    def onchange_payslip_run_id(self):
        # ~ self.rule_id = False
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
        
        PayslipObj = self.env['hr.payslip'].sudo()
        domain = [('payslip_run_id','=',self.payslip_run_id.id)]
        contracting_domain = []
        if self.wage:
            contracting_domain += ['02']
        if self.free:
            contracting_domain += ['05','99']
        if self.assimilated:
            contracting_domain += ['08','09','11']
        if contracting_domain:
            domain += [('contracting_regime','in', contracting_domain)]
        payroll_dic['rule'] = self.rule_id.name
        payroll_dic['date_start'] = '%s/%s/%s' %(self.payslip_run_id.date_start.strftime("%d"), self.payslip_run_id.date_start.strftime("%b").title(), self.payslip_run_id.date_start.strftime("%Y"))
        payroll_dic['date_end'] = '%s/%s/%s' %(self.payslip_run_id.date_end.strftime("%d"), self.payslip_run_id.date_end.strftime("%b").title(), self.payslip_run_id.date_end.strftime("%Y"))
        slip_ids = PayslipObj.search(domain, order="date_from asc, id asc")
        if not slip_ids:
            raise UserError(_('No results found.'))
        for slip in slip_ids:
            total += sum(slip.line_ids.filtered(lambda r: r.salary_rule_id.id == self.rule_id.id).mapped('total'))
            for line in slip.line_ids:
                if line.salary_rule_id.id == self.rule_id.id:
                    employees.append({
                        'enrollment': slip.employee_id.enrollment,
                        'name': slip.employee_id.complete_name,
                        'struct': slip.struct_id.name,
                        'total': line.total,
                    })
        payroll_dic['employees'] = sorted(employees, key=lambda k: k['name'])
        payroll_dic['total'] = total
        
        data={
            'payroll_data': payroll_dic,
            }
        return self.env.ref('payroll_mexico.action_report_rule_details').report_action(self, data)
