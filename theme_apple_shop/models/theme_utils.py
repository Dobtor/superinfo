# -*- coding: utf-8 -*-
"""theme.utils extension — runs once when the theme is applied to a website.

Odoo's theme.utils only exposes:
    - enable_view(xml_id)
    - disable_view(xml_id)
    - enable_asset(name) / disable_asset(name)
    - _reset_default_config()

Variable-level styling (colours, fonts, button radius) is delivered via
`apple_primary_variables.scss` injected into web.assets_primary_variables —
that bundle is loaded BEFORE Bootstrap, so our $primary / $body-color /
$btn-border-radius / $o-color-palettes overrides take effect site-wide.
"""
from odoo import models


class ThemeUtils(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_apple_shop_post_copy(self, mod):
        """Hook called by Odoo immediately after the theme is installed
        on a website. Resets any prior customizations and selects the
        cleanest header / footer variants for the Apple aesthetic.
        """
        self._reset_default_config()
        # No further enable/disable: stick with Odoo defaults; users can
        # still tweak header/footer in the customizer.
