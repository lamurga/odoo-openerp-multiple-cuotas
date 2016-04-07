# -*- encoding: utf-8 -*-
######################################################################################
#
#    Odoo/OpenERP, Open Source Management Solution
#    Copyright (c) Jonathan Murga
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
######################################################################################
{
    'name': "Sale Multiple Dues",
    'summary': """
        ...""",

    'description': """
        ...
    """,
    'author': "Jonathan Murga",
    'category': 'Sales & Purchases',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['sale'],
    # always loaded
    'data': [
        'views/sale_order.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
