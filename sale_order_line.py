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

from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    def _compute_verify_dues(self):
        self.verify_dues = 0.0
        for cuota in self.cuota_ids:
            self.verify_dues += cuota.monto_cuota

    cuota_ids = fields.One2many("sale.order.line.cuota", "order_line_id", string="Cuota")
    verify_dues = fields.Float("Verify Dues", compute='_compute_verify_dues',
                               digits_compute=dp.get_precision('Product Price'))

    @api.multi
    def action_create_cuota(self):
        self.ensure_one()
        return {
            'context': self.env.context,
            'name': 'Crear Cuotas',
            'view_type': 'form',
            'view_mode': 'form',
            'src_model': 'sale.order.line',
            'res_model': 'sale.order.dates',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'id': 'action_crear_cuotas_incuba',
            'key2': 'client_action_multi',
        }


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.one
    def _compute_verify_dues(self):
        self.verify_dues = 0.0
        for cuota in self.cuota_ids:
            self.verify_dues += cuota.monto_cuota

    cuota_ids = fields.One2many("sale.order.line.cuota", "sale_id", string="Cuota")
    verify_dues = fields.Float("Verify Dues", compute='_compute_verify_dues',
                               digits_compute=dp.get_precision('Product Price'))

    @api.multi
    def write(self, values):
        if values.get('state'):
            if self.cuota_ids:
                data_update2 = []
                for obj in self.cuota_ids:
                    data_update2.append([1, obj.id, {'state': values['state']}])
                values.update({'cuota_ids': data_update2})
        else:
            if values.get('cuota_ids'):
                data_update = []
                f = lambda var: [[cuota[1], cuota[2]] for cuota in var if cuota[0] == 1 and cuota[2]]
                var_cuotas = f(values['cuota_ids'])
                for obj in self.cuota_ids:
                    if not obj.invoice_id:
                        data_update = values['cuota_ids']
                        break
                    elif var_cuotas:
                            for val in var_cuotas:
                                if val[0] == obj.id:
                                    list_accept = [1, val[0], val[1]]
                                    if val[1].get('status'):
                                        if val[1]['status'] == 'active' or (
                                                val[1]['status'] == 'cancel' and obj.invoice_id.state == 'cancel') or (
                                                        val[1]['status'] == 'annul' and obj.invoice_id.state == 'annul'):
                                            data_update.append(list_accept)
                                    else:
                                        data_update.append(list_accept)
                values.update({'cuota_ids': data_update})
        res = super(sale_order, self).write(values)
        return res

    def button_refresh(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {}, context=context)

    def crear_cuotas(self, cr, uid, ids, context=None):
        print "crear_cuotas"
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)


class sale_advance_payment_inv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
            [('multiple', 'Hacer varias facturas'), ('all', 'Invoice the whole sales order'),
             ('percentage', 'Percentage'), ('fixed', 'Fixed price (deposit)'),
             ('lines', 'Some order lines')],
            'What do you want to invoice?', required=True,
            help="""Use Invoice the whole sale order to create the final invoice.
                Use Percentage to invoice a percentage of the total amount.
                Use Fixed Price to invoice a specific amound in advance.
                Use Some Order Lines to invoice a selection of the sales order lines.
                Use Multiple Invoices to generate many invoices.""")

    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        sale_obj = self.pool.get('sale.order')
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        invoice_obj = self.pool.get('account.invoice')

        if wizard.advance_payment_method == 'multiple':
            sale = sale_obj.browse(cr, uid, sale_ids, context=context)[0]
            if sale.cuota_ids:
                tax = sale.order_line[0].tax_id.amount
                c_monto = round(sum(c.monto_cuota for c in sale.cuota_ids), 6)
                amount_untaxed = round(sale.amount_untaxed, 6)
                if c_monto != amount_untaxed:
                    raise exceptions.ValidationError(
                            "El monto total del contrato no coincide con al suma de las cuotas")
                nro_cuota = 0
                for cuota in sale.cuota_ids:
                    datos = {
                        'amount_untaxed': cuota.monto_cuota,
                        'date_invoice': cuota.fecha_creacion,
                        'date_due': cuota.fecha_vencimiento,
                        'origin': cuota.sale_id.name,
                        'type': 'out_invoice',
                        'reference': False,
                        'account_id': cuota.sale_id.partner_id.property_account_receivable.id,
                        'partner_id': cuota.sale_id.partner_invoice_id.id,
                        'currency_id': cuota.sale_id.pricelist_id.currency_id.id,
                        'comment': '',
                        'payment_term': cuota.sale_id.payment_term.id,
                        'fiscal_position': cuota.sale_id.fiscal_position.id or cuota.sale_id.partner_id.property_account_position.id,
                        'section_id': cuota.sale_id.section_id.id,
                    }
                    datos = self._prepare_advance_invoice_vals2(cr, uid, ids, datos, context=context)
                    # si es la ultima cuota
                    nro_cuota += 1
                    nro_cuotas = len(sale.cuota_ids)

                    invoice_id = self._create_invoices(cr, uid, datos, sale_ids[0], context=context)
                    invoice_obj.write(cr, uid, invoice_id, datos, context=context)

                    cuota_obj = self.pool.get('sale.order.line.cuota')
                    cuota_obj.write(cr, uid, cuota.id, {'invoice_id': invoice_id}, context=context)

                    monto_cuota = cuota.monto_cuota
                    data_il = {
                        'origin': cuota.sale_id.name,
                        'tax_id': cuota.order_line_id.tax_id.id,
                        'invoice_id': invoice_id,
                        'price_unit': round(float(monto_cuota), 6),
                        'quantity': 1,
                        'more_description': "%s" % cuota.description
                    }
                    sale_order_line_ids = cuota.order_line_id
                    self.generate_invoice_lines(cr, uid, sale_order_line_ids, data_il, context)
                    invoice_obj.button_reset_taxes(cr, uid, invoice_id, context)

                    if nro_cuota == nro_cuotas:
                        sale_obj.write(cr, uid, [sale.id], {'state': 'progress'})
                        if context.get('open_invoices', False):
                            return sale_obj.action_view_invoice(cr, uid, sale_ids, context=context)
                        return {'type': 'ir.actions.act_window_close'}

            else:
                raise exceptions.ValidationError(u"Debe de crear cuotas para esta opción")
            if context.get('open_invoices', False):
                return sale_obj.action_view_invoice(cr, uid, sale_ids, context=context)
            return {'type': 'ir.actions.act_window_close'}

        if wizard.advance_payment_method == 'all':
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)

            if context.get('open_invoices', False):
                return res
            return {'type': 'ir.actions.act_window_close'}

        if wizard.advance_payment_method == 'lines':
            # open the list view of sales order lines to invoice
            res = act_window.for_xml_id(cr, uid, 'sale', 'action_order_line_tree2', context)
            res['context'] = {
                'search_default_uninvoiced': 1,
                'search_default_order_id': sale_ids and sale_ids[0] or False,
            }
            return res
        assert wizard.advance_payment_method in ('fixed', 'percentage')

        inv_ids = []
        for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))

        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def generate_invoice_lines(self, cr, uid, ids, data=None, context=None):
        if context is None:
            context = {}

        invoice_line_obj = self.pool.get('account.invoice.line')
        model = ids
        invoice_line_ids = []
        if data.get('invoice_id'):
            description_invoice = data['more_description'] if data['more_description'] else model.name
            price_unit = data['price_unit']

            invoice_line_id = invoice_line_obj.create(cr, uid, {
                'account_id': model.order_partner_id.property_account_receivable.id,
                'invoice_id': data['invoice_id'],
                'price_unit': price_unit,
                'product_id': model.product_id.id,
                'quantity': data['quantity'],
                'name': description_invoice,
                'origin': data['origin'],
                'invoice_line_tax_id': [(4, data['tax_id'])] if data['tax_id'] else None
            })

            invoice_line_ids.append(invoice_line_id)

        return invoice_line_ids

    def _prepare_advance_invoice_vals2(self, cr, uid, ids, vals=None, context=None):
        return vals
