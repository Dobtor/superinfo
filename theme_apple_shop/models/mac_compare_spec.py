# -*- coding: utf-8 -*-
from odoo import fields, models


class MacCompareSpec(models.Model):
    _name = 'mac.compare.spec'
    _description = 'Mac Compare Table Row'
    _order = 'sequence, id'

    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade',
        string="Product Template",
    )
    sequence = fields.Integer(default=10)
    label = fields.Char(
        string="Spec Label",
        translate=True, required=True,
        help="Left-column label, e.g. '處理器' / '記憶體' / '儲存裝置' / '連接埠'",
    )
    value = fields.Text(
        string="Spec Value",
        translate=True, required=True,
        help="Right-column value (multi-line allowed).",
    )
    icon = fields.Image(
        string="Spec Icon",
        max_width=64, max_height=64,
        help="Optional icon shown beside the label.",
    )
