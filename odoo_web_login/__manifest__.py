# -*- encoding: utf-8 -*-
##############################################################################
#
#    Samples module for Odoo Web Login Screen
#    Copyright (C) 2018- XUBI.ME (http://www.xubi.me)
#    @author binhnguyenxuan (https://www.linkedin.com/in/binhnguyenxuan)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    
#    Background Source: http://forum.xda-developers.com/showpost.php?p=37322378
#
##############################################################################
{
    'name': 'Odoo Web Login Screen',
    'summary': 'The new configurable Odoo Web Login Screen',
    'version': '12.0.1.0',
    'category': 'Website',
    'summary': """
The new configurable Odoo Web Login Screen
""",
    'author': "Soluciones Softhard",
    'website': 'http://www.solucionesofthard.com',
    'license': 'AGPL-3',
    'depends': [
        'web',
        'web_enterprise',
        'social_media',
    ],
    'data': [
        'templates/assets.xml',
        'view/res_company_view.xml',
    ],
    'qweb': [
        'templates/base_enterprise.xml',
    ],
    'installable': True,
    'application': True,
}
