# -*- coding: utf-8 -*-

import base64

import datetime
from datetime import date
from lxml import etree,html
from lxml.html.builder import *

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.addons.payroll_mexico.pyfiscal.generate_company import GenerateRfcCompany
from odoo.tools.image import image_data_uri


class CredentialTemplate(models.Model):
    _name = 'credential.template'

    @api.model
    def _default_template(self):
        '''

        '''
        html_table = TABLE(
            TBODY(
                TR(ATTR(id="1"),
                   TD(style='padding-top: 10%;padding-bottom: 10%;padding-left: 10%;padding-right: 10%;position:relative'),
                   ),
            )

        )
        html_table.set('name','frame')
        return html.tostring(html_table)

    portrait = {
        'CR80': {'height': 243, 'width': 153},
        'CR79': {'height': 237.816, 'width': 147.672},
        'CR100': {'height': 279.36, 'width': 189.36},
    }

    landscape = {
        'CR80': {'width': 243, 'height': 153},
        'CR79': {'width': 237.816, 'height': 147.672},
        'CR100': {'width': 279.36, 'height': 189.36},
    }

    #Columns
    name = fields.Char(string='Nombre de la plantilla')
    size = fields.Selection([
            ('CR80','CR80'),
            ('CR79','CR79'),
            ('CR100','CR100'),
        ],default = 'CR80',string='Tamaño', required=True)
    orientation = fields.Selection([
            ('portrait','Retrato'),
            ('landscape','Paisaje'),
        ], default = 'portrait',string='Orientación')
    body_html = fields.Text(string='Frontal', default=_default_template)
    back_html = fields.Text(string='Reverso', default=_default_template)
    # fields = fields.Many2many(comodel_name = 'ir.model.fields', string='Campos a agregar')
    fields_credential_ids = fields.One2many(inverse_name='template_id',comodel_name = 'credential.fields', string='Campos agregados')
    background_color_body = fields.Char(string="Color de fondo", default='rgba(255,255,255,0.94)')
    background_color_back = fields.Char(string="Color de fondo", default='rgba(255,255,255,0.94)')
    background_image_body = fields.Binary(string="Imagen de fondo", attachment=True,
        help="Imagen de fondo, limitado a 1024x1024px.")
    background_image_back = fields.Binary(string="Imagen de fondo", attachment=True,
        help="Imagen de fondo, limitado a 1024x1024px.")
    body_background_type = fields.Selection([('image','Imagen de fondo'),('color','Color de fondo')], default='color')
    back_background_type = fields.Selection([('image','Imagen de fondo'),('color','Color de fondo')], default='color')

    @api.onchange('background_color_body')
    def onchange_background_color_body(self):
        '''

        '''
        if self.background_color_body:
            element = etree.HTML(self.body_html)
            nodes = element.xpath('//table[@name="frame"]')
            for node in nodes:
                if node.get('style'):
                    style = node.get('style').split(';')
                    dict_style = {}
                    for item in style:
                        list_item = item.strip().split(':')
                        if len(list_item) > 1:
                            dict_style.update({list_item[0]:list_item[1]})
                    if dict_style.get('background-image'):
                        del dict_style['background-image']
                    dict_style.update({'background-color':self.background_color_body})
                    style_str = ''
                    for key in dict_style.keys():
                        style_str+='%s: %s; ' % (key, dict_style[key])
                    node.set('style', style_str)
            self.body_html = html.tostring(element) \

    @api.onchange('background_image_body')
    def onchange_background_image_body(self):
        '''

        '''
        sizes = getattr(self, self.orientation)[self.size]
        if self.background_image_body:
            element = etree.HTML(self.body_html)
            nodes = element.xpath('//table[@name="frame"]')
            for node in nodes:
                if node.get('style'):
                    style = node.get('style').split(';')
                    dict_style = {}
                    for item in style:
                        list_item = item.strip().split(':')
                        if len(list_item) > 1:
                            dict_style.update({list_item[0]:list_item[1]})
                    dict_style.update({'background-color':self.background_color_body})
                    if dict_style.get('background-color'):
                        del dict_style['background-color']
                    content = bytes(self.background_image_body,'utf-8')
                    dict_style.update({'background-image': 'url("%s"); background-size: %spt %spt;' % (image_data_uri(content),sizes['width'], sizes['height'])})
                    style_str = ''
                    for key in dict_style.keys():
                        style_str+='%s: %s; ' % (key, dict_style[key])
                    node.set('style', style_str)
            self.body_html = html.tostring(element)\

    @api.onchange('background_image_back')
    def onchange_background_image_back(self):
        '''

        '''
        sizes = getattr(self, self.orientation)[self.size]
        if self.background_image_back:
            element = etree.HTML(self.back_html)
            nodes = element.xpath('//table[@name="frame"]')
            for node in nodes:
                if node.get('style'):
                    style = node.get('style').split(';')
                    dict_style = {}
                    for item in style:
                        list_item = item.strip().split(':')
                        if len(list_item) > 1:
                            dict_style.update({list_item[0]:list_item[1]})
                    if dict_style.get('background-color'):
                        del dict_style['background-color']
                    content = bytes(self.background_image_back,'utf-8')
                    dict_style.update({'background-image': 'url("%s"); background-size: %spt %spt;' % (image_data_uri(content),sizes['width'], sizes['height'])})
                    style_str = ''
                    for key in dict_style.keys():
                        style_str+='%s: %s; ' % (key, dict_style[key])
                    node.set('style', style_str)
            self.back_html = html.tostring(element)

    @api.onchange('background_color_back')
    def onchange_background_color_back(self):
        '''

        '''
        if self.background_color_back:
            element = etree.HTML(self.back_html)
            nodes = element.xpath('//table[@name="frame"]')
            for node in nodes:
                if node.get('style'):
                    style = node.get('style').split(';')
                    dict_style = {}
                    for item in style:
                        list_item = item.strip().split(':')
                        if len(list_item) > 1:
                            dict_style.update({list_item[0]:list_item[1]})
                    if dict_style.get('background-image'):
                        del dict_style['background-image']
                    dict_style.update({'background-color':self.background_color_back})
                    style_str = ''
                    for key in dict_style.keys():
                        style_str+='%s: %s; ' % (key, dict_style[key])
                    node.set('style', style_str)
            self.back_html = html.tostring(element)


    @api.model
    def create(self,vals):
        print (vals)
        print (self.body_html)
        print(vals['body_html'])
        print (vals['back_html'])
        res_id = super(CredentialTemplate, self).create(vals)
        return res_id

    @api.onchange('size','orientation')
    def onchange_size_template(self):
        '''

        '''
        sizes = getattr(self,self.orientation)[self.size]
        element_front = etree.HTML(self.body_html)
        element_back = etree.HTML(self.back_html)
        table_front = element_front.xpath('//table[@name="frame"]')
        table_back = element_back.xpath('//table[@name="frame"]')
        for node in table_front:
            node.set(
                'style','width:%spt; height:%spt; border: 2pt solid black; border-collapse:separate; border-radius:8pt; margin:5pt;' % (sizes['width'], sizes['height']
                                                                                                                                        )
            )
        for node in table_back:
            node.set(
                'style','width:%spt; height:%spt; border: 2pt solid black; border-collapse:separate; border-radius:8pt; margin:5pt;' % (sizes['width'], sizes['height']
                                                                                                                                        )
            )
        self.body_html = html.tostring(element_front)
        self.back_html = html.tostring(element_back)

    @api.onchange('fields_credential_ids')
    def onchange_fields_credential_ids(self):
        '''
        Este metodo armara la vista html segun la configuración de los campos establecida en el formulario
        '''
        model = self.env['hr.employee']
        for field_credential in self.fields_credential_ids:
            print (field_credential.sheet)
            print (field_credential.sheet)
            print (field_credential.sheet)
            print (self.body_html  if field_credential.sheet =='front' else self.back_html)
            element = etree.HTML(self.body_html if field_credential.sheet =='front' else self.back_html)
            if field_credential.field_selection:
                if field_credential.field_selection.split('.')[-1] == 'barcode':
                    element = field_credential._get_snippet_barcode(element)
                else:
                    get_snippet = getattr(field_credential,'_get_snippet_%s' % field_credential.field_type)
                    element = get_snippet(element)
                element_html = html.tostring(element, pretty_print=True, method='xml', encoding='unicode')
                print (element_html)
                if field_credential.sheet =='front':
                    self.body_html = str(element_html)
                else:
                    self.back_html = str(element_html)

class AddFields(models.Model):
    _name='credential.fields'

    def _get_fields_selection(self):
        '''
        Este metodo va obtener los campos que se puedan seleccionar para agregar a la credencial
        '''
        self.env
        # print (self.env['hr.employee'].fields_get())
        fields = self.env['hr.employee'].fields_get()
        print (fields)
        list_selection = []
        for field_name in fields.keys():
            if fields[field_name]['type'] == 'many2one':
                submodel = fields[field_name]['relation']
                subfields = self.env[submodel].fields_get()
                for subfield in subfields.keys():
                    key = '%s.%s' % (field_name,subfield)
                    value = '%s > %s' % (fields[field_name]['string'],subfields[subfield]['string'])
                    list_selection.append((key,value))
            else:
                key = '%s' % (field_name)
                value = '%s' % (fields[field_name]['string'])
                list_selection.append((key, value))

        # print (list_relational_fields)
        print ('jdnsjdjsndjnsdnjn')
        print ('jdnsjdjsndjnsdnjn')
        print ('jdnsjdjsndjnsdnjn')
        # print (self.env['hr.employee'].fields_get().filter(lambda field: field['type'] == 'many2one'))
        # print (self.env['hr.employee']._fields.items())
        # print (self.env['hr.employee']._fields.items())
        return list_selection

    # def _get_field_id(self):

    @api.one
    @api.depends('field_selection')
    def _get_field_type(self):
        '''
        Este metodo obtiene el tipo de campo
        '''
        model = self.env['hr.employee']
        if self.field_selection:
            if len(self.field_selection.split('.')) > 1:
                field = self.field_selection.split('.')[0]
                subfield = self.field_selection.split('.')[1]
                submodel = self.env[model.fields_get(field)[field]['relation']]
                subfield = submodel.fields_get(subfield)[subfield]
                self.field_type = subfield['type']
            else:
                print(model.fields_get(self.field_selection))
                print(model.fields_get(self.field_selection))
                print(model.fields_get(self.field_selection))
                self.field_type = model.fields_get(self.field_selection)[self.field_selection]['type']
            if self.field_selection.split('.')[-1] == 'barcode':
                self.field_type = 'binary'

    #Columns
    field_id = fields.Many2one(comodel_name='ir.model.fields', string='Campos a agregar')
    sheet = fields.Selection([('front', 'Frontal'),('reverse', 'Reverso')], string='Añadir a:', required=True, default='front')
    field_type = fields.Char(string='Tipo de campo', compute='_get_field_type')
    field_selection = fields.Selection(_get_fields_selection, string='Campos')
    # submodel = fields.
    subfile_id = fields.Many2one(comodel_name='ir.model.fields', string='Sub-Campos a agregar', required=False)
    position_x = fields.Selection([
        (1,'1'),
        (2,'2'),
        (3,'3')],string='Posicion (Horizontal)', default=1, required=True)
    position_y = fields.Selection([
        (1,'1'),
        (2,'2'),
        (3,'3')],string='Posicion (Vertical)', default=1, required=True)
    image_size = fields.Selection([
                        ('25%','Pequeña'),
                        ('50%','Mediana'),
                        ('75%','Grande'),
                        ], string = 'Tamaño de imagen')
    align = fields.Selection([
                        (0,'Izquierda'),
                        (50,'Centro'),
                        (75,'Derecha'),
                        ], string = 'Alineación', required=True)
    vertical_align = fields.Selection([
                        (0,'Top'),
                        (20,'Middle-Top'),
                        (40,'Middle'),
                        (60,'Middle-Bottom'),
                        (80,'Bottom'),
                        ], string = 'Alineación', required=True)
    font_type = fields.Selection([
                    ('h1','H1'),
                    ('h2','H2'),
                    ('h3','H3'),
                    ('h4','H4'),
                    ('h5','H5'),
                    ('h6','H6'),
                    ('h7','H7'),
                    ], string='Tipo de texto')
    # ttype = fields.Char(related = 'field_id.ttype')
    template_id = fields.Many2one(comodel_name='credential.template', string='Plantilla')
    node_id = fields.Char(string='ID node')
    node_tag = fields.Char(string='Node Tag')

    def _get_left_image_size_value(self):
        '''

        '''
        image_size = int(self.image_size.replace('%',''))
        sizes = getattr(self.template_id, self.template_id.orientation)[self.template_id.size]
        image_size_pt = sizes['width']*float(image_size/100)
        print (image_size_pt)
        print (image_size_pt)
        print (image_size_pt)
        rest = sizes['width'] - image_size_pt
        left = rest * float(self.align / 100)
        return left


    def _get_snippet_binary(self, element):
        '''
        Este metodo arma y retorna el fragmento de codigo correspondiente para tipo de campo que se esta enviando
        '''
        sizes = getattr(self.template_id, self.template_id.orientation)[self.template_id.size]
        top = sizes['height']*float(self.vertical_align/100)
        left = self._get_left_image_size_value()
        img = element.xpath('//%s[@oe_data_id="%s"]' % (self.node_tag,self.node_id))
        if len(img):
            for node in img:
                node.getparent().remove(node)
                snippet = node
                snippet.set('style', "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size,left,top))
        else:
            snippet = IMG()
            snippet.set('style', "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size,left,top))
            snippet.set('data', "${object.%s}" % (self.field_selection))
            snippet.set('src', "/payroll_mexico/static/img/%s_default.png"  % self.field_selection.split('.')[-1])
            snippet.set('onerror', "this.onerror=null; this.src='/payroll_mexico/static/img/%s_default.png';" % self.field_selection.split('.')[-1])
            snippet.set('alt', "Company Logo")
            snippet.set('oe_data_id', '%s' % self.id)
            self.node_id = str(self.id)
        for node in element.xpath('//tr/td'):
            node.append(snippet)
            self.node_tag=snippet.tag


        return element

    def _get_snippet_html(self, element):
        '''


        '''
        sizes = getattr(self.template_id, self.template_id.orientation)[self.template_id.size]
        top = sizes['height'] * float(self.vertical_align / 100)
        left = self._get_left_image_size_value()
        nodes = element.xpath('//%s[@oe_data_id="%s"]' % (self.node_tag, self.node_id))
        if len(nodes):
            for node in nodes:
                node.getparent().remove(node)
                snippet = node
                snippet.set('style',
                            "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size, left, top))
        else:
            snippet = DIV(
                '${object.%s}' % self.field_selection
            )
            snippet.set('oe_data_id', '%s' % self.id)
            snippet.set('style', "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size, left, top))
            self.node_id = str(self.id)
        for node in element.xpath('//tr/td'):
            node.append(snippet)
            self.node_tag = snippet.tag
        return element


    def _get_snippet_char(self, element):
        '''


        '''
        sizes = getattr(self.template_id, self.template_id.orientation)[self.template_id.size]
        top = sizes['height'] * float(self.vertical_align / 100)
        left = sizes['width'] * float((self.align/2) / 100)
        font=self.font_type
        nodes = element.xpath('//%s[@oe_data_id="%s"]' % (font, self.node_id))
        if len(nodes):
            for node in nodes:
                node.getparent().remove(node)
                snippet = node
                snippet.set('style',
                            "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size, left, top))
        else:
            font_element = getattr(html.builder, font.upper())
            snippet = font_element(
                '${object.%s}' % self.field_selection
            )
            snippet.set('oe_data_id', '%s' % self.id)
            snippet.set('style', "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size,left,top))
            self.node_id = str(self.id)
        for node in element.xpath('//tr/td'):
            node.append(snippet)
            self.node_tag = snippet.tag
        return element

    def _get_snippet_integer(self, element):
        '''

        '''
        return self._get_snippet_char(element)

    def _get_snippet_selection(self, element):
        '''

        '''
        return self._get_snippet_char(element)

    def _get_snippet_barcode(self, element):
        '''

        '''
        sizes = getattr(self.template_id, self.template_id.orientation)[self.template_id.size]
        top = sizes['height'] * float(self.vertical_align / 100)
        left = self._get_left_image_size_value()
        img = element.xpath('//%s[@oe_data_id="%s"]' % (self.node_tag, self.node_id))
        if len(img):
            for node in img:
                node.getparent().remove(node)
                snippet = node
                snippet.set('style',
                            "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size, left, top))
        else:
            snippet = IMG()
            snippet.set('style', "width:{};position:absolute; left: {}pt; top: {}pt".format(self.image_size, left, top))
            snippet.set('src', "'/report/barcode/?type=Code128&amp;value=${%s}&amp;width=600&amp;height=120'" % (self.field_selection))
            snippet.set('onerror', "this.onerror=null; this.src='/payroll_mexico/static/img/%s_default.png';" %
                        self.field_selection.split('.')[-1])
            snippet.set('alt', "Signature")
            snippet.set('oe_data_id', '%s' % self.id)
            self.node_id = str(self.id)
        for node in element.xpath('//tr/td'):
            node.append(snippet)
            self.node_tag = snippet.tag
        return element




    def unlink_element(self):
        '''

        '''
        element = etree.HTML(self.template_id.body_html if self.sheet == 'front' else self.template_id.back_html)
        nodes = element.xpath('//%s[@oe_data_id="%s"]' % (self.node_tag, self.node_id))
        for node in nodes:
            node.getparent().remove(node)
        element_html = html.tostring(element, pretty_print=True, method='xml', encoding='unicode')
        if self.sheet == 'front':
            self.template_id.body_html = str(element_html)
        else:
            self.template_id.back_html = str(element_html)
        return self.unlink()
