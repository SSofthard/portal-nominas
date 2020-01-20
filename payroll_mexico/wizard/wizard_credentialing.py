# -*- coding: utf-8 -*-

import io
import base64
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from lxml import etree,html
from lxml.html.builder import *

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.image import image_data_uri

import imgkit
import tempfile

class hrEmployeeCredentialingWizard(models.TransientModel):
    _name = "hr.employee.credentialing.wizard"
    _description = 'Formulario de credencialización'

    #Columns
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    contracting_regime = fields.Selection([
        ('01', 'Assimilated to wages'),
        ('02', 'Wages and salaries'),
        ('03', 'Senior citizens'),
        ('04', 'Pensioners'),
        ('05', 'Free')], string='Regimen de contratación', required=True, default="02")
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Empleados a carnetizar')
    target_layout_id = fields.Many2one(comodel_name='ir.ui.view', string='Plantillas', domain="[('name','like','%credential%')]")
    template_id = fields.Many2one(comodel_name='credential.template', string='Plantillas')
    body_html = fields.Text(string='Frontal')
    back_html = fields.Text(string='Reverso')

    @api.onchange('employer_register_id', 'contracting_regime', 'work_center_id','group_id')
    def onchange_fields_filters(self):
        contract = self.env['hr.contract']
        domain_employer_register = [('employer_register_id', '=', self.employer_register_id.id)] if self.employer_register_id else []
        domain_work_center = [('employee_id.work_center_id', '=', self.work_center_id.id)] if self.work_center_id else []
        domain= [
            ('state', '=', 'open'),
            ('employee_id.group_id', '=', self.group_id.id),
            ('contracting_regime', '=', self.contracting_regime)
        ]
        employees = contract.search_read(domain + domain_employer_register, ['employee_id', 'state'])
        employee_ids = []
        for employee in employees:
            employee_ids.append(employee['employee_id'][0])
        return {'domain': {'employee_ids': [('id', 'in', employee_ids)]}}


    def report_credentaling(self):
        '''

        '''
        fronts = {}
        backs = {}
        for employee in self.employee_ids:
            templates_front = self.env['mail.template']._render_template(template_txt=self.body_html, model=employee._name,res_ids=employee._ids, post_process=False)
            templates_front[employee.id] = self.make_src_image(templates_front[employee.id])

            # print ('templates_front')
            # print (templates_front)
            templates_back = self.env['mail.template']._render_template(template_txt=self.back_html, model=employee._name,res_ids=employee._ids, post_process=False)
            templates_back[employee.id] = self.make_src_image(templates_back[employee.id])
            # print(templates_back)
            fronts.update(templates_front)
            backs.update(templates_back)
        vals = {
            'doc_ids':self.employee_ids._ids,
            'template_id':self.target_layout_id.key,
            'front_html': fronts,
            'back_html': backs,
            'paperformat':  self.get_paperformat(),
        }
        paperformat = self.get_paperformat()
        res = self.env.ref('payroll_mexico.payroll_mexico_report_credentaling').report_action(self, data=vals)
        print (res)
        print (res)

        print (paperformat)
        print (paperformat)
        print (paperformat)
        res.update({'paperformat_id': paperformat.id})
        print ('resresres')
        print ('resresres')
        print ('resresres')
        print (res['context'])
        # print(x)
        return res

    def get_paperformat(self):
        '''

        '''
        paperformat = self.env['report.paperformat'].search([('name','=',self.template_id.size),('orientation','=',self.template_id.orientation.capitalize())])
        return paperformat

    def add_template(self):
        '''

        '''
        vals = {
            'name': 'Plantilla %s' % fields.Date.context_today(self),
            'body_html':self.body_html
        }
        self.env['credential.template'].create(vals)


    @api.onchange('template_id')
    def onchange_template_id(self):
        '''

        '''
        self.body_html = self.template_id.body_html
        self.back_html = self.template_id.back_html

    def make_src_image(self, template):
        '''

        '''
        element = etree.HTML(template)
        for img in element.xpath('//img'):
            img_data=img.get('data')
            if img_data:
                img_data = img_data.replace("b'","").replace("'","")
                img.set('src','%s' % image_data_uri(bytes(img_data,'utf-8')))
        template = html.tostring(element)
        return template


    def action_print_png(self):
        '''
        Este metodo es para imprimir el txt de la liquidación que va a ser
        '''
        fronts = {}
        backs = {}
        zip_list = []
        for employee in self.employee_ids:
            templates_front = self.env['mail.template']._render_template(
                template_txt=self.body_html, model=employee._name,
                res_ids=employee._ids, post_process=False)
            templates_front[employee.id] = self.make_src_image(
                templates_front[employee.id])

            # print ('templates_front')
            # print (templates_front)
            templates_back = self.env['mail.template']._render_template(
                template_txt=self.back_html, model=employee._name,
                res_ids=employee._ids, post_process=False)
            templates_back[employee.id] = self.make_src_image(
                templates_back[employee.id])
            # print(templates_back)
            fronts.update(templates_front)
            backs.update(templates_back)
            output = io.BytesIO()
            file_png = []
            print ('imprimir txt')
            print ('imprimir txt')
            print ('imprimir txt')
            print ('imprimir txt')
            temporary_files = []
            f_name = 'credencializacion'
            prefix = 'credencializacion'
            body_file_fd, body_file_path = tempfile.mkstemp(suffix='.png',
                                                            prefix=prefix)
            object = open(body_file_fd, 'r')
            print (object)
            print (object)
            print (object)
            print (object)
            print (object)
            print (body_file_path)
            print (body_file_fd)
            res = imgkit.from_string(fronts[employee.id].decode('utf-8'), body_file_path)
            print (body_file_fd)
            print (body_file_fd)
            print (body_file_path)
            print (body_file_path)
            zip_list.append((body_file_path, body_file_fd))
            # with closing(os.fdopen(body_file_fd, 'wb')) as body_file:
            #     body_file.write(self.body_html)
            # paths.append(body_file_path)
            temporary_files.append(body_file_path)
            content = self.body_html
            print (type(content))
        file_like_object = io.BytesIO()
        zipfile_ob = zipfile.ZipFile(file_like_object, 'w')
        for zip in zip_list:
            zipfile_ob.write(zip[0], zip[1]) # In order to remove the absolute path
        zipfile_ob.close()
        print ('file_like_object')
        print ('file_like_object.getvalue()')
        data = base64.encodebytes(file_like_object.getvalue())
        export_id = self.env['hr.fees.settlement.report.txt'].create(
            {'txt_file': data, 'file_name': f_name + '.zip'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.fees.settlement.report.txt',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': export_id.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
