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

    items_per_page = 20

    @http.route(['/my/payslips', '/my/payslips/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payslips(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = {}
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        print ('dskdjsodnsldjnsdkjnsdkjsndkjsdn')
        user = request.env['res.users'].browse(request.uid)
        sign_request = request.env['sign.request.item'].sudo().search([('partner_id', '=',user.partner_id.id)]).mapped('sign_request_id')
        sign_request_count = request.env['sign.request.item'].sudo().search_count([('partner_id', '=',user.partner_id.id)])
        searchbar_sortings = {
            'stage': {'label': _('Stage'), 'order': 'state'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'stage'
        sort_order = searchbar_sortings[sortby]['order']
        pager = portal_pager(
            url="/my/payslips",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=sign_request_count,
            page=page,
            step=self.items_per_page
        )
        values.update({
            'date': date_begin,
            'sign_request': sign_request,
            'page_name': 'payslips',
            'pager': pager,
            # 'archive_groups': archive_groups,
            'default_url': '/my/payslips',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        print (searchbar_sortings)
        print (searchbar_sortings)
        print (searchbar_sortings[sortby].get('label', 'Newest'))
        return request.render('payroll_sign.payslip_receipt', values)

    @http.route('/signdoc/<request_id>/', type='http', auth="portal", website=True)
    def sign(self, request_id):
        print (request_id)
        print (request_id)
        print (request_id)
        return request.env['sign.request'].browse(request_id).sudo().go_to_document()