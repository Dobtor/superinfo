# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    # Add Apple-specific display types. ondelete=set('radio') is explicit:
    # if our values are removed, fall back to Odoo's stock 'radio' style.
    display_type = fields.Selection(
        selection_add=[
            ('radio_card', 'Apple Radio Card (大卡片+描述+價格)'),
            ('toggle_yes_no', 'Apple Yes/No Toggle (預裝軟體)'),
        ],
        ondelete={
            'radio_card': lambda recs: recs.write({'display_type': 'radio'}),
            'toggle_yes_no': lambda recs: recs.write({'display_type': 'radio'}),
        },
    )
    apple_group_label = fields.Char(
        string="Apple Group Label",
        translate=True,
        help="Legend text shown above this attribute group on the configurator, "
             "e.g. '晶片。各款強大選項任你選擇。'",
    )
    apple_help_text = fields.Html(
        string="Apple Help Text",
        translate=True,
        help="Optional help content shown in a popover next to the legend.",
    )
    apple_section_order = fields.Integer(
        string="Apple Section Order",
        default=10,
        help="Order in which this attribute group appears in the right-side "
             "configurator panel. Lower = first.",
    )
    apple_subheading = fields.Char(
        string="Apple Subheading",
        translate=True,
        help="Sub-line shown next to the main label, e.g. for 晶片 the legend "
             "splits into '晶片。' (main) + '各款強大選項任你選擇。' (subheading). "
             "If empty, falls back to apple_group_label as a single line.",
    )
    apple_price_display = fields.Selection(
        selection=[
            ('none',     'No price column (memory / storage / ethernet)'),
            ('starting', 'Starting price absolute (晶片: NT$X 起)'),
            ('extra',    'Price extra (+NT$X)'),
        ],
        default='none',
        help="How each option's price is displayed in this attribute's group: "
             "'starting' shows base+price_extra as an absolute 'X 起' (used for chip); "
             "'none' shows nothing per-option (price is rolled into the summary total).",
    )
    apple_decision_desc = fields.Char(
        string="Decision-Support Description",
        translate=True,
        help="Description for the help card, e.g. '比較各個選項，看看哪一款最適合你。'",
    )
