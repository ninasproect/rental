# -*- coding: utf-8 -*-
from odoo import http

# class RentalBackend(http.Controller):
#     @http.route('/rental_backend/rental_backend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rental_backend/rental_backend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('rental_backend.listing', {
#             'root': '/rental_backend/rental_backend',
#             'objects': http.request.env['rental_backend.rental_backend'].search([]),
#         })

#     @http.route('/rental_backend/rental_backend/objects/<model("rental_backend.rental_backend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rental_backend.object', {
#             'object': obj
#         })