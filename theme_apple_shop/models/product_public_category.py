# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    hero_image = fields.Image(
        string="分類代表照片",
        max_width=1280, max_height=720,
        help="商品實拍照片，用於分類輪播卡片、子分類卡片、照片版分類導覽列等處。"
             "與線條小圖示（nav_icon）分開管理。",
    )
    mac_tagline = fields.Char(
        string="Mac Card Tagline",
        translate=True,
        help="Short subtitle on the Mac landing card, e.g. '為輕巧而生'",
    )
    mac_subtitle = fields.Char(
        string="Mac Card Subtitle",
        translate=True,
        help="Family tag, e.g. '桌上型' / '筆記型'",
    )
    mac_starting_price = fields.Monetary(
        string="Mac Starting Price",
        compute='_compute_mac_starting_price',
        store=True,
        currency_field='mac_currency_id',
        help="Auto-computed lowest-priced variant of products in this category.",
    )
    mac_currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_mac_currency',
        help="Currency for mac_starting_price (defaults to company currency).",
    )
    mac_banner_headline = fields.Char(
        string="Banner 大標題",
        translate=True,
        help="Apple 風格 banner 大標題，例如「用 iPad 大顯身手。」",
    )
    mac_banner_description = fields.Text(
        string="Banner 說明文字",
        translate=True,
        help="Banner 下方的描述段落文字。",
    )
    banner_image = fields.Image(
        string="Banner Hero 圖片",
        max_width=1600, max_height=900,
        help="Banner 下方的大型產品 hero 圖片（類似 Apple.com 分類頁）。",
    )

    mac_landing_order = fields.Integer(
        string="Mac Landing Order",
        default=10,
        help="Order on the /shop/category/mac landing carousel.",
    )
    nav_icon = fields.Image(
        string="分類導覽圖示",
        max_width=256, max_height=256,
        help="用於商品分類圖示導覽列的極簡線條小圖示（例如筆電/平板/手機輪廓），"
             "與 Landing Card 用的商品實拍照片（hero_image）分開管理。",
    )

    def _compute_mac_currency(self):
        company_currency = self.env.company.currency_id
        for rec in self:
            rec.mac_currency_id = company_currency

    @api.depends('product_tmpl_ids.list_price',
                 'product_tmpl_ids.product_variant_ids.lst_price')
    def _compute_mac_starting_price(self):
        for rec in self:
            templates = self.env['product.template'].search(
                [('public_categ_ids', 'in', rec.ids)]
            )
            prices = []
            for t in templates:
                if t.product_variant_ids:
                    prices.append(min(t.product_variant_ids.mapped('lst_price') or [t.list_price]))
                else:
                    prices.append(t.list_price)
            rec.mac_starting_price = min(prices) if prices else 0.0

