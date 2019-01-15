# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)


class RentalOrder(models.Model):
    _name = 'rental.order'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Réservation"
    _order = 'date_order desc, id desc'

    name        = fields.Char(string='Référence', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state       = fields.Selection([
        ('draft', 'Réservation'),
        ('sent', 'Réservation envoyé'),
        ('rent', 'Location'),
        ('cancel', 'Annulé'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    start_date        =   fields.Datetime(string='date début de location',required=True,states={'draft': [('readonly', False)]})
    end_date          =   fields.Datetime(string='date fin de location',required=True, states={'draft': [('readonly', False)]})
    date_order        = fields.Datetime(string='Date de commande', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    create_date       = fields.Datetime(string='Date de création', readonly=True, index=True, help="Date à laquelle la commande client est créée.")
    confirmation_date = fields.Datetime(string='Date de confirmation', readonly=True, index=True, help="Date à laquelle la commande client est confirmée.", oldname="date_confirm", copy=False)
    user_id           = fields.Many2one('res.users', string='Vendeur', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    partner_id        = fields.Many2one('res.partner', string='Client', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always', track_sequence=1)
    company_id        = fields.Many2one('res.company', 'Entreprise', default=lambda self: self.env['res.company']._company_default_get('rental.order'))
    currency_id       = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", readonly=True, required=True)
    rental_line       = fields.One2many('rental.order.line', 'rental_id', string='ligne de location', states={'cancel': [('readonly', True)], 'rent': [('readonly', True)]}, copy=True, auto_join=True)
    note              = fields.Text('Termes et conditions',)
    pricelist_id      = fields.Many2one('product.pricelist', string='Pricelist', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_untaxed    = fields.Monetary(string='Montant HT', store=True, readonly=True, compute='_amount_all', track_visibility='onchange', track_sequence=5)
    amount_tax        = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total      = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always', track_sequence=6)
    invoice_ids       = fields.Many2many("account.invoice", string='Factures', readonly=True,copy=False)
    invoice_count     = fields.Integer('Factures', compute='compute_invoice_count')
    invoice_state     = fields.Selection([('draft', 'Réservation'),
        ('invoiced', 'Facturé'),
        ('to_be_invoice', 'Â Facturer'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3)
    picking_ids = fields.One2many(comodel_name='stock.picking', inverse_name='rental_id', string='Pickings')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')

    @api.multi
    def action_view_delivery(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for rental in self:
            rental.delivery_count = len(rental.picking_ids)

    @api.one
    @api.depends('invoice_ids')
    def compute_invoice_count(self):
        self.invoice_count = len(self.invoice_ids.ids)

    @api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('rental.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.order') or _('New')
        result = super(RentalOrder, self).create(vals)
        return result

    @api.multi
    def action_confirm(self):
        self.write({'state':'rent','invoice_state':'to_be_invoice'})
        self.create_picking()


    @api.multi
    def button_dummy(self):
        self.get_amount_all()

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            return
        self.update({
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'user_id': self.partner_id.user_id.id or self.env.uid
        })

    @api.multi
    def get_amount_all(self):
        for rental in self:
            amount_untaxed = amount_tax = 0.0
            for line in rental.rental_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                _logger.warning('\n ok ok amount_untaxed=>>%s', amount_untaxed)
            rental.update({
                'amount_untaxed': rental.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': rental.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('rental_line.price_tax','rental_line.price_total','rental_line.price_subtotal','rental_line.price_unit_period')
    def _amount_all(self):
        self.get_amount_all()




    def create_invoice(self):
        inv_obj = self.env['account.invoice']
        lines =[]
        for line in self.rental_line:
            lines.append((0, 0, {
                'name': line.name,
                'origin': self.name,
                'account_id': 1,
                'price_unit': line.price_unit_period,
                'sale_rental_price_unit': line.price_unit,
                'price_unit_period':line.price_unit_period ,
                'quantity': line.product_uom_qty,
                'discount': line.discount,
                'uom_id': line.product_uom.id,
                'product_id': line.product_id.id,
                'invoice_line_tax_ids': [(6, 0, line.tax_ids.ids)],
            }))


        invoice = inv_obj.create({
            'name': self.name,
            'origin': self.name,
            'type': 'out_invoice',
            'invoice_type': 'rental',
            'start_date':self.start_date,
            'end_date':self.end_date,
            'reference': False,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'invoice_line_ids': lines,
            'currency_id': self.pricelist_id.currency_id.id,
            'user_id': self.user_id.id,
            'comment': self.note,
        })
        self.invoice_ids =[invoice.id]
        self.invoice_state ='invoiced'


    def get_locations(self,type):
        picking_type = self.env['stock.picking.type'].search([('code', '=', type)])
        _logger.warning('\n ok ok picking_type=>%s',picking_type)
        location_dest_id = False
        location_id = False
        if len(picking_type) > 0:
            picking_type = picking_type[0]

        if picking_type:
            if picking_type.default_location_src_id:
                location_id = picking_type.default_location_src_id.id
            elif self.partner_id:
                location_id = self.partner_id.property_stock_supplier.id
            else:
                customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
            if picking_type.default_location_dest_id:
                location_dest_id = picking_type.default_location_dest_id.id
            elif self.partner_id:
                location_dest_id = self.partner_id.property_stock_customer.id
            else:
                location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()

        return {'picking_type':picking_type,'location_id':location_id,'location_dest_id':location_dest_id}

    def create_picking(self):
        self.picking_ids = [self.create_outgoing_picking().id,self.create_incoming_picking().id]

    def create_outgoing_picking(self):
        picking_obj = self.env['stock.picking']
        locations_out = self.get_locations('outgoing')
        lines =[]
        for line in self.rental_line:
            lines.append((0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'location_id': locations_out['location_id'],
                'location_dest_id': locations_out['location_dest_id'],

            }))
        picking_out = picking_obj.create({
            'origin': self.name,
            'picking_type_code':'outgoing',
            'picking_type_id': locations_out['picking_type'].id,
            'location_id': locations_out['location_id'],
            'location_dest_id' : locations_out['location_dest_id'],
            'scheduled_date':self.start_date,
            'partner_id': self.partner_id.id,
            'move_ids_without_package': lines,
        })
        picking_out.action_confirm()
        return picking_out

    def create_incoming_picking(self):
        picking_obj = self.env['stock.picking']
        locations_in = self.get_locations('incoming')
        lines = []
        for line in self.rental_line:
            lines.append((0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                'location_id': locations_in['location_id'],
                'location_dest_id': locations_in['location_dest_id'],
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
            }))

        picking_in = picking_obj.create({
            'origin': self.name,
            'picking_type_code': 'incoming',
            'picking_type_id': locations_in['picking_type'].id,
            'location_id': locations_in['location_id'],
            'location_dest_id': locations_in['location_dest_id'],
            'scheduled_date': self.end_date,
            'partner_id': self.partner_id.id,
            'move_ids_without_package': lines,
        })
        picking_in.action_confirm()
        return  picking_in

