{
    'name': 'Custom Homepage',
    'version': '18.0.1.0.0',
    'summary': '自訂網站首頁與服務頁面',
    'category': 'Website',
    # views/training_pages.xml 以 inherit_id 覆寫 superinfo_website_data 的
    # page_*_view，必須宣告依賴以確保載入順序。
    # theme_apple_shop：商品輪播 snippet 的 controller / JS widget / options /
    # 已 vendor 的 Swiper.js 都放在那邊（共用實作，避免跟 superinfo_website_data
    # 對 theme_apple_shop 的既有依賴形成循環依賴）。這裡只放自己的版型 + skin。
    'depends': ['website', 'website_blog', 'superinfo_website_data', 'theme_apple_shop'],
    'data': [
        'views/stitch_shared.xml',
        'views/homepage_template.xml',
        'views/service_pages.xml',
        'views/training_pages.xml',
        'views/stitch_homepage.xml',
        'views/snippets.xml',
        'data/menu_data.xml',
        'data/pages_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_homepage/static/src/css/design_bridge.css',
            'custom_homepage/static/src/css/training.css',
            'custom_homepage/static/src/css/homepage_product_swiper.css',
        ],
    },
    'installable': True,
    'auto_install': False,
}
