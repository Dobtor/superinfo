# -*- coding: utf-8 -*-
{
    'name': 'Apple Shop Theme',
    'summary': 'Apple-style buy-mac flow over Odoo website_sale',
    'description': """
        Mode B (override-only) implementation of the Apple Shop UX:
        - Overrides /shop/category/<mac> → renders 8-card Mac landing
        - Overrides /shop/<mac-product> → renders left-image / right-sticky-panel configurator
        - Reuses Odoo native cart / checkout / payment / confirmation flow
        Module uninstall reverts all routes to Odoo defaults.
    """,
    'author': 'Dobtor SI',
    'website': 'https://www.dobtor.com',
    'category': 'Theme',
    'version': '18.0.2.1.0',
    'sequence': 920,
    'depends': [
        'base',
        'website',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.xml',
        # Backend views
        'views/product_attribute_views.xml',
        'views/product_template_views.xml',
        'views/product_public_category_views.xml',
        # Frontend templates (override website_sale)
        'views/buy_mac_landing.xml',
        'views/buy_mac_configurator.xml',
        'views/shop_cart_overrides.xml',
        # Data — order matters: attributes → categories → products → accessories
        'data/product_attributes.xml',
        'data/product_categories.xml',
        'data/products_accessories.xml',
        'data/products_mac.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'assets': {
        # Site-wide Bootstrap variable overrides — loaded BEFORE Bootstrap so
        # !default rules pick up our values. Affects every page.
        'web.assets_primary_variables': [
            'theme_apple_shop/static/src/scss/apple_primary_variables.scss',
        ],
        'web.assets_frontend': [
            # Our own $apple-* design tokens — prepended (no Bootstrap dependency)
            ('prepend', 'theme_apple_shop/static/src/scss/apple_variables.scss'),
            # Element-level defaults — depends on Bootstrap variables
            # ($font-family-base, $primary, $body-color, $border-radius, ...).
            # Bootstrap _variables.scss must load FIRST, so this file goes AFTER
            # the framework chunk (no prepend) but before page-specific SCSS.
            'theme_apple_shop/static/src/scss/apple_theme_defaults.scss',
            # Page-specific styles
            'theme_apple_shop/static/src/scss/apple_landing.scss',
            'theme_apple_shop/static/src/scss/apple_configurator.scss',
            'theme_apple_shop/static/src/scss/apple_cart.scss',
            'theme_apple_shop/static/src/scss/apple_overrides.scss',
            # JS widgets
            'theme_apple_shop/static/src/js/apple_configurator.js',
            'theme_apple_shop/static/src/js/apple_image_carousel.js',
            'theme_apple_shop/static/src/js/apple_cart_drawer.js',
            'theme_apple_shop/static/src/js/apple_compare_table.js',
        ],
    },
    'images': [],
    'demo': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
