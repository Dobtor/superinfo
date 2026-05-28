# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    apple_description = fields.Text(
        string="Apple Description",
        translate=True,
        help="Detailed description shown on the radio_card body, e.g. "
             "'10 核心 CPU、10 核心 GPU、16 核心神經網路引擎'.",
    )
    apple_sub_label = fields.Char(
        string="Apple Sub Label",
        translate=True,
        help="Optional secondary line above price, e.g. '2 個選項'.",
    )
    apple_image = fields.Image(
        string="Apple Option Image",
        max_width=400, max_height=400,
        help="Image for this option (e.g. colour swatch, chip illustration).",
    )
    apple_price_display = fields.Char(
        string="Apple Price Display Override",
        translate=True,
        help="Optional override for the price label, e.g. 'NT$26,900 起'. "
             "If empty, price is auto-formatted from price_extra.",
    )
