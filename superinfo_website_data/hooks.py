# -*- coding: utf-8 -*-
"""安裝後處理。

兩件事，都是 Odoo 18 架構下「以資料建立選單」必須在 hook 補的：

1. **把選單掛進預設網站的真正選單樹**
   `website.main_menu` 只是「給新網站複製用的範本根選單」；網站建立時會被
   `copy_menu_hierarchy` 複製成各自的 per-website 樹。`website._get_menu_ids()`
   只回傳 `website_id == 該網站` 的選單，故本模組以 XML 建立、`website_id` 為空、
   且掛在 `website.main_menu` 下的選單，預設網站的導覽列「不會顯示」。
   因此這裡：① 對本模組所有選單寫上 `website_id`；② 將最上層選單改掛到
   預設網站的真實根選單 `website.menu_id`。

2. **補上商城分類選單的真實 /shop/category/<slug> 網址**
   分類 slug 為 `name-id`，id 安裝時才指派，無法寫死於靜態 XML。
"""

# (商城選單 XML id, 對應分類 XML id)
SHOP_MENU_CATEGORY = [
    ("menu_shop_iphone_17", "categ_iphone_17"),
    ("menu_shop_iphone_17_air", "categ_iphone_17_air"),
    ("menu_shop_iphone_17_pro", "categ_iphone_17_pro"),
    ("menu_shop_iphone_acc", "categ_iphone_acc"),
    ("menu_shop_imac", "categ_mac_imac"),
    ("menu_shop_ipad_std", "categ_ipad_std"),
    ("menu_shop_ipad_mini", "categ_ipad_mini"),
    ("menu_shop_ipad_air", "categ_ipad_air"),
    ("menu_shop_ipad_pro", "categ_ipad_pro"),
    ("menu_shop_ipad_pencil", "categ_ipad_pencil"),
    ("menu_shop_ipad_keyboard", "categ_ipad_keyboard"),
    ("menu_shop_airpods", "categ_airpods"),
    ("menu_shop_acc_switcheasy", "categ_acc_switcheasy"),
    ("menu_shop_acc_elecom", "categ_acc_elecom"),
    ("menu_shop_acc_other", "categ_acc_other"),
]

# 最上層選單（XML 中掛在 website.main_menu 之下者）
TOP_MENU_XMLIDS = [
    "menu_about", "menu_services", "menu_training", "menu_shop", "menu_news",
]

M = "superinfo_website_data."


def _post_init_hook(env):
    website = env.ref("website.default_website", raise_if_not_found=False)
    if not website:
        website = env["website"].search([], limit=1)
    if not website:
        return

    # 1) 本模組建立的所有選單 → 指派到預設網站
    imd = env["ir.model.data"].search([
        ("module", "=", "superinfo_website_data"),
        ("model", "=", "website.menu"),
    ])
    menus = env["website.menu"].browse(imd.mapped("res_id")).exists()
    if menus:
        menus.write({"website_id": website.id})

    # 2) 最上層選單改掛到預設網站的真實根選單
    root = website.menu_id
    if root:
        for xid in TOP_MENU_XMLIDS:
            m = env.ref(M + xid, raise_if_not_found=False)
            if m:
                m.parent_id = root.id

    # 3) 商城分類選單補上正確 /shop/category/<slug>（v18：ir.http._slug）
    IrHttp = env["ir.http"]
    for menu_xid, categ_xid in SHOP_MENU_CATEGORY:
        menu = env.ref(M + menu_xid, raise_if_not_found=False)
        categ = env.ref(M + categ_xid, raise_if_not_found=False)
        if menu and categ:
            menu.url = "/shop/category/%s" % IrHttp._slug(categ)

    # 4) 清快取，讓導覽列即時反映新選單樹
    env.registry.clear_cache()
