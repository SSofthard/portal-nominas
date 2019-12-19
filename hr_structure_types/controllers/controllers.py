# -*- coding: utf-8 -*-
from odoo import http

# class AddonsMexico/hrStructureTypes(http.Controller):
#     @http.route('/addons_mexico/hr_structure_types/addons_mexico/hr_structure_types/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/addons_mexico/hr_structure_types/addons_mexico/hr_structure_types/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('addons_mexico/hr_structure_types.listing', {
#             'root': '/addons_mexico/hr_structure_types/addons_mexico/hr_structure_types',
#             'objects': http.request.env['addons_mexico/hr_structure_types.addons_mexico/hr_structure_types'].search([]),
#         })

#     @http.route('/addons_mexico/hr_structure_types/addons_mexico/hr_structure_types/objects/<model("addons_mexico/hr_structure_types.addons_mexico/hr_structure_types"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('addons_mexico/hr_structure_types.object', {
#             'object': obj
#         })