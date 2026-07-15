from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class CustomHomepage(Website):

    @http.route('/', type='http', auth='public', website=True)
    def index(self, **kw):
        return request.render('custom_homepage.homepage_page')

    # Product swiper controller now lives in theme_apple_shop (shared — see
    # /theme_apple_shop/snippet/product_swiper), which this module depends on.
