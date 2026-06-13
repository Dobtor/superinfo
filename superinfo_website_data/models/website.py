# -*- coding: utf-8 -*-
from odoo import api, models

# 完整選單樹。每個 node：name / 可選 url / 可選 categ(分類 xmlid，產生 /shop/category/<slug>) / 可選 children
MENU_TREE = [
    {"name": "關於我們", "url": "/about"},
    {"name": "專案服務", "url": "#", "children": [
        {"name": "共契BOT專區", "url": "/services/bot"},
        {"name": "iPad 大量部署", "url": "/services/ipad-deployment"},
        {"name": "BYOD 自帶載具計畫", "url": "/services/byod"},
        {"name": "Mac 電腦教室", "url": "/services/mac-classroom"},
        {"name": "實際案例", "url": "/services/cases"},
        {"name": "PROMISE", "url": "/services/promise"},
    ]},
    # 蘋果培訓 已捨棄，改為兩個頂層選單
    {"name": "蘋果教育專區", "url": "/apple-training/edu-hub", "children": [
        {"name": "課程學習中心", "url": "/apple-training/courses"},
        {"name": "輔助使用", "url": "/apple-training/accessibility"},
        {"name": "永續政策", "url": "/apple-training/sustainability"},
        {"name": "聰明投資", "url": "/apple-training/smart-investment"},
        {"name": "生命週期管理", "url": "/apple-training/lifecycle"},
        {"name": "教育軟體解決方案", "url": "/apple-training/services-apps"},
    ]},
    {"name": "蘋果培訓適用對象", "url": "/apple-training/audiences", "children": [
        {"name": "IT 部門", "url": "/apple-training/it"},
        {"name": "教育工作者", "url": "/apple-training/educators"},
        {"name": "教育領導者", "url": "/apple-training/leaders"},
        {"name": "決策者", "url": "/apple-training/decision-makers"},
        {"name": "家長", "url": "/apple-training/parents"},
    ]},
    # 產品線頂層選單：頂層連父分類（child_of 遞迴 → 顯示該線全部商品），
    # 第二層連葉分類做篩選範圍。Odoo 選單只支援兩層，故原站第三層商品歸入第二層。
    {"name": "iPhone", "categ": "categ_iphone", "children": [
        {"name": "iPhone 17", "categ": "categ_iphone_17"},
        {"name": "iPhone 17 Air", "categ": "categ_iphone_17_air"},
        {"name": "iPhone 17 Pro", "categ": "categ_iphone_17_pro"},
        {"name": "iPhone 配件", "categ": "categ_iphone_acc"},
    ]},
    {"name": "Mac", "categ": "categ_mac", "children": [
        {"name": "iMac", "categ": "categ_mac_imac"},
        {"name": "Mac 配件", "categ": "categ_mac_acc"},
    ]},
    {"name": "iPad", "categ": "categ_ipad", "children": [
        {"name": "iPad", "categ": "categ_ipad_std"},
        {"name": "iPad mini", "categ": "categ_ipad_mini"},
        {"name": "iPad Air", "categ": "categ_ipad_air"},
        {"name": "iPad Pro", "categ": "categ_ipad_pro"},
        {"name": "Apple Pencil", "categ": "categ_ipad_pencil"},
        {"name": "鍵盤", "categ": "categ_ipad_keyboard"},
    ]},
    {"name": "AirPods", "categ": "categ_airpods"},
    {"name": "副廠週邊", "categ": "categ_acc", "children": [
        {"name": "SwitchEasy", "categ": "categ_acc_switcheasy"},
        {"name": "ELECOM", "categ": "categ_acc_elecom"},
        {"name": "其他周邊", "categ": "categ_acc_other"},
    ]},
    {"name": "最新消息", "url": "/blog"},
    {"name": "商店資訊", "url": "#", "children": [
        {"name": "常見問題", "url": "/info/faq"},
        {"name": "資訊安全", "url": "/info/security"},
        {"name": "隱私權政策", "url": "/info/privacy"},
        {"name": "購物須知與服務條款", "url": "/info/terms"},
    ]},
]


def _all_names(nodes, acc):
    for n in nodes:
        acc.add(n["name"])
        _all_names(n.get("children", []), acc)
    return acc


# 曾經用過、現已移除的頂層選單名稱（升級時一併清除，避免殘留）
OBSOLETE_MENU_NAMES = ["商城", "蘋果培訓"]


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _superinfo_build_menus(self):
        """於安裝與每次升級時呼叫（由 data/menus.xml 的 <function> 觸發）。

        直接以 website_id 建立選單樹 → Odoo 的 website.menu.create() 會走
        'website_id' in vals 分支，**不做跨網站複製**，因此不會產生重複；
        子選單掛在同一網站的父選單複本下 → 下拉正確顯示。
        先依名稱清掉舊的（含先前 bug 版本造成的重複），再重建 → 具冪等性。
        """
        for website in self.search([]):
            website._superinfo_build_menus_one()

    def _superinfo_build_menus_one(self):
        self.ensure_one()
        Menu = self.env["website.menu"]
        root = self.menu_id
        if not root:
            return
        names = list(_all_names(MENU_TREE, set())) + OBSOLETE_MENU_NAMES
        # 清掉本網站上同名的舊選單（移除舊版重複與已移除的「商城」），父刪子會 cascade
        Menu.search([("website_id", "=", self.id), ("name", "in", names)]).unlink()
        self._superinfo_create_nodes(MENU_TREE, root, base_seq=20)
        self.env.registry.clear_cache()

    def _superinfo_create_nodes(self, nodes, parent, base_seq=10):
        Menu = self.env["website.menu"]
        IrHttp = self.env["ir.http"]
        for i, node in enumerate(nodes):
            url = node.get("url") or "#"
            categ_xid = node.get("categ")
            blog_xid = node.get("blog")
            if categ_xid:
                categ = self.env.ref(
                    "superinfo_website_data." + categ_xid, raise_if_not_found=False
                )
                url = "/shop/category/%s" % IrHttp._slug(categ) if categ else "/shop"
            elif blog_xid:
                blog = self.env.ref(
                    "superinfo_website_data." + blog_xid, raise_if_not_found=False
                )
                url = "/blog/%s" % IrHttp._slug(blog) if blog else "/blog"
            menu = Menu.create({
                "name": node["name"],
                "url": url,
                "parent_id": parent.id,
                "website_id": self.id,
                "sequence": base_seq + i * 10,
            })
            if node.get("children"):
                self._superinfo_create_nodes(node["children"], menu, base_seq=10)
