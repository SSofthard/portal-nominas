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
from odoo.addons.portal.controllers.portal import CustomerPortal,pager as portal_pager
from odoo.addons.portal.controllers.web import Home

logger = logging.getLogger(__name__)

# Completely arbitrary limits
MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT = IMAGE_LIMITS = (1024, 768)
LOC_PER_SITEMAP = 45000
SITEMAP_CACHE_TIME = datetime.timedelta(hours=12)


class PayslipsSign(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(PayslipsSign, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        sign_request = request.env['sign.request']
        sign_request_count = request.env['sign.request.item'].sudo().search_count([('partner_id', '=',partner.id)])


        values.update({
            'sign_request': sign_request_count,
        })
        print ('lksnlasnkansaknslknaslkasnlk')
        print ('lksnlasnkansaknslknaslkasnlk')
        print ('lksnlasnkansaknslknaslkasnlk')
        print ('lksnlasnkansaknslknaslkasnlk')
        print ('lksnlasnkansaknslknaslkasnlk')
        print ('lksnlasnkansaknslknaslkasnlk')
        print ('lksnlasnkansaknslknaslkasnlk')
        print (values)
        return values

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
        print (self._items_per_page)
        print (self._items_per_page)
        print (self._items_per_page)

        searchbar_sortings = {
            'state': {'label': _('Estado'), 'order': 'state'},
            'reference': {'label': _('Reference'), 'order': 'reference'},
            'create_date': {'label': _('Mas reciente'), 'order': 'create_date desc'},
            'res_name': {'label': _('Nombre del recurso'), 'order': 'res_name'},
        }
        if not sortby:
            sortby = 'state'
        sort_order = searchbar_sortings[sortby]['order']
        sign_request_ids = request.env['sign.request.item'].sudo().search([('partner_id', '=', user.partner_id.id)]).mapped('sign_request_id')._ids
        sign_request = request.env['sign.request'].sudo().search([('id', 'in', sign_request_ids)], order=sort_order,
                                                                 limit=self._items_per_page,
                                                                 offset=(page - 1) * self._items_per_page)
        sign_request_count = request.env['sign.request.item'].sudo().search_count([('partner_id', '=', user.partner_id.id)])
        pager = portal_pager(
            url="/my/payslips",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=sign_request_count,
            page=page,
            step=self._items_per_page
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