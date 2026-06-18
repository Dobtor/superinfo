# -*- coding: utf-8 -*-
{
    'name': 'Superinfo 極電資訊 官網資料',
    'summary': '極電資訊 superinfo.com.tw 全站資料模組（純原生 snippet，無自訂樣式）',
    'description': """
極電資訊官網資料模組
====================
以 Odoo 18 原生 website / website_sale / website_blog 模型與原生 snippet
重建 superinfo.com.tw 全站內容：選單、CMS 頁面、商城分類、商品（含變體）、
最新消息、品牌牆。安裝即建站，不含任何自訂 SCSS/JS/snippet。

對應 snippet：s_carousel / s_dynamic_snippet_products / s_references /
s_cards_grid / s_image_text / s_numbers / s_key_benefits / s_process_steps /
s_features / s_faq_collapse / s_comparisons / s_text_block / s_call_to_action。
""",
    'author': 'Dobtor SI',
    'website': 'https://www.dobtor.com',
    'category': 'Website',
    'version': '18.0.1.0.0',
    'depends': [
        'website',
        'website_sale',
        'website_blog',
        # 提供 apple_*/mac_* 欄位定義 + Apple 風格商店呈現；
        # 本模組的 product_mac_apple.xml 會填這些欄位的值。
        'theme_apple_shop',
    ],
    'data': [
        # 公司 / 網站基本設定
        'data/res_config.xml',
        # 商品分類 / 屬性 / 商品
        'data/product_categories.xml',
        'data/product_attributes.xml',
        # Apple/Mac 主題整合（須在 categ_mac / attr_color 之後載入）
        'data/product_mac_apple.xml',
        'data/products_iphone.xml',
        'data/products_mac.xml',
        'data/products_ipad.xml',
        'data/products_airpods.xml',
        'data/products_accessories.xml',
        'data/products_variants.xml',
        # CMS 頁面（原生 snippet）
        'data/page_home.xml',
        'data/page_about.xml',
        'data/pages_project.xml',
        'data/page_ipad_deploy.xml',
        'data/page_byod.xml',
        'data/page_mac_classroom.xml',
        'data/pages_training.xml',
        'data/pages_info.xml',
        'data/footer.xml',
        # 最新消息 / 實際案例（部落格）
        'data/blog_news.xml',
        'data/blog_cases.xml',
        # 商品圖（每次升級重載）
        'data/product_images.xml',
        # 選單（最後，程式化建立：確保 page/category 已存在；安裝與升級都重建）
        'data/menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'superinfo_website_data/static/src/scss/superinfo_pages.scss',
            'superinfo_website_data/static/src/scss/apl_tailwind.css',
            'superinfo_website_data/static/src/js/apl_reveal.js',
        ],
    },
    'images': ['static/description/cover.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
