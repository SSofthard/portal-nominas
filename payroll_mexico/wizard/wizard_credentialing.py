# -*- coding: utf-8 -*-

import io
import base64
import imgkit
import tempfile
import zipfile
import socket
import requests


from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from lxml import etree,html
from lxml.html.builder import *

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.image import image_data_uri


class hrEmployeeCredentialingWizard(models.TransientModel):
    _name = "hr.employee.credentialing.wizard"
    _description = 'Formulario de credencialización'

    #Columns
    group_id = fields.Many2one('hr.group', "Grupo", required=True)
    work_center_id = fields.Many2one('hr.work.center', "Centro de trabajo", required=False)
    employer_register_id = fields.Many2one('res.employer.register', "Registro Patronal", required=False)
    contracting_regime = fields.Selection([
        ('02', 'Wages and salaries'),
        ('05', 'Free'),
        ('08', 'Assimilated commission agents'),
        ('09', 'Honorary Assimilates'),
        ('11', 'Assimilated others'),
        ('99', 'Other regime'),
    ], string='Contracting Regime', required=True, default="02")
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
        res.update({'paperformat_id': paperformat.id})
        print ('resresres')
        print ('resresres')
        print ('resresres')
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
        print ('elementelementelement')
        print (element)
        print (element)
        for img in element.xpath('//img'):
            img_data = img.get('data')
            if img_data:
                img_data = img_data.replace("b'","").replace("'","")
                img.set('src','%s' % image_data_uri(bytes(img_data,'utf-8')))
        template = html.tostring(element)
        return template

    def add_host_barcode(self, template, employee):
        '''

        '''
        element = etree.HTML(template)
        host = socket.gethostname()
        for img in element.xpath('//img[@alt="Barcode"]'):
            img_src = img.get('src')
            if img_src:
                dict_vals={}
                vals = img_src.split('?')[-1].split('&')
                for item in vals:
                    item = item.split('=')
                    dict_vals.update({item[0]:item[1]})
                dict_vals['value'] = dict_vals['value'].split('object.')[-1].split('%')[0]
                dict_vals['value'] = getattr(employee, dict_vals['value'])
                barcode = self.env['ir.actions.report'].barcode(dict_vals['type'], value=dict_vals['value'], width=dict_vals['width'], height=dict_vals['height'])
                img.set('src', '%s' % image_data_uri(base64.b64encode(barcode)))
        template = html.tostring(element)
        return template


    def action_print_png(self):
        '''
        Este metodo es para imprimir el txt de la liquidación que va a ser
        '''
        fronts = {}
        backs = {}
        zip_list = []
        sizes = getattr(self.template_id, self.template_id.orientation)[self.template_id.size]
        f_name = 'credencializacion_%s_%s' % (self.template_id.name, fields.Date.context_today(self))
        for employee in self.employee_ids:
            element = etree.HTML(self.body_html)
            element.set('style','display: table')
            body_html = html.tostring(element)
            element_back = etree.HTML(self.back_html)
            element_back.set('style', 'display: table')
            back_html = html.tostring(element_back)
            templates_front = self.env['mail.template']._render_template(
                template_txt=body_html, model=employee._name,
                res_ids=employee._ids, post_process=False)
            templates_front[employee.id] = self.make_src_image(
                templates_front[employee.id])
            templates_front[employee.id] = self.add_host_barcode(
                templates_front[employee.id],employee)
            templates_back = self.env['mail.template']._render_template(
                template_txt=back_html, model=employee._name,
                res_ids=employee._ids, post_process=False)
            templates_back[employee.id] = self.make_src_image(
                templates_back[employee.id])
            templates_back[employee.id] = self.add_host_barcode(
                templates_back[employee.id], employee)
            fronts.update(templates_front)
            backs.update(templates_back)
            temporary_files = []
            prefix_front = 'credencializacion_front_%s_' % employee.barcode
            prefix_back = 'credencializacion_back_%s_' % employee.barcode
            body_front_file_fd, body_front_file_path = tempfile.mkstemp(suffix='.png',
                                                            prefix=prefix_front)
            body_back_file_fd, body_back_file_path = tempfile.mkstemp(suffix='.png',
                                                            prefix=prefix_back)
            imgkit.from_string(fronts[employee.id].decode('utf-8'), body_front_file_path, {'width':sizes['width'], 'quality':100,'quiet':''})
            zip_list.append((body_front_file_path, body_front_file_fd,prefix_front))
            imgkit.from_string(backs[employee.id].decode('utf-8'), body_back_file_path, {'width':sizes['width'], 'quality':100,'quiet':''})
            zip_list.append((body_back_file_path, body_back_file_fd,prefix_back))
        file_like_object = io.BytesIO()
        zipfile_ob = zipfile.ZipFile(file_like_object, 'w')
        for zip in zip_list:
            zipfile_ob.write(zip[0], zip[2]) # In order to remove the absolute path
        zipfile_ob.close()
        data = base64.encodebytes(file_like_object.getvalue())
        export_id = self.env['hr.credential.zip.wizard'].create(
            {'zip_file': data, 'file_name': f_name + '.zip'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.credential.zip.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': export_id.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
