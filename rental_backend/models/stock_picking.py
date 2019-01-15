# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp

class StockPiking(models.Model):
    _inherit = 'stock.picking'



    rental_id       =   fields.Many2one('rental.order',string='Location')
