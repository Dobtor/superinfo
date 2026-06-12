# superinfo_website_data — 極電資訊官網資料模組

以 **Odoo 18 原生** website / website_sale / website_blog 模型與原生 snippet（block）重建
[superinfo.com.tw](https://www.superinfo.com.tw/) 全站內容。**不含任何自訂 SCSS／JS／snippet**，
安裝即建站。

## 內容

| 區塊 | 來源 | 對應原生 snippet / 模型 |
|------|------|------|
| 69 件商品（價格／圖片／描述／分類） | Google 商品 feed（權威來源） | `product.template` |
| 20 個商城分類樹（iPhone/Mac/iPad/AirPods/副廠週邊） | 站台導覽 | `product.public.category` |
| 商城多選單 → 各分類 `/shop/category/<slug>` 篩選結果 | — | `website.menu`（slug 由 `post_init_hook` 補上） |
| 主選單（關於我們／專案服務／蘋果培訓／商城／最新消息／商店資訊） | 站台導覽 | `website.menu` |
| 首頁 | banner + 品牌 | `s_carousel` / `s_cards_grid` / `s_references` / `s_call_to_action` |
| 關於我們 | 逐字文案 + hero | `s_cover` / `s_text_block` |
| 專案服務 6 頁 | 逐字文案 + hero | `s_cover` / `s_text_block` |
| 蘋果培訓 13 頁 | 逐字文案 + hero | `s_cover` / `s_text_block` |
| 常見問題 | 逐字 Q&A | `s_cover` / `s_faq_collapse` |
| 資訊安全／隱私權／購物須知 | 逐字文案 + hero | `s_cover` / `s_text_block` |
| 最新消息 4 篇 | 站台公告 | `blog.blog` / `blog.post`（website_blog 模組，模型名是 `blog.blog` 非 `website.blog`） |

## 安裝

```bash
# 把本模組放進 addons 路徑後：
./odoo-bin -d <db> -i superinfo_website_data --stop-after-init
# 升級：
./odoo-bin -d <db> -u superinfo_website_data --stop-after-init
```

`post_init_hook` 會把 15 個商城分類選單的 URL 補成正確的 `/shop/category/<id>-<slug>`。

## 補強紀錄

1. **隱私權政策 / 購物須知**：已用瀏覽器渲染擷取 JS 動態載入的完整條文（隱私 22 段、購物須知 129 段），逐字建入 `s_text_block`。
2. **商品顏色變體**：已從商品圖路徑解析出官方色名，建立 `product.attribute`「顏色」（`display_type=color`、`create_variant=always`）共 17 色，並對 12 件可信商品（iPhone 17 / 17 Air、iPad A16、iPad mini、iMac）建立 `product.template.attribute.line` 變體。
3. **Mac / MacBook**：經實機爬取確認，原站 MacBook Pro/Air、Mac mini 等分類頁目前為**空殼分類頁（無上架 SKU、無價格、無內容）**，故不虛構商品；商城 Mac 分類忠實呈現原站唯一可購買的 1 台 iMac。

## Odoo 18 規範稽核（已修正）

對照 odoo-18.0 原始碼逐項稽核，修正下列會導致安裝失敗或功能失效的問題：

1. **選單無法顯示（最關鍵）**：`website._get_menu_ids()` 只回傳 `website_id == 該網站` 的選單，且 `website.main_menu` 僅為「新網站複製範本」。原以 XML 掛在 main_menu、`website_id` 為空的選單在預設網站導覽列不會出現。→ `post_init_hook` 改為：對全部選單寫入 `website_id`、最上層選單改掛到 `website.menu_id` 真實根、最後 `clear_cache()`。
2. **post_init_hook 未曝露**：Odoo 以 `getattr(package, '_post_init_hook')` 取用，`__init__.py` 補上 `from .hooks import _post_init_hook`。
3. **slug API**：v18 改為 `env['ir.http']._slug(record)`（`name-id`），已更新。
4. **s_cover 視差背景**：移除需 `.s_parallax_bg` 子元素的 `parallax` 類別，改純 `oe_img_bg`。
5. **首頁 `o_grid_mode`**：改 `s_nb_column_fixed`。

已驗證通過：頁面/部落格在 `website_id` 為空時可正常服務（domain 含 `False`）、25 個頁面 URL 唯一且不與核心路由衝突、70 張 base64 圖與 38 個版型圖皆為合法影像（非錯誤頁）、所有 `ref` 解析、`display_type='color'`／`create_variant='always'`／`type='consu'`／`homepage_url` 皆符合 v18。

## 其他說明

- 圖片皆已縮圖（最長邊 ≤ 700–900px）以控制 repo 體積（約 53MB）。
- 每個容量在原站本就是獨立商品（如 iPhone 17 256GB / 512GB），已忠實保留為獨立 `product.template`；「顏色」才是商品內的變體維度。
