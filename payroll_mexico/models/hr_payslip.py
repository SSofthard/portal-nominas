# -*- coding: utf-8 -*-

import babel
import pytz
import base64
import qrcode

from pytz import timezone
from datetime import date, datetime, time, timedelta
from dateutil import relativedelta as rdelta
from io import StringIO, BytesIO
from lxml import etree as ET
from .tool_convert_numbers_letters import numero_to_letras

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.addons.payroll_mexico.cfdilib_payroll import cfdilib, cfdv32, cfdv33


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _order = 'create_date desc'

    complete_name = fields.Char("Serie/Folio")
    payroll_type = fields.Selection([
            ('O', 'Ordinary Payroll'),
            ('E', 'Extraordinary Payroll')], 
            string='Payroll Type', 
            default="O", 
            # required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_month = fields.Selection([
            ('1', 'January'),
            ('2', 'February'),
            ('3', 'March'),
            ('4', 'April'),
            ('5', 'May'),
            ('6', 'June'),
            ('7', 'July'),
            ('8', 'August'),
            ('9', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December')], string='Payroll month', 
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_of_month = fields.Selection([
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6')], string='Payroll of the month', 
            required=True, 
            default="1",
            readonly=True,
            states={'draft': [('readonly', False)]})
    payroll_period = fields.Selection([
            ('01', 'Daily'),
            ('02', 'Weekly'),
            ('10', 'Decennial'),
            ('04', 'Biweekly'),
            ('05', 'Monthly')], 
            string='Payroll period', 
            default="04",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    input_ids = fields.Many2many('hr.inputs', string="Inpust reported on payroll")
    table_id = fields.Many2one('table.settings', string="Table Settings")
    subtotal_amount_untaxed = fields.Float(string='Base imponible')
    amount_tax = fields.Float(string='Impuestos')
    payroll_tax_count = fields.Integer(compute='_compute_payroll_tax_count', string="Payslip Computation Details")
    move_infonacot_id = fields.Many2one('hr.credit.employee.account', string="FONACOT Move")
    group_id = fields.Many2one('hr.group', string="Group/Company", related="employee_id.group_id")
    integral_salary = fields.Float(string = 'Salario diario integral', related='contract_id.integral_salary')
    employer_register_id = fields.Many2one('res.employer.register', "Employer Register", required=False)
    payment_date = fields.Date(string='Fecha de pago',
        readonly=True, states={'draft': [('readonly', False)]})
    # ~ CFDI
    way_pay = fields.Selection([
            ('99', '99 - Por Definir'),
            ], 
            string='way to pay', 
            default="99",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    type_voucher = fields.Selection([
            ('N', 'Payroll'),
            ], 
            string='Tipo', 
            default="N",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    payment_method = fields.Selection([
            ('PUE', 'Pago en una sola exhibición'),
            ], 
            string='Payment method', 
            default="PUE",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    cfdi_use = fields.Selection([
            ('P01', 'To define'),
            ], 
            string='Uso CFDI', 
            default="P01",
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]})
    invoice_status = fields.Selection([
            ('factura_no_generada', 'Factura no generada'),
            ('factura_correcta', 'Factura correcta'),
            ('problemas_factura', 'Problemas con la factura'),
            ('problemas_cancelada', 'Factura cancelada'),
            ], 
            string='Invoice Status', 
            default="factura_no_generada",
            required=False,
            readonly=True)
    integral_variable_salary = fields.Float(string = 'Salario diario variable', compute='_compute_integral_variable_salary')
    structure_type_id = fields.Many2one(
                                    'hr.structure.types',
                                    related="contract_id.structure_type_id",
                                    string="Structure Types")
    year = fields.Integer(string='Año', compute='_ge_year_period', store=True)
    code_payslip = fields.Char(string='Serie', store=True, readonly=False)
    number = fields.Char(string='Folio')
    
    type_related_cfdi = fields.Selection([
            ('04', 'Sustitución de los CFDI previos'),
            ], 
            string='Tipo de relación', 
            required=False,
            readonly=True,
            states={'draft': [('readonly', False)]})
    uuid = fields.Char(string='CFDI relacionado', readonly=True, states={'draft': [('readonly', False)]})
    cfdi_issue_date = fields.Char(string='Fecha de emisión', readonly=True)
    invoice_date = fields.Char(string='Fecha de certificación', readonly=True)
    certificate_number = fields.Char(string='N° de Serie del CSD del SAT', readonly=True)
    certificate_number_emisor = fields.Char(string='N° de Serie del CSD del Emisor', readonly=True)
    stamp_cfd = fields.Text(string='Sello CDF',readonly=False)
    stamp_sat = fields.Text(string='Sello SAT', readonly=False)
    original_string = fields.Text(string='Cadena Original', readonly=False)
    UUID_sat = fields.Char(string='UUID', readonly=True)
    code_error = fields.Char(string='Código de error', readonly=True)
    error = fields.Char(string='Error', readonly=True)
    xml_timbre = fields.Many2one('ir.attachment', string="Timbre (XML)", readonly=True)
    qr_timbre = fields.Binary(string="Qr", readonly=True)
    # PDF Stamped
    pdf = fields.Many2one('ir.attachment', string="CFDI PDF", copy=False, readonly=True)
    filename = fields.Char(string='Filename', related="pdf.name", copy=False, readonly=True)
    filedata = fields.Binary(string='Filedatas', related="pdf.datas", copy=False, readonly=True)
    
    def overtime(self,type_overtime):
        days = 0
        quantity = 0
        for inpu in self.input_ids:
            if inpu.input_id.input_id.type_overtime == type_overtime:
                quantity += inpu.amount
                days += 1
        return {'days':int(days),'quantity':int(quantity)}
            

    def to_json(self):
        perceptions = self.env['hr.payslip.line'].search([('category_id.code','=',['PERCEPCIONES','PERCEPCIONESPECIE']),('slip_id','=',self.id)])
        
        perceptions_ordinary = self.env['hr.payslip.line'].search([('category_id.code','in',['PERCEPCIONES','PERCEPCIONESPECIE']),('slip_id','=',self.id),('salary_rule_id.type','=','perception')])
                
        deduction = self.env['hr.payslip.line'].search([('category_id.code','=','DED'),('slip_id','=',self.id)])
        
        other_payments = self.env['hr.payslip.line'].search([('category_id.code','=','PERCEPCIONES'),('slip_id','=',self.id),('salary_rule_id.type','=','other_payment')])
        
        other_deduction = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','=','DED'),('slip_id','=',self.id),('salary_rule_id.type_deduction','not in',['002'])]).mapped('total'))))
        
       
        isr_deduction = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','=','DED'),('slip_id','=',self.id),('salary_rule_id.type_deduction','in',['002'])]).mapped('total'))))
        
        bank_account = self.env['bank.account.employee'].search([('employee_id','=',self.employee_id.id),('predetermined','=',True),('state','=','active')])
        
        
        
        
        show_total_taxes_withheld = False
        if isr_deduction > 0:
            show_total_taxes_withheld = True
        
        
        perceptions_only = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','in',['PERCEPCIONES','PERCEPCIONESPECIE']),('salary_rule_id.type','=','perception'),('slip_id','=',self.id)]).mapped('total'))))
        other_payment_only = float("{0:.2f}".format(sum(other_payments.mapped('total'))))
        subtotal = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','=','GROSS'),('slip_id','=',self.id)]).mapped('total'))))
        discount_amount = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','=','DEDT'),('slip_id','=',self.id)]).mapped('total'))))
       
        total_salaries = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','in',['PERCEPCIONES','PERCEPCIONESPECIE']),
                                                                    ('salary_rule_id.type','=','perception'),
                                                                    ('slip_id','=',self.id),
                                                                    ('salary_rule_id.type_perception','not in',['022','023','025','039','044'])]).mapped('total'))))
        
        total_separation_compensation = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','in',['PERCEPCIONES','PERCEPCIONESPECIE']),
                                                                    ('salary_rule_id.type','=','perception'),
                                                                    ('slip_id','=',self.id),
                                                                    ('salary_rule_id.type_perception','in',['022','023','025'])]).mapped('total'))))
        total_retirement_pension_retirement = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','in',['PERCEPCIONES','PERCEPCIONESPECIE']),
                                                                    ('salary_rule_id.type','=','perception'),
                                                                    ('slip_id','=',self.id),
                                                                    ('salary_rule_id.type_perception','in',['039','044'])]).mapped('total'))))
        total_taxed = float("{0:.2f}".format(sum(self.env['hr.payslip.line'].search([('category_id.code','=','BRUTOG'),
                                                                ('slip_id','=',self.id),]).mapped('total'))))
        total = float("{0:.2f}".format(subtotal - discount_amount))
        type_perception = dict(self.env['hr.salary.rule']._fields.get('type_perception').selection)
        days = "{0:.3f}".format(self.env['hr.payslip.worked_days'].search([('code','=','WORK100'),('payslip_id','=',self.id)],limit=1).number_of_days)
        perceptions_list = []
        for p in perceptions_ordinary:
            if p.total > 0:
                amount_g = self.env['hr.payslip.line'].search([('salary_rule_id','=',p.salary_rule_id.salary_rule_taxed_id.id),('slip_id','=',self.id)],limit=1)
                perceptions_dict= {
                                    'type': p.salary_rule_id.type_perception,
                                    'key': p.salary_rule_id.code,
                                    'concept': p.salary_rule_id.name,
                                    'quantity': p.quantity,
                                    'amount_g': amount_g.total,
                                    'amount_e': "{0:.2f}".format(p.total - amount_g.total),
                                }
                if p.salary_rule_id.type_perception == '019':
                    overtime = self.overtime(p.salary_rule_id.type_overtime)
                    perceptions_dict['extra_hours']= [{
                                                    'days': overtime['days'],
                                                    'type': p.salary_rule_id.type_overtime,
                                                    'amount': amount_g.total,
                                                    'hours': overtime['quantity'],
                                                }]
                perceptions_list.append(perceptions_dict)
                
        deduction_list = []
        disability_list = []
        deduction_dict ={}
        for d in deduction:
            if d.total > 0:
                deduction_dict = {
                            'type': d.salary_rule_id.type_deduction,
                            'key': d.salary_rule_id.code,
                            'concept': d.salary_rule_id.name,
                            'amount': d.total,
                        }
                if d.salary_rule_id.type_deduction == '006':
                    if d.salary_rule_id.type_disability == '01':
                        disability = self.env['hr.payslip.worked_days'].search([('code','in',['F02']),('payslip_id','=',self.id)])
                    elif d.salary_rule_id.type_disability == '02':
                        disability = self.env['hr.payslip.worked_days'].search([('code','in',['F01']),('payslip_id','=',self.id)])
                    elif d.salary_rule_id.type_disability == '03':
                        disability = self.env['hr.payslip.worked_days'].search([('code','in',['F03']),('payslip_id','=',self.id)])
                    elif d.salary_rule_id.type_disability == '04':
                        disability = self.env['hr.payslip.worked_days'].search([('code','in',['F09']),('payslip_id','=',self.id)])
                    disability_dict = {
                                'days': int(disability.number_of_days),
                                'type': d.salary_rule_id.type_disability,
                                'amount': d.total,
                            }
                    disability_list.append(disability_dict)
                deduction_list.append(deduction_dict)
                    
                    
        other_list = []
        for o in other_payments:
            if o.total > 0:
                other_dict = {
                            'type': o.salary_rule_id.type_other_payment,
                            'key': o.salary_rule_id.code,
                            'concept': o.salary_rule_id.name,
                            'amount': o.total,
                        }
                if o.salary_rule_id.type_other_payment== '002':
                    subsidy = self.env['hr.payslip.line'].search([('salary_rule_id.code','=',['UI106']),('slip_id','=',self.id)],limit=1)
                    other_dict['subsidy'] = subsidy.total
                other_list.append(other_dict)

        
        
        data = {
            'serie': self.code_payslip,
            'number': self.number,
            'date_invoice_tz': '',
            'payment_policy': self.way_pay,
            'certificate_number': '',
            'certificate': '',
            'subtotal': "{0:.2f}".format(subtotal),
            'discount_amount': "{0:.2f}".format(discount_amount),
            'currency': 'MXN',
            'rate': '1',
            'amount_total': total,
            'document_type': self.type_voucher,
            'pay_method':self.payment_method,
            'emitter_zip': self.company_id.zip,
            'emitter_rfc': self.company_id.rfc,
            'emitter_name': self.company_id.business_name,
            'emitter_fiscal_position': self.company_id.tax_regime,
            'receiver_rfc': self.employee_id.rfc,
            'receiver_name': self.employee_id.complete_name,
            'receiver_reg_trib': '',
            'receiver_use_cfdi': self.cfdi_use,
            'invoice_lines': [{
                'price_unit': "{0:.2f}".format(subtotal),
                'subtotal_wo_discount': "{0:.2f}".format(subtotal),
                'discount': "{0:.2f}".format(discount_amount),
            }],
            'taxes': {
                'total_transferred': '0.00',
                'total_withhold': '0.00',
            },
            'payroll': {
                'type': self.payroll_type,
                'payment_date': self.payment_date,
                'date_from': self.date_from,
                'date_to': '',
                'number_of_days': days,
                'curp_emitter': '',
                'employer_register': '',
                'vat_emitter': '',
                'date_start': '',
                'seniority_emp': '',
                'curp_emp': '',
                'nss_emp': '',
                'contract_type': self.contract_id.type_id.code,
                'total_perceptions': perceptions_only,
                'total_deductions': discount_amount,
                'total_other': other_payment_only,
                'emp_risk': '',
                'emp_syndicated': 'No',
                'working_day': self.employee_id.type_working_day,
                'emp_regimen_type': self.contract_id.contracting_regime,
                'no_emp': self.employee_id.enrollment,
                'departament': self.contract_id.department_id.name,
                'emp_job': self.contract_id.job_id.name,
                'payment_periodicity': '',
                'emp_bank': '',
                'emp_account': '',
                'emp_base_salary': '',
                'emp_diary_salary': '',
                'emp_state': self.employee_id.work_center_id.state_id.code,
                'total_salaries': float("{0:.2f}".format(total_salaries)),
                'total_compensation': float("{0:.2f}".format(total_separation_compensation)),
                'total_retirement': float("{0:.2f}".format(total_retirement_pension_retirement)),
                'total_taxed': float("{0:.2f}".format(total_taxed)),
                'total_exempt': float("{0:.2f}".format((total_salaries+total_separation_compensation+total_retirement_pension_retirement) - total_taxed)),
                
                
                
                
                
                'perceptions': list(perceptions_list),
                
               
                'total_other_deductions': other_deduction,
                'show_total_taxes_withheld': show_total_taxes_withheld,
                'total_taxes_withheld': isr_deduction,   
                
                'deductions': list(deduction_list),
                'other_payments': list(other_list),
                'inabilities': disability_list
            },
        }
        
        if self.employee_id.deceased:
            data['receiver_rfc'] = 'XAXX010101000'
        if self.company_id.test_cfdi:
            data['receiver_rfc'] = 'TUCA5703119R5'
        
        
        
        if self.type_related_cfdi == '04':
            data['cfdi_related_type'] = self.type_related_cfdi
            data['cfdi_related'] = [{'uuid': self.uuid}]
        if self.payroll_type == 'E':
            data['payroll']['date_to'] = self.date_from
        else:
            data['payroll']['date_to'] = self.date_to
            
        if self.contract_id.type_id.code in ['01','02','03','04','05','06','07','08']:
            data['payroll']['employer_register']= self.employer_register_id.employer_registry
            if self.contract_id.contracting_regime == '02':
                data['payroll']['nss_emp'] = self.employee_id.ssnid
                data['payroll']['emp_risk'] = self.employer_register_id.job_risk
                data['payroll']['date_start'] = self.contract_id.previous_contract_date or self.contract_id.date_start
                data['payroll']['emp_diary_salary'] = "{0:.2f}".format(self.contract_id.integral_salary) 
                if self.employee_id.syndicalist:
                    data['payroll']['emp_syndicated'] = 'Sí'
                date_1 = self.contract_id.previous_contract_date or self.contract_id.date_start
                date_2 = self.date_to
                week = (int(abs(date_1 - date_2).days))/7
                antiquity_date = rdelta.relativedelta(date_2,date_1)
                antiquity = 'P'+str(int(week))+'W'
                data['payroll']['seniority_emp'] = antiquity
        if not self.employee_id.curp:
            if self.employee_id.gender == 'male':
                data['payroll']['curp_emp'] = 'XEXX010101HNEXXXA4'
            else:
                data['payroll']['curp_emp'] = 'XEXX010101MNEXXXA8'
        else:
            data['payroll']['curp_emp'] = self.employee_id.curp
        
        if self.payroll_type == 'O':
            data['payroll']['payment_periodicity'] = self.payroll_period
        else:
            data['payroll']['payment_periodicity'] = '99'
        
        if bank_account:
            data['payroll']['emp_bank'] = bank_account.bank_id.code
            data['payroll']['emp_account'] = bank_account.bank_account
            
        return data
    
    
    @api.multi
    def action_cfdi_nomina_generate(self):
        for payslip in self:
            tz = pytz.timezone(self.env.user.partner_id.tz)
            csd_company = self.env['res.company.fiel.csd'].search([('company_id','=',payslip.company_id.id),('type','=','csd'),('predetermined','=',True),('state','=','valid')])
            if csd_company.company_id.test_cfdi:
                url = csd_company.company_id.url_cfdi_test
                user = csd_company.company_id.user_cfdi_test
                password = csd_company.company_id.password_cfdi_test
            else:
                url = csd_company.company_id.url_cfdi
                user = csd_company.company_id.user_cfdi
                password = csd_company.company_id.password_cfdi
            if not url or not user or not password:
                vals = {
                     'code_error':'Desconocido',
                     'error':'Debe establecer la url el user y password para la conexción con el PAC',
                     'invoice_status':'problemas_factura'
                    }
                payslip.write(vals)
            elif not csd_company:
                vals = {
                     'code_error':'Desconocido',
                     'error':'Debe establecer el registro predeterminado para los archivos .key y .cer',
                     'invoice_status':'problemas_factura'
                    }
                payslip.write(vals)
            elif not csd_company.cer:
                vals = {
                     'code_error':'Desconocido',
                     'error':'Debe registrar su archivo .cer',
                     'invoice_status':'problemas_factura'
                    }
                payslip.write(vals)
            elif not csd_company.key:
                vals = {
                     'code_error':'Desconocido',
                     'error':'Debe registrar su archivo .key',
                     'invoice_status':'problemas_factura'
                    }
                payslip.write(vals)
            elif not csd_company.track:
                vals = {
                     'code_error':'Desconocido',
                     'error':'Debe registrar la pista para el archivo .key',
                     'invoice_status':'problemas_factura'
                    }
                payslip.write(vals)
            else:
                values = payslip.to_json()
                payroll = cfdv33.get_payroll(values, certificado=csd_company.cer.datas, llave_privada=csd_company.key.datas, 
                                                        password=csd_company.track, tz=tz, url=url, user=user, password_pac = password,  
                                                        debug_mode=True,)
                if not payroll.error_timbrado:
                    NSMAP = {
                         'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                         'cfdi':'http://www.sat.gob.mx/cfd/3', 
                         'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                         }
                    file=payroll.document_path.read()
                    document = ET.fromstring(file)
                    Complemento = document.find('cfdi:Complemento', NSMAP)
                    TimbreFiscalDigital = Complemento.find('tfd:TimbreFiscalDigital', NSMAP)
                    vals = {}
                    xml = base64.b64encode(file)
                    ir_attachment=self.env['ir.attachment']
                    folder_id = payslip.get_folder()
                    value={u'name': str(self.employee_id.complete_name)+'_'+str(self.date_from)+'_'+str(self.date_to), 
                            u'url': False,
                            u'company_id': self.company_id.id, 
                            u'folder_id': folder_id, 
                            u'datas_fname': str(self.employee_id.complete_name)+'_'+str(self.date_from)+'_'+str(self.date_to)+'.xml', 
                            u'type': u'binary', 
                            u'public': False, 
                            u'datas':xml , 
                            u'description': False}
                    xml_timbre = ir_attachment.create(value)
                    
                    
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4)
                    
                    url_qr ='https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id='+TimbreFiscalDigital.attrib['UUID']+'&re='+values['emitter_rfc']+'&rr='+values['receiver_rfc']+'&tt='+str(values['amount_total'])+'&fe='+TimbreFiscalDigital.attrib['SelloCFD'][-8:]
                    qr.add_data(url_qr)
                    qr.make(fit=True)
                    img = qr.make_image()
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    img_str = base64.b64encode(buffer.getvalue())
                    vals = {
                         'invoice_date':TimbreFiscalDigital.attrib['FechaTimbrado'],
                         'certificate_number':TimbreFiscalDigital.attrib['NoCertificadoSAT'],
                         'certificate_number_emisor':document.attrib['NoCertificado'],
                         'stamp_cfd':TimbreFiscalDigital.attrib['SelloCFD'],
                         'stamp_sat':TimbreFiscalDigital.attrib['SelloSAT'],
                         'original_string':payroll.cadena_original,
                         'cfdi_issue_date':payroll.date_timbre,
                         'UUID_sat':TimbreFiscalDigital.attrib['UUID'],
                         'xml_timbre':xml_timbre.id,
                         'invoice_status':'factura_correcta',
                         'code_error':'',
                         'error':'',
                         'qr_timbre':img_str,
                         'pdf': '',
                        }
                    payslip.write(vals)
                    
                    
                    # Generate CFDI PDF
                    payroll = {}
                    payroll[payslip.id] = payslip.data_payroll_report(),
                    data = {
                        'payroll_data': payroll,
                        'values': values,
                        'docids': payslip.id,
                    }
                    pdf = self.env.ref('payroll_mexico.action_payroll_cfdi_report').render_qweb_pdf(payslip.id, data=data)[0]
                    pdf_name = '%s_%s_%s' %(payslip.employee_id.complete_name, payslip.date_from, payslip.date_to) + '.pdf'
                    
                    attachment_id = payslip.env['ir.attachment'].create({
                        'name': pdf_name,
                        'res_id': payslip.id,
                        'folder_id': folder_id,
                        'res_model': payslip._name,
                        'datas': base64.encodestring(pdf),
                        'datas_fname': pdf_name,
                        'description': 'CFDI PDF',
                        'type': 'binary',
                    })
                    payslip.pdf = attachment_id.id
                else:
                    vals = {
                         'invoice_date':'',
                         'certificate_number':'',
                         'certificate_number_emisor':'',
                         'stamp_cfd':'',
                         'stamp_sat':'',
                         'original_string':'',
                         'cfdi_issue_date':'',
                         'UUID_sat':'',
                         'xml_timbre':False,
                         'invoice_status':'problemas_factura',
                          'code_error':payroll.error_timbrado['codigoError'],
                         'error':payroll.error_timbrado['error'],
                         'qr_timbre': False,
                         'pdf': False,
                        }
                    payslip.write(vals)
        return True 
    
    def get_folder(self):
        """ Function get folder is not exists, create folder """
        Folder = self.env['documents.folder']
        #Search or Create Group Folder 
        group_folder = self.group_id.name.upper()
        group_folder_id = Folder.search([('name','=',group_folder)])
        if not group_folder_id:
            group_folder_id = Folder.create({
                'name': group_folder,
                'company_id': self.company_id.id,
            })
        #Search or Create Year Folder
        year_folder = str(self.year)
        year_folder_id = Folder.search([('name','=',year_folder)])
        if not year_folder_id:
            year_folder_id = Folder.create({
                'name': year_folder,
                'parent_folder_id': group_folder_id.id,
                'company_id': self.company_id.id,
            })
        #Search or Create Month Folder
        month_folder = dict(
            self._fields['payroll_month']._description_selection(
                self.env)).get(self.payroll_month).upper()
        month_folder_id = Folder.search([('name','=',month_folder),('parent_folder_id','=',year_folder_id.id)])
        if not month_folder_id:
            month_folder_id = Folder.create({
                'name': month_folder,
                'parent_folder_id': year_folder_id.id,
                'company_id': self.company_id.id,
            })
        #Search or Create Period Folder
        date_from = self.date_from.strftime('%d/%b/%Y').title()
        date_to = self.date_to.strftime('%d/%b/%Y').title()
        period_folder = '%s A %s' %(date_from, date_to)
        period_folder_id = Folder.search([('name','=',period_folder),('parent_folder_id','=',month_folder_id.id)])
        if not period_folder_id:
            period_folder_id = Folder.create({
                'name': period_folder,
                'parent_folder_id': month_folder_id.id,
                'company_id': self.company_id.id,
            })
        return period_folder_id.id
    
    @api.one
    @api.depends('date_from')
    def _ge_year_period(self):
        '''
        Este metodo obtiene el valor para el campo año basado en las fecha date_from de la nomina
        '''
        self.year = self.date_from.year
    
    @api.one
    @api.depends('subtotal_amount_untaxed')
    def _compute_integral_variable_salary(self):
        '''Este metodo se utiliza para el cálculo de salario diario integral variable'''
        days_factor = {
                       'daily':1,
                       'weekly':7,
                       'decennial':10,
                       'biweekly':15,
                       'monthly':30,
                       }
        list_percepcions = self.line_ids.filtered(lambda o: o.salary_rule_id.apply_variable_compute == True
                                                                and o.salary_rule_id.type == 'perception')
        total_perception = self.get_total_perceptions_to_sv(list_percepcions)
        factor_days = (self.employee_id.group_id.days/30)*days_factor[self.payroll_period]
        self.integral_variable_salary = total_perception/factor_days

    def get_total_perceptions_to_sv(self, lines):
         '''
         Este metodo permite consultar si la regla aplica según los criterios de evaluación por ley
         '''
         vals=[]
         for line in lines:
             if line.salary_rule_id.type_perception in ['010','049']:
                 print ('''cuando el importe de cada uno no exceda del 10% del último SBC comunicado al
                        ~ Seguro Social, de ser así la cantidad que rebase integrará''')
                 proporcion_percepcion = line.amount/self.contract.salary_var
                 if proporcion_percepcion > 0.1:
                     restante = (line.amount - (self.contract.salary_var*0.1))*line.quantity
                     vals.append(restante)
             if line.salary_rule_id.type_perception == '019' and line.salary_rule_id.type_overtime == '02':
                 print ('''el generado dentro de los límites señalados en la Ley Federal del Trabajo (LFT), esto es que no
                         exceda de tres horas diarias ni de tres veces en una semana''')
                 vals.append(line.total)
             if line.salary_rule_id.type_perception in ['029']:
                 print ('''si su importe no rebasa el 40% del SMGVDF, de lo contrario el excedente se integrará''')
                 minimum_salary = self.company_id.municipality_id.get_salary_min(self.date_from)
                 if line.amount > (minimum_salary*0.40):
                     restante = (line.amount - (minimum_salary*0.40))*line.quantity
                     vals.append(restante)
             else:
                 vals.append(line.total)
         return sum(vals)

    def data_payroll_report(self):
        payroll_dic = {}
        lines = []
        line_ded = []
        domain = [('slip_id','=', self.id)]
        # Salario diario
        sd = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI002')]).mapped('total'))
        #Salrio diario integral
        sdi = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI003')]).mapped('total'))
        total_percep = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'P195')]).mapped('total'))
        total_ded = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'D103')]).mapped('total'))
        total = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'T001')]).mapped('total'))
        line_ids = self.env['hr.payslip.line'].search(domain + [('appears_on_payslip','=', True), ('total','!=', 0)])
        for line in line_ids:
            if line.category_id.code in ['PERCEPCIONES']:
                lines.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'exempt': 0,
                    'type': 'PERCEPCIONES',
                })
            if line.category_id.code == 'DED':
                line_ded.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'DED',
                })
        bank_account=self.env['bank.account.employee'].search([('employee_id','=', self.employee_id.id),('predetermined','=', True)])
        payroll_dic['payroll_period'] = dict(self._fields['payroll_period']._description_selection(self.env)).get(self.payroll_period).upper()
        payroll_dic['sd'] = sd
        payroll_dic['sdi'] = sdi
        payroll_dic['total_percep'] = total_percep
        payroll_dic['total_ded'] = total_ded
        payroll_dic['total'] = total
        payroll_dic['total_word'] = numero_to_letras(abs(total)) or 00
        payroll_dic['decimales'] =  str(round(float(total), 2)).split('.')[1] or 00
        payroll_dic['company'] = self.company_id.name.upper() or ''
        payroll_dic['lines'] = lines
        payroll_dic['line_ded'] = line_ded
        payroll_dic['bank'] = bank_account.bank_id.name
        payroll_dic['bank_account'] = bank_account.bank_account
        # Buscar Faltas
        leave_type = self.env['hr.leave.type'].search([('code','!=',False)])
        total_faults = 0
        absenteeism = 0
        inhability = 0
        diasimss = sum(self.worked_days_line_ids.filtered(lambda r: r.code == 'DIASIMSS').mapped('number_of_days'))
        payroll_dic['paid_days'] = diasimss #abs(self.date_from - self.date_to).days
        for leave in leave_type:
            for wl in self.worked_days_line_ids:
                if leave.code == wl.code:
                    if leave.time_type == 'inability':
                        inhability += wl.number_of_days
                    if leave.time_type == 'leave':
                        absenteeism += wl.number_of_days
        total_faults += inhability + absenteeism
        payroll_dic['faults'] = total_faults
        return payroll_dic
        
    @api.multi
    def get_pdf_cfdi(self):
        if not self.pdf:
            raise UserError(_("The payroll is not stamped."))
        return {
            'name': 'CFDI',
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=" + self._name +"&id=" + str(
                self.id) + "&filename_field=filename&field=filedata&download=true&filename=" + self.filename,
            'target': 'new',
        }

    @api.multi
    def print_payroll_receipt(self):
        payroll = {}
        data = {}
        for payslip in self:
            payroll[payslip.id] = payslip.data_payroll_report(),
        data={
            'payroll_data': payroll,
            'docids': self.ids,
            }
        return self.env.ref('payroll_mexico.action_payroll_receipt_report').with_context({'active_model': 'hr.payslip'}).report_action(self,data)      

    @api.multi
    def print_payroll_receipt_timbrado(self):
        payroll_dic = {}
        line_percep = []
        line_ded = []
        domain = [('slip_id','=', self.id)]
        sd = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI002')]).mapped('total'))
        sdi = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'UI003')]).mapped('total'))
        sub_caused = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'P105')]).mapped('total'))
        total_percep = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'P195')]).mapped('total'))
        total_ded = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'D103')]).mapped('total'))
        total = sum(self.env['hr.payslip.line'].search(domain + [('code','=', 'T001')]).mapped('total'))
        line_ids = self.env['hr.payslip.line'].search(domain + [('appears_on_payslip','=', True), ('total','!=', 0)])
        for line in line_ids:
            if line.category_id.code == 'PERCEPCIONES':
                line_percep.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'PERCEPCIONES',
                })
            if line.category_id.code == 'DED':
                line_ded.append({
                    'code': line.code,
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                    'type': 'DED',
                })
        payroll_dic['name'] = self.employee_id.complete_name
        payroll_dic['ssnid'] = self.employee_id.ssnid
        payroll_dic['rfc'] = self.employee_id.rfc
        payroll_dic['curp'] = self.employee_id.curp
        payroll_dic['date_from'] = self.date_from
        payroll_dic['date_to'] = self.date_to
        payroll_dic['payroll_period'] = dict(self._fields['payroll_period']._description_selection(self.env)).get(self.payroll_period).upper()
        payroll_dic['no_period'] = self.payroll_of_month
        payroll_dic['paid_days'] = abs(self.date_from - self.date_to).days
        payroll_dic['sd'] = sd
        payroll_dic['sdi'] = sdi
        payroll_dic['sub_caused'] = sub_caused
        payroll_dic['total_percep'] = total_percep
        payroll_dic['total_ded'] = total_ded
        payroll_dic['total'] = total
        payroll_dic['total_word'] = numero_to_letras(abs(total)) or 00
        payroll_dic['decimales'] =  str(round(total, 2)).split('.')[1] or 00
        payroll_dic['company'] = self.company_id.name.upper() or ''
        payroll_dic['lines'] = line_percep
        payroll_dic['line_ded'] = line_ded
        # Buscar Faltas
        leave_type = self.env['hr.leave.type'].search([('code','!=',False)])
        total_faults = 0
        absenteeism = 0
        inhability = 0
        for leave in leave_type:
            for wl in self.worked_days_line_ids:
                if leave.code == wl.code:
                    if leave.time_type == 'inability':
                        inhability += wl.number_of_days
                    if leave.time_type == 'leave':
                        absenteeism += wl.number_of_days
        total_faults += inhability + absenteeism
        payroll_dic['faults'] = total_faults
        values = payslip.to_json()
        data={
            'payroll_data':payroll_dic,
            'values':values,
            }
        return self.env.ref('payroll_mexico.action_payroll_receipt_timbrado_report').with_context({'active_model': 'hr.payslip'}).report_action(self,data)      

    @api.multi
    def _compute_payroll_tax_count(self):
        for payslip in self:
            line_ids = payslip.line_ids.filtered(lambda o: o.salary_rule_id.payroll_tax == True)
            payslip.payroll_tax_count = len(line_ids)

    @api.multi
    def action_view_payroll_tax(self):
        line_ids = self.mapped('line_ids')
        action = self.env.ref('hr_payroll.act_payslip_lines').read()[0]
        if len(line_ids) >= 1:
            line_tax_ids = line_ids.filtered(lambda o: o.salary_rule_id.payroll_tax == True)
            action['domain'] = [('id', 'in', line_tax_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []
        structure_ids = contracts.get_all_structures(self.struct_id)
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')
        hr_inputs = self.env['hr.inputs'].browse([])
        self.input_ids.write({'payslip':False,'state':'approve'})
        self.input_ids = False
        for contract in contracts:
            employee_id = (self.employee_id and self.employee_id.id) or (contract.employee_id and contract.employee_id.id)
            for input in inputs:
                amount = 0.0
                other_input_line = self.env['hr.inputs'].search([('employee_id', '=', employee_id),('input_id', '=', input.id),('state','in',['approve']),('payslip','=',False)])
                # ~ print (other_input_line)
                hr_inputs += other_input_line
                for line in other_input_line:
                    amount += line.amount
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'amount': amount,
                    'contract_id': contract.id,
                }
                res += [input_data]
            self.input_ids = hr_inputs
            hr_inputs.write({'payslip':True})
        return res
    
    @api.multi
    def compute_sheet(self):
        for payslip in self:
            # ~ payslip._compute_complete_name()
            if not payslip.settlement:
                sequence = payslip.group_id.sequence_payslip_id
                number = payslip.number or sequence.next_by_id()
                code_payslip = payslip.employee_id.group_id.code_payslip
            else:
                number = payslip.number or self.env['ir.sequence'].next_by_code('salary.settlement')
                code_payslip = ''
            payment_date = False
            if payslip.payslip_run_id:
                if payslip.payslip_run_id.payment_date:
                    payment_date = payslip.payslip_run_id.payment_date
            payslip.search_inputs()
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number, 'code_payslip':code_payslip, 'payment_date':payment_date})
            if payslip.settlement:
                val = {
                    'contract_id':payslip.contract_id.id,
                    'employee_id':payslip.employee_id.id,
                    'type':'02',
                    'date': payslip.date_end,
                    'wage':payslip.contract_id.wage,
                    'salary':payslip.contract_id.integral_salary,
                    'reason_liquidation':payslip.reason_liquidation,
                    }
                self.env['hr.employee.affiliate.movements'].create(val)
                payslip.contract_id.state = 'close'
                history = self.env['hr.change.job'].search([('employee_id', '=', self.employee_id.id),('contract_id', '=', self.contract_id.id)], limit=1)
                history.date_to = self.date_end
                history.low_reason = payslip.reason_liquidation
                if self.contract_id.contracting_regime == '02':
                    infonavit = self.env['hr.infonavit.credit.line'].search([('employee_id', '=', self.employee_id.id),('state', 'in', ['active','draft','discontinued'])], limit=1)
                    if infonavit:
                        infonavit.state = 'closed'
                        val_infonavit = {
                            'move_type': 'low_credit',
                            'date': self.date_end,
                            'infonavit_id':infonavit.id,
                            }
                        self.env['hr.infonavit.credit.history'].create(val_infonavit)
            payslip.payslip_run_id.set_tax_iva_honorarium()
        return True

    def _generate_sequence(self, code_group):
        '''
        Este metodo permite crear las secuencias pertenecientes a la permutacion de la mercaderia, con las divisiones
        y los proveedores
        :return:
        '''
        sequence_data=self.env['ir.sequence'].create({'prefix': '%s-' % code_group,
                                        'padding': 5,
                                        'implementation': 'no_gap',
                                        'code': 'salary.slip.%s' % (code_group),
                                        'name': 'Procesamiento de nómina'})
        return sequence_data
    
    @api.onchange('employee_id', 'date_from', 'date_to','contract_id')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        
        contract_ids = []
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang') or 'en_US'
        if self.settlement:
            self.name= _('FINIQUITO %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        else:
            self.name = _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))

        if not self.contract_id or employee.id != self.contract_id.employee_id.id:
            self.contract_id = False
            contract = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),('state','in',['open'])])
            if not contract:
                return
            self.contract_id = contract[0].id
            contract_ids = [contract[0].id]
        else:
            contract_ids = [self.contract_id.id]
            
        self.company_id = self.contract_id.company_id
        self.struct_id=False
        contracts = self.env['hr.contract'].browse(contract_ids)
        if not contracts[0].date_end and self.settlement:
            self.contract_id = False
            self.worked_days_line_ids = []
            return
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        self.worked_days_line_ids = []
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        self.payroll_month = str(date_from.month)
        table_id = self.env['table.settings'].search([('year','=',int(date_from.year))],limit=1).id
        if not table_id:
            title = _("Aviso!")
            message = 'Debe configurar una tabla de configuracion para el año del periodo de la nómina.'
            warning = {
                'title': title,
                'message': message
            }
            self.update({'date_end': False})
            return {'warning': warning}
        self.table_id = table_id
        self.employer_register_id = employee.employer_register_id.id
        return
        
    def search_inputs(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to) or (not self.contract_id):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contracts = self.contract_id
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        input_lines = self.input_line_ids.browse([])
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        self.input_line_ids = input_lines
        return
    
    @api.multi
    def compute_amount_untaxed(self):
        '''
        Este metodo calcula el monto de base imponible para la nomina a este monto se le calculara el impuesto
        '''
        for payslip in self:
            lines_untaxed = payslip.line_ids.filtered(lambda line: line.salary_rule_id.type == 'perception' and line.salary_rule_id.payroll_tax)
            payslip.subtotal_amount_untaxed = sum(lines_untaxed.mapped('amount'))
            payslip.get_tax_amount()


    @api.multi
    def get_tax_amount(self):
        '''
        Este metodo calcula el monto de impuesto para la nomina
        '''
        self.amount_tax = self.env['hr.isn'].get_value_isn(self.employee_id.work_center_id.state_id.id, self.subtotal_amount_untaxed, self.date_from.year)


    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to,payroll_period=False ):
        '''Este metodo hereda el comportamiento nativo para agregar los dias feriados, prima dominical al O2m de dias trabajados'''
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)
            # compute leave days
            leaves = {}
            total_leave_days=0
            hours_leave_days=0
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            inability = 0
            inability_hours = 0
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours
                if holiday.holiday_status_id.code in ['F08'] or not holiday.holiday_status_id.unpaid:
                    if holiday.holiday_status_id.time_type == 'inability':
                        inability += hours / work_hours
                        inability_hours += hours
                        if contract.employee_id.group_id.pay_three_days_disability:
                            if float(current_leave_struct['number_of_days']) > 3:
                                total_leave_days += hours / work_hours
                                hours_leave_days += hours
                    else:
                        total_leave_days += hours / work_hours
                        hours_leave_days += hours
            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to,
                                                                calendar=contract.resource_calendar_id, contract=contract)
            attendances_hours =  sum(attendace.hour_to - attendace.hour_from
                                    for attendace in calendar.attendance_ids
                                    )
            attendances_list = calendar.attendance_ids.mapped('dayofweek')
            count_days_week = list(set(attendances_list))
            count_days_weeks = {
                'name': _("Dias semana"),
                'sequence': 1,
                'code': 'DIASEMANA',
                'number_of_days': len(count_days_week),
                'number_of_hours': attendances_hours,
                'contract_id': contract.id,
            }
            days_factor = contract.employee_id.group_id.days
            elemento_calculo = {
                'name': _("Periodo mensual"),
                'sequence': 1,
                'code': 'PERIODO100',
                'number_of_days': days_factor,
                'number_of_hours': 0,
                'contract_id': contract.id,
            }
            res.append(elemento_calculo)
            date_start = date_from if contract.date_start < date_from else contract.date_start
            date_end =  contract.date_end if contract.date_end and contract.date_end < date_to else date_to
            from_full = date_start
            to_full = date_end + timedelta(days=1)
            payroll_periods_days = {
                '05': 30,
                '04': 15,
                '02': 7,
                '10': 10,
                '01': 1,
                                }
            period = self.payroll_period
            if payroll_period:
                period = payroll_period
            if (to_full - from_full).days >= payroll_periods_days[period]:
                cant_days = payroll_periods_days[period]*(days_factor/30)
            else:
                cant_days = (to_full - from_full).days*(days_factor/30)
            if cant_days < 0:
                cant_days = 0
            if contract.contracting_regime == '02':
                cant_days_IMSS = {
                    'name': _("Días a cotizar en la nómina"),
                    'sequence': 1,
                    'code': 'DIASIMSS',
                    'number_of_days': cant_days - inability,
                    'number_of_hours': (cant_days * contract.resource_calendar_id.hours_per_day) - inability_hours ,
                    'contract_id': contract.id,
                }
                res.append(cant_days_IMSS)
            if contract.employee_id.pay_holiday:
                dias_feriados = {
                    'name': _("Días feriados"),
                    'sequence': 1,
                    'code': 'FERIADO',
                    'number_of_days': work_data['public_days'],
                    'number_of_hours': work_data['public_days_hours'],
                    'contract_id': contract.id,
                }
                res.append(dias_feriados)
            prima_dominical = {
                'name': _("DOMINGO"),
                'sequence': 1,
                'code': 'DOMINGO',
                'number_of_days': work_data['sundays'],
                'number_of_hours': work_data['sundays_hours'],
                'contract_id': contract.id,
            }
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': cant_days - total_leave_days,
                'number_of_hours': (cant_days * contract.resource_calendar_id.hours_per_day) - hours_leave_days,
                'contract_id': contract.id,
            }
            res.append(count_days_weeks)
            res.append(attendances)
            res.append(prima_dominical)
            res.extend(leaves.values())
        return res
        
    @api.onchange('contract_id')
    def onchange_contract(self):
        return
    
    @api.multi
    def unlink(self):
        for pay in self:
            pay.input_ids.write({'payslip':False,'state':'approve'})
        return super(HrPayslip, self).unlink()
    
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
        if run_data['employer_register_id']:
            res['value']['employer_register_id'] = run_data['employer_register_id'][0]
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

    @api.multi
    def write(self, vals):
        payslip = super(HrPayslip, self).write(vals)
        if 'code_payslip' and 'number' in vals:
           self.complete_name = self.code_payslip +'/'+ self.number
        return payslip


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    
    type_perception = fields.Selection(
        selection=[('001', 'Sueldos, Salarios  Rayas y Jornales'), 
                   ('002', 'Gratificación Anual (Aguinaldo)'), 
                   ('003', 'Participación de los Trabajadores en las Utilidades PTU'),
                   ('004', 'Reembolso de Gastos Médicos Dentales y Hospitalarios'), 
                   ('005', 'Fondo de ahorro'),
                   ('006', 'Caja de ahorro'),
                   ('009', 'Contribuciones a Cargo del Trabajador Pagadas por el Patrón'), 
                   ('010', 'Premios por puntualidad'),
                   ('011', 'Prima de Seguro de vida'), 
                   ('012', 'Seguro de Gastos Médicos Mayores'), 
                   ('013', 'Cuotas Sindicales Pagadas por el Patrón'), 
                   ('014', 'Subsidios por incapacidad'),
                   ('015', 'Becas para trabajadores y/o hijos'), 
                   ('019', 'Horas extra'),
                   ('020', 'Prima dominical'), 
                   ('021', 'Prima vacacional'),
                   ('022', 'Prima por antigüedad'),
                   ('023', 'Pagos por separación'),
                   ('024', 'Seguro de retiro'),
                   ('025', 'Indemnizaciones'), 
                   ('026', 'Reembolso por funeral'), 
                   ('027', 'Cuotas de seguridad social pagadas por el patrón'), 
                   ('028', 'Comisiones'),
                   ('029', 'Vales de despensa'),
                   ('030', 'Vales de restaurante'),
                   ('031', 'Vales de gasolina'),
                   ('032', 'Vales de ropa'),
                   ('033', 'Ayuda para renta'),
                   ('034', 'Ayuda para artículos escolares'),
                   ('035', 'Ayuda para anteojos'),
                   ('036', 'Ayuda para transporte'),
                   ('037', 'Ayuda para gastos de funeral'),
                   ('038', 'Otros ingresos por salarios'),
                   ('039', 'Jubilaciones, pensiones o haberes de retiro'),
                   ('044', 'Jubilaciones, pensiones o haberes de retiro en parcialidades'),
                   ('045', 'Ingresos en acciones o títulos valor que representan bienes'),
                   ('046', 'Ingresos asimilados a salarios'),
                   ('047', 'Alimentación diferentes a los establecidos en el Art 94 último párrafo LISR'),
                   ('048', 'Habitación'),
                   ('049', 'Premios por asistencia'),
                   ('050', 'Viáticos'),
                   ('051', 'Pagos por gratificaciones, primas, compensaciones, recompensas u otros a extrabajadores derivados de jubilación en parcialidades'),
                   ('052', 'Pagos que se realicen a extrabajadores que obtengan una jubilación en parcialidades derivados de la ejecución de resoluciones judicial o de un laudo'),
                   ('053', 'Pagos que se realicen a extrabajadores que obtengan una jubilación en una sola exhibición derivados de la ejecución de resoluciones judicial o de un laudo'),
                   ],
        string=_('Type of perception'),
    )
    type_deduction = fields.Selection(
        selection=[('001', 'Seguridad social'), 
                   ('002', 'ISR'), 
                   ('003', 'Aportaciones a retiro, cesantía en edad avanzada y vejez.'),
                   ('004', 'Otros'), 
                   ('005', 'Aportaciones a Fondo de vivienda'),
                   ('006', 'Descuento por incapacidad'),
                   ('007', 'Pensión alimenticia'),
                   ('008', 'Renta'),
                   ('009', 'Préstamos provenientes del Fondo Nacional de la Vivienda para los Trabajadores'), 
                   ('010', 'Pago por crédito de vivienda'),
                   ('011', 'Pago de abonos INFONACOT'), 
                   ('012', 'Anticipo de salarios'), 
                   ('013', 'Pagos hechos con exceso al trabajador'), 
                   ('014', 'Errores'),
                   ('015', 'Pérdidas'), 
                   ('016', 'Averías'), 
                   ('017', 'Adquisición de artículos producidos por la empresa o establecimiento'),
                   ('018', 'Cuotas para la constitución y fomento de sociedades cooperativas y de cajas de ahorro'), 				   
                   ('019', 'Cuotas sindicales'),
                   ('020', 'Ausencia (Ausentismo)'), 
                   ('021', 'Cuotas obrero patronales'),
                   ('022', 'Impuestos Locales'),
                   ('023', 'Aportaciones voluntarias'),
                   ('024', 'Ajuste en Gratificación Anual (Aguinaldo) Exento'),
                   ('025', 'Ajuste en Gratificación Anual (Aguinaldo) Gravado'),
                   ('026', 'Ajuste en Participación de los Trabajadores en las Utilidades PTU Exento'),
                   ('027', 'Ajuste en Participación de los Trabajadores en las Utilidades PTU Gravado'),
                   ('028', 'Ajuste en Reembolso de Gastos Médicos Dentales y Hospitalarios Exento'),
                   ('029', 'Ajuste en Fondo de ahorro Exento'),
                   ('030', 'Ajuste en Caja de ahorro Exento'),
                   ('031', 'Ajuste en Contribuciones a Cargo del Trabajador Pagadas por el Patrón Exento'),
                   ('032', 'Ajuste en Premios por puntualidad Gravado'),
                   ('033', 'Ajuste en Prima de Seguro de vida Exento'),
                   ('034', 'Ajuste en Seguro de Gastos Médicos Mayores Exento'),
                   ('035', 'Ajuste en Cuotas Sindicales Pagadas por el Patrón Exento'),
                   ('036', 'Ajuste en Subsidios por incapacidad Exento'),
                   ('037', 'Ajuste en Becas para trabajadores y/o hijos Exento'),
                   ('038', 'Ajuste en Horas extra Exento'),
                   ('039', 'Ajuste en Horas extra Gravado'),
                   ('040', 'Ajuste en Prima dominical Exento'),
                   ('041', 'Ajuste en Prima dominical Gravado'),
                   ('042', 'Ajuste en Prima vacacional Exento'),
                   ('043', 'Ajuste en Prima vacacional Gravado'),
                   ('044', 'Ajuste en Prima por antigüedad Exento'),
                   ('045', 'Ajuste en Prima por antigüedad Gravado'),
                   ('046', 'Ajuste en Pagos por separación Exento'),
                   ('047', 'Ajuste en Pagos por separación Gravado'),
                   ('048', 'Ajuste en Seguro de retiro Exento'),
                   ('049', 'Ajuste en Indemnizaciones Exento'),
                   ('050', 'Ajuste en Indemnizaciones Gravado'),
                   ('051', 'Ajuste en Reembolso por funeral Exento'),
                   ('052', 'Ajuste en Cuotas de seguridad social pagadas por el patrón Exento'),
                   ('053', 'Ajuste en Comisiones Gravado'),
                   ('054', 'Ajuste en Vales de despensa Exento'),
                   ('055', 'Ajuste en Vales de restaurante Exento'),
                   ('056', 'Ajuste en Vales de gasolina Exento'),
                   ('057', 'Ajuste en Vales de ropa Exento'),
                   ('058', 'Ajuste en Ayuda para renta Exento'),
                   ('059', 'Ajuste en Ayuda para artículos escolares Exento'),
                   ('060', 'Ajuste en Ayuda para anteojos Exento'),
                   ('061', 'Ajuste en Ayuda para transporte Exento'),
                   ('062', 'Ajuste en Ayuda para gastos de funeral Exento'),
                   ('063', 'Ajuste en Otros ingresos por salarios Exento'),
                   ('064', 'Ajuste en Otros ingresos por salarios Gravado'),
                   ('065', 'Ajuste en Jubilaciones, pensiones o haberes de retiro en una sola exhibición Exento '),
                   ('066', 'Ajuste en Jubilaciones, pensiones o haberes de retiro en una sola exhibición Gravado '),
                   ('067', 'Ajuste en Pagos por separación Acumulable '),
                   ('068', 'Ajuste en Pagos por separación No acumulable'),
                   ('069', 'Ajuste en Jubilaciones, pensiones o haberes de retiro en parcialidades Exento'),
                   ('070', 'Ajuste en Jubilaciones, pensiones o haberes de retiro en parcialidades Gravado'),
                   ('071', 'Ajuste en Subsidio para el empleo (efectivamente entregado al trabajador)'),
                   ('072', 'Ajuste en Ingresos en acciones o títulos valor que representan bienes Exento'),
                   ('073', 'Ajuste en Ingresos en acciones o títulos valor que representan bienes Gravado'),
                   ('074', 'Ajuste en Alimentación Exento'),
                   ('075', 'Ajuste en Alimentación Gravado'),
                   ('076', 'Ajuste en Habitación Exento'),
                   ('077', 'Ajuste en Habitación Gravado'),
                   ('078', 'Ajuste en Premios por asistencia'),
                   ('079', 'Ajuste en Pagos distintos a los listados y que no deben considerarse como ingreso por sueldos, salarios o ingresos asimilados.'),
                   ('080', 'Ajuste en Viáticos gravados.'),
                   ('081', 'Ajuste en Viáticos (entregados al trabajador)'),
                   ('082', 'Ajuste en Fondo de ahorro Gravado'),
                   ('083', 'Ajuste en Caja de ahorro Gravado'),
                   ('084', 'Ajuste en Prima de Seguro de vida Gravado'),
                   ('085', 'Ajuste en Seguro de Gastos Médicos Mayores Gravado'),
                   ('086', 'Ajuste en Subsidios por incapacidad Gravado'),
                   ('087', 'Ajuste en Becas para trabajadores y/o hijos Gravado'),
                   ('088', 'Ajuste en Seguro de retiro Gravado'),
                   ('089', 'Ajuste en Vales de despensa Gravado'),
                   ('090', 'Ajuste en Vales de restaurante Gravado'),
                   ('091', 'Ajuste en Vales de gasolina Gravado'),
                   ('092', 'Ajuste en Vales de ropa Gravado'),
                   ('093', 'Ajuste en Ayuda para renta Gravado'),
                   ('094', 'Ajuste en Ayuda para artículos escolares Gravado'),
                   ('095', 'Ajuste en Ayuda para anteojos Gravado'),
                   ('096', 'Ajuste en Ayuda para transporte Gravado'),
                   ('097', 'Ajuste en Ayuda para gastos de funeral Gravado'),
                   ('098', 'Ajuste a ingresos asimilados a salarios gravados'),
                   ('099', 'Ajuste a ingresos por sueldos y salarios gravados'),
                   ('100', 'Ajuste en Viáticos exentos'),
                   ('101', 'ISR Retenido de ejercicio anterior'),
                   ('102', 'Ajuste a pagos por gratificaciones, primas, compensaciones, recompensas u otros a extrabajadores derivados de jubilación en parcialidades, gravados'),
                   ('103', 'Ajuste a pagos que se realicen a extrabajadores que obtengan una jubilación en parcialidades derivados de la ejecución de una resolución judicial o de un laudo gravados'),
                   ('104', 'Ajuste a pagos que se realicen a extrabajadores que obtengan una jubilación en parcialidades derivados de la ejecución de una resolución judicial o de un laudo exentos'),
                   ('105', 'Ajuste a pagos que se realicen a extrabajadores que obtengan una jubilación en una sola exhibición derivados de la ejecución de una resolución judicial o de un laudo gravados'),
                   ('106', 'Ajuste a pagos que se realicen a extrabajadores que obtengan una jubilación en una sola exhibición derivados de la ejecución de una resolución judicial o de un laudo exentos'),
                   ('107', 'Ajuste al Subsidio Causado '),
                   ],
        string=_('Type of deduction'),
    )
    type_other_payment = fields.Selection(
        selection=[('001', 'Reintegro de ISR pagado en exceso'), 
                   ('002', 'Subsidio para el empleo'), 
                   ('003', 'Viáticos.'),
                   ('004', 'Apliación de saldo a favor por compensación anual'), 
                   ('005', 'Reintegro de ISR retenido en exceso de ejercicio anterior'),
                   ('006', 'Alimentos en bienes (Servicios de comedor y comida) Art 94 último párrafo LISR'),
                   ('007', 'ISR ajustado por subsidio'),
                   ('008', 'Subsidio efectivamente entregado que no correspondía (Aplica sólo cuando haya ajuste al cierre de mes en relación con el Apéndice 7 de la guía de llenado de nómina)'),
                   ('999', 'Cuotas obrero patronales')],
        string=_('Otros Pagos'),
    )
    type = fields.Selection([
        ('not_apply', 'Does not apply'),
        ('perception', 'Perception'),
        ('deductions', 'Deductions'),
        ('other_payment', 'Otros Pagos')
        ], string='Type', default="not_apply")
    type_overtime = fields.Selection([
        ('01', 'Dobles'),
        ('02', 'Triples'),
        ('03', 'Simples'),
        ], string='Tipo de Hora Extra')
    type_disability = fields.Selection([
        ('01', 'Riesgo de trabajo.'),
        ('02', 'Enfermedad en general.'),
        ('03', 'Maternidad.'),
        ('04', 'Licencia por cuidados médicos de hijos diagnosticados con cáncer.'),
        ], string='Tipo de incapacidad')
    payment_type = fields.Selection([
        ('01', 'Species.'),
        ('02', 'Cash.'),
        ], string='Payment Type', default="02")
    payroll_tax = fields.Boolean('Apply payroll tax?', default=False, help="If selected, this rule will be taken for the calculation of payroll tax.")
    settlement = fields.Boolean(string='Settlement structure?')
    salary_rule_taxed_id = fields.Many2one('hr.salary.rule', "Regla (Monto Gravado)", required=False, copy=False)
    code_category_id = fields.Char(related='category_id.code')
    apply_variable_compute = fields.Boolean(string='Apply for variable salary calculation')
    

class HrInputs(models.Model):
    _name = 'hr.inputs'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, states={'approve': [('readonly', False)]})
    payslip = fields.Boolean('Payroll?')
    amount = fields.Float('Amount', readonly=True, states={'approve': [('readonly', False)]}, digits=(16, 2))
    input_id = fields.Many2one('hr.rule.input', string='Input', required=True, readonly=True, states={'approve': [('readonly', False)]})
    code = fields.Char(string='Code', related="input_id.code")
    state = fields.Selection([
        ('approve', 'Approved'),
        ('paid', 'Reported on payroll')], string='Status', readonly=True, default='approve')
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', related= 'input_id.type', readonly=True, store=True)
    group_id = fields.Many2one('hr.group', "Group", related= 'employee_id.group_id', readonly=True, store=True)
    date_overtime = fields.Date('Fecha', readonly=True, states={'approve': [('readonly', False)]})

    @api.multi
    def name_get(self):
        result = []
        for inputs in self:
            name = '%s %s %s' %(inputs.employee_id.name.upper(), inputs.input_id.name.upper(), str(inputs.amount))
            result.append((inputs.id, name))
        return result


class HrRuleInput(models.Model):
    _inherit = 'hr.rule.input'
    
    @api.model
    def name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|',('code', operator, name),('name', operator, name)]
        rule_input = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(rule_input).name_get()
    
    type = fields.Selection([
        ('perception', 'Perception'),
        ('deductions', 'Deductions')], string='Type', required=True)
    input_id = fields.Many2one('hr.salary.rule', string='Salary Rule Input', required=False)
