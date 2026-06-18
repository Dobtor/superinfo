# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pencil_engraving_text = fields.Char(
        string="Apple Pencil 雷射刻字",
        help="用戶為 Apple Pencil 輸入的雷射刻字文字。",
    )
    ipad_engraving_text = fields.Char(
        string="iPad 雷射刻字",
        help="用戶為 iPad 輸入的雷射刻字文字。",
    )
