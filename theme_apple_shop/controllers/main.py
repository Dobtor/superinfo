# -*- coding: utf-8 -*-
"""Mode B: override website_sale routes — never add new ones.

Conditionally branches on Mac category / Mac product:
- /shop/category/<mac>      → Apple-style landing
- /shop/<mac-product>       → Apple-style configurator
- everything else           → super() to Odoo defaults
"""
import json

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class AppleShop(WebsiteSale):

    # ─── helpers ───────────────────────────────────────────────────

    def _is_mac_categ(self, categ):
        if not categ:
            return False
        return bool(categ.exists()) and categ._is_descendant_of_mac_root()

    def _is_mac_product(self, product):
        if not product:
            return False
        return bool(product.exists()) and product.is_mac_product

    # ─── /shop and /shop/category/<categ> ──────────────────────────

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        # /shop/category/<mac_descendant>  → Apple-style landing
        if self._is_mac_categ(category):
            return self._render_mac_landing(category)

        # Plain /shop with no filter and no search → default to Apple Mac
        # landing (this module is a Mac sample shop, so the natural shop
        # entry IS the buy-mac page). Drops through to Odoo defaults if
        # user supplied search/price filters.
        if (not category and not search
                and not min_price and not max_price and not page):
            mac_root = request.env.ref(
                'theme_apple_shop.categ_mac', raise_if_not_found=False
            )
            if mac_root:
                return self._render_mac_landing(mac_root)

        return super().shop(
            page=page, category=category, search=search,
            min_price=min_price, max_price=max_price, ppg=ppg, **post,
        )

    def _render_mac_landing(self, mac_root):
        Categ = request.env['product.public.category']
        models = Categ.search([
            ('parent_id', '=', mac_root.id),
            ('mac_role', '=', 'model'),
        ], order='mac_landing_order, sequence, id')
        return request.render('theme_apple_shop.buy_mac_landing', {
            'mac_root': mac_root,
            'mac_models': models,
            'main_object': mac_root,
        })

    # ─── /shop/<product> ───────────────────────────────────────────

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        if self._is_mac_product(product):
            return self._render_mac_configurator(product, **kwargs)
        return super().product(
            product, category=category, search=search, **kwargs,
        )

    def _render_mac_configurator(self, product, **kwargs):
        attribute_lines = product._get_apple_attribute_groups()
        default_ptavs = product.mac_default_ptav_ids or self._compute_initial_default_ptavs(product)
        exclusion_table = json.dumps(product._get_apple_exclusion_table())
        return request.render('theme_apple_shop.buy_mac_configurator', {
            'product': product,
            'attribute_lines': attribute_lines,
            'default_ptavs': default_ptavs,
            'optional_products': product.optional_product_ids,
            'compare_specs': product.mac_compare_spec_ids.sorted(
                lambda s: (s.sequence, s.id)
            ),
            'exclusion_table': exclusion_table,
            'main_object': product,
        })

    def _compute_initial_default_ptavs(self, product):
        """If admin didn't set mac_default_ptav_ids, pick the cheapest PTAV
        per attribute_line as the initial selection."""
        defaults = request.env['product.template.attribute.value']
        for line in product.attribute_line_ids:
            cheapest = line.product_template_value_ids.sorted(
                lambda v: (v.price_extra, v.product_attribute_value_id.sequence)
            )[:1]
            defaults |= cheapest
        return defaults

    # ─── Mac configurator add-to-cart endpoint ─────────────────────
    # Why a custom endpoint instead of POST /shop/cart/update_json directly?
    # Mac products use create_variant='dynamic' — variants are NOT pre-built;
    # they must be created from a PTAV combination before cart_update_json
    # can accept them. We do that lookup server-side here, then feed the
    # resulting product.product.id into the standard cart endpoint.

    @http.route(
        ['/shop/buy-mac/cart/add'],
        type='json', auth='public', methods=['POST'], website=True,
        csrf=False,
    )
    def mac_add_to_cart(self, product_template_id,
                        product_template_attribute_value_ids=None,
                        optional_product_ids=None, **kwargs):
        Template = request.env['product.template'].sudo()
        tmpl = Template.browse(int(product_template_id)).exists()
        if not tmpl or not self._is_mac_product(tmpl):
            return {'error': 'Invalid Mac product'}

        # Resolve PTAV recordset
        ptav_ids = [int(i) for i in (product_template_attribute_value_ids or [])]
        ptavs = request.env['product.template.attribute.value'].sudo().browse(ptav_ids)

        # Find or dynamically create the variant from the chosen combination
        try:
            variant = tmpl._create_product_variant(ptavs, log_warning=False)
        except Exception as e:
            return {'error': f'Variant creation failed: {e}'}
        if not variant:
            return {'error': 'No matching variant'}

        # Add variant to cart
        order_sudo = request.website.sale_get_order(force_create=True)
        order_sudo._cart_update(
            product_id=variant.id,
            add_qty=1,
            no_variant_attribute_value_ids=ptavs.filtered(
                lambda p: p.attribute_id.create_variant == 'no_variant'
            ).ids,
        )

        # Add each optional product (accessory / software / AppleCare) as separate cart line
        for opt_id in (optional_product_ids or []):
            opt_tmpl = Template.browse(int(opt_id)).exists()
            if not opt_tmpl:
                continue
            opt_variant = opt_tmpl.product_variant_id
            if not opt_variant:
                continue
            order_sudo._cart_update(product_id=opt_variant.id, add_qty=1)

        return {
            'cart_quantity': order_sudo.cart_quantity,
            'amount_total': order_sudo.amount_total,
            'currency_id': order_sudo.currency_id.id,
            'product_name': tmpl.name,
        }
