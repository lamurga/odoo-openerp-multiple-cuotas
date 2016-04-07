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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from datetime import datetime as dt
from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from openerp.tools.translate import _


class Sale_Order_Line_Cuota(models.Model):
    _name = 'sale.order.line.cuota'

    @api.depends('sale_id')
    def _get_compute_state(self):
        for rec in self:
            rec.state = rec.sale_id.state

    CHOICE_STATE = [('active', 'Activo'), ('cancel', 'Cancelado'), ('annul', 'Anulado')]

    monto_cuota = fields.Float(u"Monto SIN IGV",
                               digits_compute=dp.get_precision('Product Price'),
                               required=True)
    fecha_vencimiento = fields.Date(u"Fecha de vencimiento",
                                    required=True)
    fecha_creacion = fields.Date(u"Fecha de emisión",
                                 required=True)
    mes_creacion = fields.Char(compute='_get_date', store=True)
    nro_cuota = fields.Integer(u"Num Cuota",
                               readonly=True)

    sale_id = fields.Many2one("sale.order",
                              ondelete='cascade',
                              string="Lista Presupuesto")
    order_line_id = fields.Many2one("sale.order.line",
                                    ondelete='cascade',
                                    string=u"Presupuesto")
    invoice_id = fields.Many2one("account.invoice",
                                 ondelete='restrict',
                                 required=False,
                                 string=u"Factura")
    state = fields.Char(compute="_get_compute_state", store=True)
    description = fields.Char(u"Descripción",
                              required=True)
    status = fields.Selection(CHOICE_STATE, u'Estado',
                              readonly=False,
                              default='active')

    @api.depends('fecha_creacion')
    def _get_date(self):
        for rec in self:
            if rec.fecha_creacion:
                rec.mes_creacion = dt.strptime(rec.fecha_creacion, '%Y-%m-%d').strftime('%Y-%m')

    @api.onchange('status', 'invoice_id')
    def _onchange_status(self):
        if self.invoice_id:
            if self.status == 'cancel' and self.invoice_id.state != 'cancel':
                raise except_orm(
                  _('Configuration Error!'),
                  _("Lo sentimos, primero debe de cancelar la factura.")
                  )
            elif self.status == 'annul' and self.invoice_id.state != 'annul':
                raise except_orm(
                  _('Configuration Error!'),
                  _("Lo sentimos, primero debe de anular la factura.")
                  )


class account_invoice(models.Model):
    _inherit = "account.invoice"

    cuota_id = fields.Many2one("sale.order.line.cuota",
                               required=False,
                               string="Cuota")