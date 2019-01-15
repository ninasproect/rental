# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'



    start_date      =   fields.Datetime(string='date début de location', required=False,states={'draft': [('readonly', False)]})
    end_date        =   fields.Datetime(string='date fin de location', required=False, states={'draft': [('readonly', False)]})
    rental_id       =   fields.Many2one('rental.order',string='Location')
    invoice_type    =   fields.Selection(string="Facture d'une", selection=[('sale', 'Vente'), ('rental', 'location'), ],default='sale', required=True)