# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import datetime
import json
import os
import logging
import requests
import werkzeug.utils
import werkzeug.wrappers

from itertools import islice
from xml.etree import ElementTree as ET

import odoo

from odoo import http, models, fields, _
from odoo.http import request


class Timbrado(http.Controller):

   @http.route('/cfdiImpresion/<int:withholding>', type='http', auth="public", website=True, multilang=False)
    def print_report_inslr(self,withholding,**kwargs):
        withholding_obj = request.env['account.wh.islr']
        withholding = withholding_obj.search([('id','=',int(withholding))])
        arbol=withholding_obj.generate_file_xml(withholding)
        f = StringIO.StringIO()
        arbol.write(f, encoding="ISO-8859-1", xml_declaration=True)
        f.seek(0)
        file=f.read()
        xlshttpheaders = [('Content-Type', 'application/xml'), ('Content-Length', len(file))]
        response=request.make_response(file, headers=xlshttpheaders)
        response.headers.add('Content-Disposition', 'attachment; filename=Pago_ISLR.xml;')
        return response

  
