{
    'name': 'Custom Homepage',
    'version': '18.0.1.0.0',
    'summary': '自訂網站首頁與服務頁面',
    'category': 'Website',
    'depends': ['website', 'website_blog'],
    'data': [
        'views/stitch_shared.xml',
        'views/homepage_template.xml',
        'views/service_pages.xml',
        'views/training_pages.xml',
        'views/stitch_homepage.xml',
        'data/menu_data.xml',
        'data/pages_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'custom_homepage/static/src/css/design_bridge.css',
            'custom_homepage/static/src/css/training.css',
        ],
    },
    'installable': True,
    'auto_install': False,
}
