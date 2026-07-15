# -*- coding: utf-8 -*-
"""Mode B: override website_sale routes — never add new ones.

Conditionally branches on Mac category / Mac product:
- /shop/category/<mac>      → Apple-style landing
- /shop/<mac-product>       → Apple-style configurator
- everything else           → super() to Odoo defaults
"""
import json
import logging

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.combo_configurator import WebsiteSaleComboConfiguratorController
from odoo.addons.website_sale.controllers.product_configurator import WebsiteSaleProductConfiguratorController

_logger = logging.getLogger(__name__)


class AppleShop(WebsiteSaleComboConfiguratorController, WebsiteSaleProductConfiguratorController, WebsiteSale):

    # ─── helpers ───────────────────────────────────────────────────

    # ─── / (homepage) ────────────────────────────────────────────────
    # 不覆寫根路由：首頁交由 Odoo 原生邏輯（網站設定 → 首頁網址）決定，
    # 不綁死成 Mac landing。要把 Mac landing 當首頁時，於後台將首頁網址
    # 設為 /shop/category/mac 即可（該路由仍由本控制器提供）。

    # ─── /contactus ─────────────────────────────────────────────────────

    @http.route(['/contactus'], type='http', auth='public', website=True, sitemap=True)
    def contactus(self, success=False, **kwargs):
        return request.render('theme_apple_shop.contactus', {
            'success': bool(success),
            'main_object': request.website,
        })

    @http.route(['/contactus/submit'], type='http', auth='public', website=True,
                methods=['POST'], csrf=True)
    def contactus_submit(self, contact_name='', email_from='', phone='',
                         partner_name='', name='', description='', tag_ids='', **kwargs):
        """Receive the Apple-style contact form and create a CRM lead."""
        request.env['crm.lead'].sudo().create({
            'contact_name': contact_name,
            'email_from': email_from,
            'phone': phone,
            'partner_name': partner_name,
            'name': name or '(無主旨)',
            'description': description,
            'type': 'lead',
        })
        return request.redirect('/contactus/thanks')

    @http.route(['/contactus/thanks'], type='http', auth='public', website=True, sitemap=False)
    def contactus_thanks(self, **kwargs):
        return request.render('theme_apple_shop.contactus_thanks', {
            'main_object': request.website,
        })

    # ─── Snippet: category icon nav content ──────────────────────────

    @http.route('/theme_apple_shop/snippet/categ_nav',
                type='http', auth='public', website=True)
    def snippet_categ_nav(self, **kwargs):
        Categ = request.env['product.public.category']
        categs = Categ.search([('parent_id', '=', False)], order='sequence, id')
        # inherit_branding=False: this fragment is injected into another
        # page's DOM via JS — without this, QWeb tags every element with
        # data-oe-* markers pointing back at THIS template's view, so saving
        # the host page corrupts the shared template with that page's content.
        return request.env['ir.qweb'].with_context(inherit_branding=False)._render(
            'theme_apple_shop.s_apple_categ_nav_content',
            {'categories': categs},
        )

    # ─── Snippet: category carousel content ───────────────────────────

    @http.route('/theme_apple_shop/snippet/categ_carousel',
                type='http', auth='public', website=True)
    def snippet_categ_carousel(self, categ_id='0', **kwargs):
        Categ = request.env['product.public.category']
        cid = int(categ_id)
        if cid:
            categs = Categ.search([('parent_id', '=', cid)], order='sequence, id')
        else:
            categs = Categ.search([('parent_id', '=', False)], order='sequence, id')
        return request.env['ir.qweb'].with_context(inherit_branding=False)._render(
            'theme_apple_shop.s_apple_categ_carousel_content',
            {'categories': categs},
        )

    # ─── Snippet: product swiper content (shared — also used by
    # custom_homepage's s_homepage_product_swiper via the same .s_product_swiper
    # JS widget/endpoint; see custom_homepage's manifest depends comment) ────

    @http.route('/theme_apple_shop/snippet/product_swiper',
                type='http', auth='public', website=True)
    def snippet_product_swiper(self, categ_id='0', **kwargs):
        cid = int(categ_id)
        products = request.env['product.template'].sudo()
        if cid:
            # child_of also matches cid itself, so a leaf category with its
            # own products keeps working the same as before.
            categ_ids = request.env['product.public.category'].sudo().search(
                [('id', 'child_of', cid)]
            ).ids
            products = products.search([
                ('public_categ_ids', 'in', categ_ids),
                ('is_published', '=', True),
            ], order='name')
        # inherit_branding=False: this fragment is injected into the host
        # page's DOM via JS — without this, QWeb tags every element with
        # data-oe-* markers pointing back at THIS template's view, so saving
        # the host page corrupts this shared template with that page's content.
        return request.env['ir.qweb'].with_context(inherit_branding=False)._render(
            'theme_apple_shop.s_product_swiper_content',
            {'products': products},
        )

    # ─── /shop/category/mac  (friendly slug without ID suffix) ───────

    @http.route(
        ['/shop/category/mac'],
        type='http', auth='public', methods=['GET'], website=True,
    )
    def mac_category_landing(self, **kwargs):
        mac_root = request.env.ref(
            'superinfo_website_data.categ_mac', raise_if_not_found=False
        )
        if mac_root:
            return self._render_category_landing(mac_root)
        return request.redirect('/shop')

    # ─── /shop and /shop/category/<categ> ──────────────────────────

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        # Any category page → Apple landing
        if category and category.exists():
            return self._render_category_landing(category)

        # 無篩選的 /shop 不再強制導 Mac landing：交還 Odoo 原生商店頁。
        # 要把 Mac landing 當商店入口時，請用 /shop/category/mac。
        return super().shop(
            page=page, category=category, search=search,
            min_price=min_price, max_price=max_price, ppg=ppg, **post,
        )

    def _render_category_landing(self, categ, page_title=None, is_homepage=False):
        Categ = request.env['product.public.category']
        top_categories = Categ.search(
            [('parent_id', '=', False)],
            order='sequence, id',
        )
        subcategories = Categ.search(
            [('parent_id', '=', categ.id)],
            order='sequence, id',
        )
        # When no subcategories, fall back to products in this category
        products = None
        if not subcategories and not is_homepage:
            products = request.env['product.template'].sudo().search([
                ('public_categ_ids', '=', categ.id),
                ('is_published', '=', True),
            ], order='name')
        title = page_title or ('選購 ' + categ.name)
        return request.render('theme_apple_shop.buy_mac_landing', {
            'mac_root': categ,
            'current_categ': categ,
            'top_categories': top_categories,
            'subcategories': subcategories,
            'products': products,
            'is_homepage': is_homepage,
            'main_object': categ,
            'page_title': title,
        })

    # ─── /shop/<product> ───────────────────────────────────────────

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        return self._render_mac_configurator(product, **kwargs)

    def _render_mac_configurator(self, product, **kwargs):
        attribute_lines = product._get_apple_attribute_groups()
        default_ptavs = product.mac_default_ptav_ids or self._compute_initial_default_ptavs(product)
        exclusion_table = json.dumps(product._get_apple_exclusion_table())
        color_image_map = self._build_color_image_map(product)
        return request.render('theme_apple_shop.buy_mac_configurator', {
            'product': product,
            'attribute_lines': attribute_lines,
            'default_ptavs': default_ptavs,
            'optional_products': product.optional_product_ids,
            'exclusion_table': exclusion_table,
            'color_image_map': color_image_map,
            'main_object': product,
        })

    def _build_color_image_map(self, product):
        """Return {ptav_id: image_url} for each color swatch.

        Strategy (in order):
        1. gallery images with product_variant_id whose combination includes this color PTAV
        2. variant's own image_variant_1024 (if variant exists and has an image)
        3. gallery images matched positionally to color PTAVs (index order)
        4. fallback: product template main image
        """
        color_attr = product.mac_color_attribute_id
        if not color_attr:
            return {}

        color_line = product.attribute_line_ids.filtered(
            lambda l: l.attribute_id == color_attr
        )
        if not color_line:
            return {}

        # 只取啟用的色值，略過已封存的幽靈 PTAV（與模板色票迴圈一致）
        color_ptavs = color_line.product_template_value_ids.filtered('ptav_active')
        fallback_url = '/web/image/product.template/%d/image_1024' % product.id
        result = {}

        # Strategy 1 & 2: try existing variants
        for ptav in color_ptavs:
            variant = product.product_variant_ids.filtered(
                lambda v: ptav in v.product_template_attribute_value_ids
            )[:1]
            if variant:
                # prefer gallery image linked to this variant
                gimg = product.product_template_image_ids.filtered(
                    lambda i: i.product_variant_id and i.product_variant_id.id == variant.id
                )[:1]
                if gimg:
                    result[ptav.id] = '/web/image/product.image/%d/image_1024' % gimg.id
                elif variant.image_variant_1024:
                    result[ptav.id] = '/web/image/product.product/%d/image_variant_1024' % variant.id

        # Strategy 3: positional fallback — gallery images (excluding variant-linked ones)
        # paired with color PTAVs in declaration order
        if len(result) < len(color_ptavs):
            unlinked_imgs = product.product_template_image_ids.filtered(
                lambda i: not i.product_variant_id
            ).sorted(lambda i: i.sequence)
            for i, ptav in enumerate(color_ptavs):
                if ptav.id not in result and i < len(unlinked_imgs):
                    result[ptav.id] = '/web/image/product.image/%d/image_1024' % unlinked_imgs[i].id

        # Strategy 4: final fallback
        for ptav in color_ptavs:
            result.setdefault(ptav.id, fallback_url)

        return result

    def _compute_initial_default_ptavs(self, product):
        """If admin didn't set mac_default_ptav_ids, pick the cheapest PTAV
        per attribute_line as the initial selection."""
        defaults = request.env['product.template.attribute.value']
        for line in product.attribute_line_ids:
            # 略過已封存的幽靈 PTAV，否則預設可能落在買不到的幽靈色值上
            cheapest = line.product_template_value_ids.filtered('ptav_active').sorted(
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
                        optional_product_ids=None,
                        pencil_engraving_text=None,
                        ipad_engraving_text=None,
                        **kwargs):
        Template = request.env['product.template'].sudo()
        tmpl = Template.browse(int(product_template_id)).exists()
        if not tmpl:
            return {'error': 'Invalid product'}

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

        # Save engraving text onto the newly created order line
        if pencil_engraving_text or ipad_engraving_text:
            line = order_sudo.order_line.filtered(
                lambda l: l.product_id.id == variant.id
            ).sorted('id', reverse=True)[:1]
            if line:
                vals = {}
                if pencil_engraving_text:
                    vals['pencil_engraving_text'] = pencil_engraving_text[:10]
                if ipad_engraving_text:
                    vals['ipad_engraving_text'] = ipad_engraving_text[:30]
                line.sudo().write(vals)

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
