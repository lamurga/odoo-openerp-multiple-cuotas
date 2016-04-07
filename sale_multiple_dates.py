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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from dateutil import relativedelta
from datetime import datetime
from datetime import timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class sale_order_dates(models.TransientModel):
    _name = "sale.order.dates"

    CHOICE_STATE = [('active', 'Activo'), ('canceled', 'Cancelado'), ('annulled', 'Anulado')]

    se_repite = fields.Selection([('monthly', 'Cada mes'), ('yearly', 'Cada año')], "Se repite",
                                 help="Elija una frecuencia de pago", required=True, default='monthly')
    repetir_cada = fields.Selection([('1', '1'),
                                     ('2', '2'),
                                     ('3', '3'),
                                     ('4', '4'),
                                     ('5', '5'),
                                     ('6', '6'),
                                     ('7', '7'),
                                     ('8', '8'),
                                     ('9', '9'),
                                     ('10', '10'),
                                     ('11', '11'),
                                     ('12', '12')], "Repetir Cada", help="Elegir cada cuando tiempo se repetirá",
                                    required=True, default='1')
    empieza = fields.Date("Empieza", required=True, default=fields.Date.today)
    finaliza = fields.Char("Finaliza despues de", required=True, default="6")

    @api.multi
    def crear(self):
        # cuotas = self.env['cuota'].browse(self._context.get('active_ids'))
        sale = self.env['sale.order.line'].browse(self._context.get('active_ids'))

        date_start = datetime.strptime(self.empieza, DEFAULT_SERVER_DATE_FORMAT)
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        n_cuota = 0
        c_monto = 0.0
        if date_start >= today:
            if self.se_repite == "monthly":
                list_created = []
                customer_name = None
                for i in range(0, int(self.finaliza)):
                    n_cuota += 1
                    cuotas = self.env['sale.order.line.cuota'].browse(self._context.get('active_ids'))
                    empieza = datetime.strptime(self.empieza, DEFAULT_SERVER_DATE_FORMAT)
                    fecha = (empieza + relativedelta.relativedelta(months=int(self.repetir_cada) * i)).strftime(
                        DEFAULT_SERVER_DATE_FORMAT)
                    fecha_v = datetime.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
                    monto_cuota = round(sale.price_unit / (float(self.finaliza)), 2)
                    cuotas.create({
                        'monto_cuota': (monto_cuota) if n_cuota != int(self.finaliza) else round(sale.price_unit,
                                                                                                 2) - c_monto,
                        'fecha_vencimiento': (fecha_v + relativedelta.relativedelta(
                            days=int(sale.order_id.partner_id.property_payment_term.line_ids.days))).strftime(
                            DEFAULT_SERVER_DATE_FORMAT),
                        'fecha_creacion': fecha,
                        'nro_cuota': (i + 1),
                        'description': sale.name + ". Cuota " + str(n_cuota) + " de " + str(self.finaliza),
                        'sale_id': sale.order_id.id,
                        'order_line_id': sale.id
                    })
                    c_monto += monto_cuota
                    date_cuota = (empieza + relativedelta.relativedelta(months=int(self.repetir_cada) * i)).strftime(
                            "%Y-%m")
                    customer_id = sale.order_id.partner_id.id
                    if customer_name is None:
                        customer_name = sale.order_id.partner_id.name
                    count_cuota = self.env['sale.order.line.cuota'].search_count([('mes_creacion', '=', date_cuota),
                                                                                 ('sale_id.partner_id.id', '=',
                                                                                 customer_id)])
                    count_cuota = count_cuota -1
                    if count_cuota > 0:
                        month = self.env['ir.translation'].date_part(fecha, 'month', format='char', lang='pe')
                        to_warning = month + ' (' + str(count_cuota) + ')'
                        list_created.append(to_warning)

                if list_created:
                    msg = 'El cliente %s ya tiene cuotas en el mes: %s' % (customer_name, list_created)
                    return self.action_popup(msg)
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'reload',
                    }
            else:
                for i in range(0, int(self.finaliza)):
                    empieza = datetime.strptime(self.empieza, DEFAULT_SERVER_DATE_FORMAT)
                    print "%s" % (empieza + relativedelta.relativedelta(years=int(self.repetir_cada) * i)).strftime(
                        DEFAULT_SERVER_DATE_FORMAT)
        else:
            raise Warning(_('La fecha de inicio debe ser mayor igual a la fecha actual!'))

    @api.multi
    def refresh(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_popup(self, msg):
         return {
            'type': 'ir.actions.client',
            'tag': 'action_warn',
            'name': _('Adevertencia'),
            'params': {
                'title': _('Datos guardados con éxito, pero ya existen cuotas!'),
                'text': _(msg),
                'sticky': True
            }
         }
