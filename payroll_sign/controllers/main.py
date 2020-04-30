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
from odoo.tools import pycompat, OrderedSet
from odoo.addons.http_routing.models.ir_http import slug, _guess_mimetype
from odoo.addons.web.controllers.main import Binary
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.portal.controllers.web import Home

logger = logging.getLogger(__name__)

# Completely arbitrary limits
MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT = IMAGE_LIMITS = (1024, 768)
LOC_PER_SITEMAP = 45000
SITEMAP_CACHE_TIME = datetime.timedelta(hours=12)


class PayslipsSign(http.Controller):

    @http.route('/mypayslips', type='http', auth="public", website=True)
    def main(self):
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        user = request.env['res.users'].browse(request.uid)
        sign_request = request.env['sign.request.item'].search([('partner_id', '=',user.partner_id.id)]).mapped('sign_request_id')
        return request.render('payroll_sign.payslip_receipt', {'sign_request':sign_request})
