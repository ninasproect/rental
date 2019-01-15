# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.addons import decimal_precision as dp
import datetime
import math
import logging
_logger = logging.getLogger(__name__)

class RentalOrderLine(models.Model):
    _name = 'rental.order.line'
    _description = 'Rental Order Line'
    _order = 'rental_id, sequence, id'


    rental_id           = fields.Many2one('rental.order', string="Référence de la location", required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    name                = fields.Text(string='Description', required=True)
    sequence            = fields.Integer(string='Séquence', default=10)
    price_unit          = fields.Float('Prix ​​unitaire', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    price_subtotal      = fields.Monetary(compute='_compute_amount', string='Sous-total', readonly=True, store=True)
    tax_ids             = fields.Many2many('account.tax', string='Taxes',domain=['|', ('active', '=', False), ('active', '=', True)])
    price_tax           = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    discount            = fields.Float(string='Remise(%)', digits=dp.get_precision('Product Price'), default=0.0)
    price_total         = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    price_unit_period   = fields.Monetary(compute='_compute_amount', string='Prix ​​unitaire / Période', readonly=True, store=True)
    product_uom         = fields.Many2one('uom.uom', string='Unité de mesure')
    product_id          = fields.Many2one('product.product', string='Article', domain=[('rental_ok', '=', True)], change_default=True, ondelete='restrict')
    product_uom_qty     = fields.Float(string='Quantité commandée', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_image       = fields.Binary('Image du produit', related="product_id.image", store=False, readonly=False)
    salesman_id         = fields.Many2one(related='rental_id.user_id', store=True, string='Vendeur', readonly=True)
    currency_id         = fields.Many2one(related='rental_id.currency_id', depends=['rental_id'], store=True, string='Devise', readonly=True)
    company_id          = fields.Many2one(related='rental_id.company_id', string='Entreprise', store=True, readonly=True)
    order_partner_id    = fields.Many2one(related='rental_id.partner_id', store=True, string='Client', readonly=False)
    state               = fields.Selection([
        ('draft', 'Réservation'),
        ('sent', 'Réservation envoyé'),
        ('rent', 'Location'),
        ('cancel', 'Annulé'),
    ], related='rental_id.state', string='Statut de location', readonly=True, copy=False, store=True, default='draft')



    @api.depends('product_id','rental_id.start_date','rental_id.end_date','product_uom_qty','discount','price_unit','tax_ids')
    def _compute_amount(self):
        delta   =   1
        for line in self:
            if line.rental_id.end_date != False and line.rental_id.start_date :
                if line.product_id.rental_unit=="occasion":
                    amount =  line.product_id.rental_unit * line.product_uom_qty
                if line.product_id.rental_unit=="hour":
                    delta      =   (line.rental_id.end_date - line.rental_id.start_date).total_seconds()/60/60
                if line.product_id.rental_unit=="day":
                    delta  =   (line.rental_id.end_date - line.rental_id.start_date).total_seconds()/60/60/24
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)*delta
            taxes = line.tax_ids.compute_all(price, line.rental_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.rental_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal':line.price_unit * line.product_uom_qty * delta,
                'price_unit_period':line.price_unit * delta,
            })


    @api.onchange('product_id')
    def product_id_change(self):
        self.name = self.product_id.description_sale or self.product_id.name
        self.price_unit = self.product_id.rental_price
        self.product_uom = self.product_id.uom_id.id







