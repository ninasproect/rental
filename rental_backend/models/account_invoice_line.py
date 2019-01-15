# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'




    sale_rental_price_unit   =  fields.Monetary(string='Prix ​​unitaire', digits=dp.get_precision('Product Price'))
    price_unit_period        =  fields.Float(related="price_unit" ,string='Prix ​​unitaire / Période', digits=dp.get_precision('Product Price'))

    @api.onchange('sale_rental_price_unit')
    def _onchange_sale_rental_price_unit(self):
        self.price_unit = self.sale_rental_price_unit * self.get_delta()

    @api.one
    @api.depends('price_unit_period')
    def _compute_price_unit_period(self):
        self.price_unit_period = self.sale_rental_price_unit * self.get_delta()



    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        if not self.product_id:
            return res

        if self.invoice_id.invoice_type=='rental':
            if not self.invoice_id.start_date or not self.invoice_id.end_date:
                warning = {
                    'title': _('Warning!'),
                    'message': _("Vous devez d'abord sélectionner une date de début et une date de fin de location"),
                }
                return {'warning': warning}

        return res



    def get_delta(self):
        delta = 1
        if self.invoice_id.invoice_type == "rental":
            if not self.invoice_id.start_date or not self.invoice_id.end_date:
                return 1
            else :
                if self.product_id.rental_unit == "occasion":
                    delta = 1
                if self.product_id.rental_unit == "hour":
                    delta = (self.invoice_id.end_date - self.invoice_id.start_date).total_seconds() / 60 / 60
                if self.product_id.rental_unit == "day":
                    delta = (self.invoice_id.end_date - self.invoice_id.start_date).total_seconds() / 60 / 60 / 24
        return delta

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        warning = {}
        result = {}
        if not self.uom_id:
            self.sale_rental_price_unit = 0.0
        if self.product_id and self.uom_id:
            if self.invoice_id.type in ('in_invoice', 'in_refund'):
                price_unit = self.product_id.standard_price
            else:
                #out_invoice
                if self.invoice_id.invoice_type=='rental':
                    price_unit = self.product_id.rental_price
                else :
                    price_unit = self.product_id.lst_price
            self.sale_rental_price_unit = self.product_id.uom_id._compute_price(price_unit, self.uom_id)
            if self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _('The selected unit of measure has to be in the same category as the product unit of measure.'),
                }
                self.uom_id = self.product_id.uom_id.id
        if warning:
            result['warning'] = warning
        return result