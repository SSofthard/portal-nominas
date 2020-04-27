# -*- coding: utf-8 -*-

import babel
import pytz
import base64
import qrcode
import logging
import zeep

from pytz import timezone
from datetime import date, datetime, time, timedelta
from dateutil import relativedelta as rdelta
from io import StringIO, BytesIO
from lxml import etree as ET

from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.addons.payroll_mexico.cfdilib_payroll import cfdilib, cfdv32, cfdv33

from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    #Columns
    pdf_signed = fields.Boolean(string='Document Signed')
    sign_status = fields.Selection(related='sign_request_id.state')
    sign_request_id = fields.Many2one(string='Solicitud de firmado')


    def send_pdf_to_sign(self):
        '''
        Este metodo realiza los procesos correspondientes para la solicitud de firma de recibo de nómina
        :return:
        '''
        sign_request_obj = self.env['sign.request']
        sign_send_request_obj = self.env['sign.send.request']
        sign_template_obj = self.env['sign.template']
        sign_template = sign_template_obj.create({
            'name':self.pdf.name,
            'folder_id':self.pdf.folder_id.id,
            'document_tag_ids':self.pdf.tag_ids._ids,
            'attachment_id':self.pdf.id,
            'sign_item_ids': [(0, False,{
                'name':'Firma',
                'type_id':self.env['sign.item.type'].search([('type','=','signature')]).id,
                'responsible_id': self.env['sign.item.role'].search([('name','=','Empleado')]).id,
                'page': 1,
                'posX': 0.757,
                'posY': 0.414,
                'width': 0.171,
                'height': 0.040,
                                         })],
        })
        print (self.env['sign.item.role'].search([('name', '=', 'Empleado')]).id)
        print (self.env['sign.item.role'].search([('name', '=', 'Empleado')]).id)
        sign_send_request = sign_send_request_obj.create({
            'template_id': sign_template.id,
            'filename': sign_template.name,
            'signer_ids':[(0, False,{
                'role_id':self.env['sign.item.role'].search([('name','=','Empleado')]).id,
                'partner_id':self.employee_id.address_home_id.id,
            })],
            'signers_count':1,
            'signer_id': self.employee_id.address_home_id.id,
            'subject':_("Signature Request - %s") % (sign_template.attachment_id.name)
        })
        return sign_send_request.create_request()

