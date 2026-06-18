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
    'category': 'Website',
    'version': '18.0.2.1.0',
    'sequence': 920,
    'depends': [
        'base',
        'website',
        'website_sale',
        # 'superinfo_website_data',  # uncomment when module is in addons path
    ],
    'data': [
        'security/ir.model.access.xml',
        # Assets registered via ir.asset (bypasses theme_ prefix limitation)
        'data/assets.xml',
        # Backend views
        'views/sale_order_views.xml',
        'views/product_attribute_views.xml',
        'views/product_template_views.xml',
        'views/product_public_category_views.xml',
        # Frontend templates (override website_sale)
        'views/buy_mac_landing.xml',
        'views/buy_mac_configurator.xml',
        'views/shop_cart_overrides.xml',
        'views/shop_trust_features.xml',
        'views/contactus.xml',
        'views/snippets.xml',
        # Data — base records owned by superinfo_website_data; theme only adds mac_* fields
        'data/product_attributes.xml',
        'data/product_categories.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'images': [],
    'demo': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
