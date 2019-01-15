# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    rental_ok     = fields.Boolean('Peut être loué', default=False
                                   )
    rental_price  = fields.Monetary('Prix de location', digits=dp.get_precision('Product Price'),default=0)
    rental_unit   = fields.Selection(string="Unité de location", selection=[('occasion ', 'Occasion '),
                                                                            ('hour', 'Heure'),
                                                                            ('day', 'Jour'),
                                                                            ('week', 'Semaine'),
                                                                            ('month', 'Mois'),
                                                           ])





