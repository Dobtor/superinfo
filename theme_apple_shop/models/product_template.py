# -*- coding: utf-8 -*-
import base64
import json
import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mac_color_attribute_id = fields.Many2one(
        'product.attribute',
        string="Mac Color Attribute",
        help="Which product.attribute drives the colour swatch and main-image swap. "
             "Leave empty if the product has no colour variants.",
    )
    mac_compare_spec_ids = fields.One2many(
        'mac.compare.spec', 'product_tmpl_id',
        string="Mac Compare Specs",
        help="Rows shown in the compare-table section at the bottom of the configurator.",
    )
    mac_default_ptav_ids = fields.Many2many(
        'product.template.attribute.value',
        'mac_default_ptav_rel',
        'tmpl_id', 'ptav_id',
        string="Default Selected Options",
        help="Pre-checked options when the configurator first loads. "
             "Pick one PTAV from each attribute_line for a clean default.",
    )
    apple_panel_section = fields.Selection(
        selection=[
            ('software',  'Pro App (Final Cut Pro / Logic Pro pre-install)'),
            ('accessory', 'Accessory (Mouse / Keyboard / Trackpad)'),
            ('applecare', 'AppleCare+ Protection Plan'),
        ],
        help="Where to render this product on the Mac configurator panel.",
    )
    apple_license_url = fields.Char(
        string="Apple License URL",
        help="External URL to the SLA / EULA shown as '查看授權協議' link "
             "next to a software pre-install option (Final Cut Pro / Logic Pro).",
    )

    def _get_apple_attribute_groups(self):
        """Returns this template's attribute_line_ids ordered by
        product.attribute.apple_section_order ASC.
        """
        self.ensure_one()
        return self.attribute_line_ids.sorted(
            key=lambda line: (line.attribute_id.apple_section_order, line.id)
        )

    def _get_apple_exclusion_table(self):
        """Build a JSON-serialisable exclusion map for the configurator JS.
        Returns {ptav_id: [excluded_ptav_ids, ...], ...}
        Used by the configurator widget to disable invalid combos in real-time.
        """
        self.ensure_one()
        table = {}
        for ptav in self.attribute_line_ids.product_template_value_ids:
            excl = list(set(
                ptav.exclude_for.filtered(
                    lambda e: e.product_tmpl_id == self
                ).value_ids.ids
            ))
            if excl:
                table[ptav.id] = excl
        return table

    @api.model
    def _sync_apple_assets_from_manifest(self):
        """Read tools/apple_assets_manifest.json and apply per-record images.
        Called from data/post_install.xml on every upgrade.
        Idempotent: missing/empty files are skipped silently.
        """
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manifest_path = os.path.join(module_dir, 'tools', 'apple_assets_manifest.json')
        if not os.path.isfile(manifest_path):
            _logger.info("apple manifest absent; skipping asset sync (%s)", manifest_path)
            return False

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        Category = self.env['product.public.category']
        AttrValue = self.env['product.attribute.value']
        n_cat = n_prod = n_color = 0

        # 1. Mac model categories
        for slug, info in manifest.get('mac_categories', {}).items():
            xml_id = info.get('xml_id')
            if not xml_id:
                continue
            categ = self.env.ref(xml_id, False)
            if not categ:
                continue
            updates = {}
            for field, key in (('mac_hero_image', 'hero'),):
                rel = info.get(key)
                if not rel:
                    continue
                full = os.path.join(module_dir, rel)
                if not os.path.isfile(full) or os.path.getsize(full) < 100:
                    continue
                with open(full, 'rb') as f:
                    updates[field] = base64.b64encode(f.read())
            if updates:
                categ.write(updates)
                n_cat += 1

        # 2. Mac product templates
        for slug, info in manifest.get('mac_products', {}).items():
            xml_id = info.get('xml_id')
            if not xml_id:
                continue
            prod = self.env.ref(xml_id, False)
            if not prod:
                continue
            rel = info.get('image_1920')
            if rel:
                full = os.path.join(module_dir, rel)
                if os.path.isfile(full) and os.path.getsize(full) >= 100:
                    with open(full, 'rb') as f:
                        prod.image_1920 = base64.b64encode(f.read())
                    n_prod += 1

        # 3. Color attribute swatches
        for slug, info in manifest.get('color_swatches', {}).items():
            xml_id = info.get('xml_id')
            if not xml_id:
                continue
            val = self.env.ref(xml_id, False)
            if not val:
                continue
            rel = info.get('apple_image')
            if rel:
                full = os.path.join(module_dir, rel)
                if os.path.isfile(full) and os.path.getsize(full) >= 100:
                    with open(full, 'rb') as f:
                        val.apple_image = base64.b64encode(f.read())
                    n_color += 1

        # 4. Accessory products (Magic Mouse / Keyboard / FCP / Logic / AppleCare)
        n_acc = 0
        for slug, info in manifest.get('accessories', {}).items():
            xml_id = info.get('xml_id')
            if not xml_id:
                continue
            prod = self.env.ref(xml_id, False)
            if not prod:
                continue
            rel = info.get('image_1920')
            if rel:
                full = os.path.join(module_dir, rel)
                if os.path.isfile(full) and os.path.getsize(full) >= 100:
                    with open(full, 'rb') as f:
                        prod.image_1920 = base64.b64encode(f.read())
                    n_acc += 1
        if n_acc:
            _logger.info("synced %s accessory product images", n_acc)

        # 5. Multi-angle thumbnails → product.image one2many
        # Idempotent: replace per-product gallery on each upgrade. Existing
        # images are deleted first so a manifest edit (e.g. fewer angles)
        # propagates cleanly.
        ProductImage = self.env['product.image']
        n_thumbs = 0
        for slug, info in manifest.get('thumbs', {}).items():
            prod = self.env.ref(info.get('product_xml_id') or '', False)
            if not prod:
                continue
            # Drop only the gallery rows we manage (mark name with prefix)
            existing = ProductImage.search([
                ('product_tmpl_id', '=', prod.id),
                ('name', '=like', 'apple_thumb_%'),
            ])
            existing.unlink()
            for idx, rel in enumerate(info.get('images', []), 1):
                full = os.path.join(module_dir, rel)
                if not os.path.isfile(full) or os.path.getsize(full) < 100:
                    continue
                with open(full, 'rb') as f:
                    img_b64 = base64.b64encode(f.read())
                ProductImage.create({
                    'name': f'apple_thumb_{idx}',
                    'image_1920': img_b64,
                    'product_tmpl_id': prod.id,
                    'sequence': idx,
                })
                n_thumbs += 1
        if n_thumbs:
            _logger.info("synced %s product.image thumbs across all Mac models", n_thumbs)

        _logger.info(
            "apple asset sync done: %s categories, %s products, %s color swatches",
            n_cat, n_prod, n_color,
        )
        return True

    @api.model
    def _setup_apple_price_extras(self):
        """Apply price_extra to PTAVs based on a known schedule.
        Called once via post_install function call.

        @api.model so the post_install <function> tag can call it without
        passing an ids argument — Odoo's call_kw skips the args[0] pop for
        @api.model methods (api.py line 522-528).
        """
        # Schedule: (template_xml_id, attribute_xml_id, value_xml_id, price_extra)
        schedule = [
            # Mac mini chip
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_chip',
             'theme_apple_shop.attr_val_chip_m4_pro', 20000),
            # Mac mini memory: each step +6000
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_memory',
             'theme_apple_shop.attr_val_mem_24', 6000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_memory',
             'theme_apple_shop.attr_val_mem_32', 12000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_memory',
             'theme_apple_shop.attr_val_mem_48', 18000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_memory',
             'theme_apple_shop.attr_val_mem_64', 24000),
            # Mac mini storage
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_storage',
             'theme_apple_shop.attr_val_storage_512', 6000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_storage',
             'theme_apple_shop.attr_val_storage_1tb', 12000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_storage',
             'theme_apple_shop.attr_val_storage_2tb', 24000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_storage',
             'theme_apple_shop.attr_val_storage_4tb', 48000),
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_storage',
             'theme_apple_shop.attr_val_storage_8tb', 96000),
            # Mac mini ethernet
            ('theme_apple_shop.prod_mac_mini', 'theme_apple_shop.attr_ethernet',
             'theme_apple_shop.attr_val_ether_10g', 3000),
        ]
        for tmpl_xid, attr_xid, val_xid, price in schedule:
            tmpl = self.env.ref(tmpl_xid, False)
            attr = self.env.ref(attr_xid, False)
            val = self.env.ref(val_xid, False)
            if not (tmpl and attr and val):
                continue
            ptav = self.env['product.template.attribute.value'].search([
                ('product_tmpl_id', '=', tmpl.id),
                ('attribute_id', '=', attr.id),
                ('product_attribute_value_id', '=', val.id),
            ], limit=1)
            if ptav:
                ptav.price_extra = price
        return True
