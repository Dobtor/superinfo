/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/**
 * Apple-style configurator widget.
 *
 * Responsibilities:
 *   - Real-time price recalculation when PTAV / optional product selection changes
 *   - Image cross-fade when colour swatch changes
 *   - Variant exclusion enforcement (server-rendered exclusion table)
 *   - Add-to-bag → /shop/cart/update_json (Odoo native)
 *   - Trigger cart drawer open on success
 */
publicWidget.registry.AppleConfigurator = publicWidget.Widget.extend({
    selector: ".apple-configurator",
    events: {
        "change input.ptav-input": "_onPtavChange",
        "change input.optional-input": "_onOptionalChange",
        "change input.optional-toggle-input": "_onSoftwareToggle",
        "change input.tradein-input": "_onTradeinToggle",
        "change input.laser-toggle-input": "_onLaserToggle",
        "input .engraving-input": "_onEngravingInput",
        "click .swatch": "_onSwatchClick",
        "click .add-to-bag": "_onAddToBag",
        "click .help-trigger": "_onHelpClick",
        "keydown .rc-card": "_onCardKeyDown",
    },

    start() {
        this._cacheDom();
        this._buildExclusionTable();
        this._bindRadioCardClick();
        this._refreshAvailability();
        this._recalcPrice(/* initial */ true);
        return this._super(...arguments);
    },

    _cacheDom() {
        this.$el = this.el;
        this.basePrice = parseFloat(this.el.dataset.basePrice) || 0;
        this.colorAttrId = parseInt(this.el.dataset.colorAttrId || 0);
        this.productTmplId = parseInt(this.el.dataset.productTmplId);
        this.currencySymbol = this.el.dataset.currencySymbol || "NT$";
        this._priceDisplays = this.el.querySelectorAll('[data-display="total"]');
        this._mainImage = this.el.querySelector(".main-image");
        // 問價請求的序號，用於丟棄亂序返回的舊結果（見 _recalcPrice）
        this._priceToken = 0;
    },

    _buildExclusionTable() {
        try {
            const raw = this.el.dataset.exclusionTable || "{}";
            this._exclusionTable = JSON.parse(raw);
        } catch (e) {
            this._exclusionTable = {};
        }
    },

    /**
     * Whole .rc-card label is clickable — but if user clicks on the <input>
     * directly it bubbles up. Either way the input receives 'change'.
     * We also want clicking anywhere on the card to focus the input for a11y.
     */
    _bindRadioCardClick() {
        this.el.querySelectorAll(".rc-card").forEach((card) => {
            card.addEventListener("click", (ev) => {
                const input = card.querySelector("input");
                if (input && !input.disabled && ev.target !== input) {
                    input.checked = input.type === "checkbox" ? !input.checked : true;
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                }
            });
        });
    },

    // ─── Price recalculation ─────────────────────────

    /**
     * 變體價一律向後端問（原生 combination_info），不在前端加總 price_extra。
     * 原因：商品的成交價不一定等於「各選項固定加價之和」——同一組容量升級在
     * 不同記憶體下的價差可以不同，這種交互定價只有後端查表算得出來，前端相加
     * 必然算錯（且會與結帳金額不一致）。沒有交互定價的商品，該端點回傳的就是
     * 原生線性價，行為與改版前相同。
     */
    async _recalcPrice(skipAnimation) {
        const ptavIds = Array.from(
            this.el.querySelectorAll("input.ptav-input:checked")
        )
            .map((inp) => parseInt(inp.dataset.ptavId))
            .filter((id) => !isNaN(id));

        // 加購商品是各自獨立的訂單明細，不屬於變體定價，仍在前端加總
        let optionalTotal = 0;
        this.el.querySelectorAll("input.optional-input:checked").forEach((inp) => {
            optionalTotal += parseFloat(inp.dataset.price || 0);
        });

        // 連續點選會併發多個請求，只認最後一次發出的那個的結果
        const token = ++this._priceToken;
        let variantPrice = null;
        let combinationPossible = true;
        if (this.productTmplId && ptavIds.length) {
            try {
                const info = await rpc("/website_sale/get_combination_info", {
                    product_template_id: this.productTmplId,
                    product_id: false,
                    combination: ptavIds,
                    add_qty: 1,
                });
                if (token !== this._priceToken) {
                    return;     // 已有更晚發出的請求，本次結果作廢
                }
                if (info) {
                    // 不可售的組合（變體封存／被排除）後端不給價，
                    // 此時 info.price 會是回退的原生價，顯示出來會誤導 → 不採用
                    combinationPossible = info.is_combination_possible !== false;
                    if (combinationPossible && typeof info.price === "number") {
                        variantPrice = info.price;
                    }
                }
            } catch (e) {
                variantPrice = null;    // 落回線性估算，不讓價格欄空白
            }
        }

        // 按鈕狀態要跟著組合可售性走：自刻頁面的按鈕不吃原生變體狀態，
        // 少了這一步，不可售組合按下去只會撞訂單層的 ValidationError
        this._setAddToBagEnabled(combinationPossible);

        if (!combinationPossible) {
            this._setPriceUnavailable();
            return;
        }

        const total = variantPrice === null
            ? this._linearFallback()
            : variantPrice + optionalTotal;

        if (skipAnimation) {
            this._setPrice(total);
        } else {
            this._animatePriceUpdate(total);
        }
    },

    _setAddToBagEnabled(enabled) {
        const btn = this.el.querySelector(".add-to-bag");
        if (!btn) {
            return;
        }
        btn.disabled = !enabled;
        btn.classList.toggle("disabled", !enabled);
        btn.setAttribute("aria-disabled", String(!enabled));
    },

    /** 不供應的組合顯示破折號：語言中性，且與「0 元」明確區分。 */
    _setPriceUnavailable() {
        this._priceDisplays.forEach((el) => {
            el.textContent = "—";
        });
    },

    /** 後端問價失敗時的估算：基本價 ＋ Σ 固定加價（改版前的算法）。 */
    _linearFallback() {
        let total = this.basePrice;
        this.el.querySelectorAll("input.ptav-input:checked").forEach((inp) => {
            total += parseFloat(inp.dataset.priceExtra || 0);
        });
        this.el.querySelectorAll("input.optional-input:checked").forEach((inp) => {
            total += parseFloat(inp.dataset.price || 0);
        });
        return total;
    },

    _setPrice(total) {
        const formatted = this._formatCurrency(total);
        this._priceDisplays.forEach((el) => {
            el.textContent = formatted;
        });
    },

    _animatePriceUpdate(total) {
        const formatted = this._formatCurrency(total);
        this._priceDisplays.forEach((el) => {
            el.classList.add("fade-out");
            setTimeout(() => {
                el.textContent = formatted;
                el.classList.remove("fade-out");
                el.classList.add("fade-in");
                setTimeout(() => el.classList.remove("fade-in"), 200);
            }, 150);
        });
    },

    _formatCurrency(amount) {
        // Format as TWD-style: NT$XX,XXX (no decimals)
        const rounded = Math.round(amount);
        return `${this.currencySymbol}${rounded.toLocaleString("en-US")}`;
    },

    // ─── Event handlers ──────────────────────────────

    _onPtavChange(ev) {
        const input = ev.currentTarget;
        const attrId = input.dataset.attributeId;
        this.el
            .querySelectorAll(`input.ptav-input[data-attribute-id="${attrId}"]`)
            .forEach((inp) => {
                const wrap = inp.closest(".form-selector") || inp.closest(".rc-card");
                if (wrap) wrap.classList.toggle("is-selected", inp.checked);
                if (wrap) wrap.classList.toggle("selected", inp.checked); // legacy
            });

        this._recalcPrice();
        this._refreshAvailability();

        if (this.colorAttrId && parseInt(input.dataset.attributeId) === this.colorAttrId) {
            const swatch = input.closest(".swatch");
            this._swapMainImage(swatch?.dataset.imageUrl);
            const colorLabel = this.el.querySelector(".active-color-name");
            if (colorLabel) colorLabel.textContent = input.dataset.displayName || "";
        }
    },

    _onOptionalChange(ev) {
        const wrap = ev.currentTarget.closest(".form-selector") ||
                     ev.currentTarget.closest(".rc-card");
        if (wrap) {
            wrap.classList.toggle("is-selected", ev.currentTarget.checked);
            wrap.classList.toggle("selected", ev.currentTarget.checked);
        }
        this._recalcPrice();
    },

    /**
     * Software toggle (FCP / Logic Pro): radio group within the same software_id.
     * Only the "yes please install" option contributes to price (its
     * input also has class `optional-input`); the "no thanks" option has 0.
     */
    _onSoftwareToggle(ev) {
        const input = ev.currentTarget;
        const groupName = input.name;
        this.el.querySelectorAll(`input[name="${groupName}"]`).forEach((r) => {
            const wrap = r.closest(".form-selector");
            if (wrap) wrap.classList.toggle("is-selected", r.checked);
        });
        this._recalcPrice();
    },

    /**
     * Trade-in radio: pure UI choice, no cart impact.
     * - Toggles .is-selected class on form-selector wrappers
     * - Expands/collapses .rf-tradeupinline-drawer when 加入換購 chosen
     */
    _onTradeinToggle(ev) {
        const input = ev.currentTarget;
        const groupName = input.name;
        this.el.querySelectorAll(`input[name="${groupName}"]`).forEach((r) => {
            const wrap = r.closest(".form-selector") || r.closest(".rc-card");
            if (wrap) wrap.classList.toggle("is-selected", r.checked);
        });
        const drawer = this.el.querySelector(".rf-tradeupinline-drawer");
        if (drawer) {
            const showDrawer = input.value === "join" && input.checked;
            if (showDrawer) {
                drawer.removeAttribute("hidden");
            } else {
                drawer.setAttribute("hidden", "hidden");
            }
        }
    },

    // ─── Laser Engraving ──────────────────────────
    _onLaserToggle(ev) {
        const input = ev.currentTarget;
        // update is-selected on all radio rows
        this.el.querySelectorAll('input[name="laser-engrave"]').forEach((r) => {
            const wrap = r.closest(".form-selector");
            if (wrap) wrap.classList.toggle("is-selected", r.checked);
        });
        const drawer = this.el.querySelector(".as-laser-drawer");
        if (!drawer) return;
        const show = input.value === "1" && input.checked;
        if (show) {
            drawer.removeAttribute("hidden");
            this._syncLaserPreviewColor();
            // focus first input
            const first = drawer.querySelector(".laser-input");
            if (first) first.focus();
        } else {
            drawer.setAttribute("hidden", "hidden");
            // clear inputs & preview when dismissed
            drawer.querySelectorAll(".laser-input").forEach((i) => { i.value = ""; });
            this._updateLaserPreview();
        }
    },

    _onEngravingInput(ev) {
        const input = ev.currentTarget;
        const field = input.closest(".as-laser-field");
        if (field) {
            const counter = field.querySelector(".engraving-count");
            if (counter) counter.textContent = [...input.value].length;
        }
        // Update inline SVG / span preview
        if (input.id === "pencil-engraving-input") {
            const svgText = this.el.querySelector("#pencil-preview-text");
            if (svgText) svgText.textContent = input.value;
        } else if (input.id === "ipad-engraving-input") {
            const span = this.el.querySelector("#ipad-preview-text");
            if (span) span.textContent = input.value;
        }
    },

    _onLaserInput(ev) {
        const input = ev.currentTarget;
        // update character counter
        const field = input.closest(".as-laser-field");
        if (field) {
            const counter = field.querySelector(".as-laser-count");
            if (counter) counter.textContent = [...input.value].length;
        }
        this._updateLaserPreview();
    },

    _updateLaserPreview() {
        const line1Input = this.el.querySelector("#laser-line1");
        const prev1 = this.el.querySelector(".as-laser-preview-line1");
        if (!prev1) return;
        const text1 = line1Input ? line1Input.value.trim() : "";
        prev1.textContent = text1;
    },

    _syncLaserPreviewColor() {
        const device = this.el.querySelector(".as-laser-preview-device");
        if (!device) return;
        // Find the active swatch's background-color
        const activeSwatch = this.el.querySelector(".swatch[aria-checked='true']");
        if (activeSwatch) {
            const bg = activeSwatch.style.backgroundColor;
            if (bg) {
                device.style.background = `radial-gradient(ellipse at 30% 30%, color-mix(in srgb, ${bg} 80%, #fff), color-mix(in srgb, ${bg} 50%, #fff))`;
                return;
            }
        }
        // fallback: light silver
        device.style.background = "";
    },

    _onSwatchClick(ev) {
        const swatch = ev.currentTarget;
        // Toggle aria-checked among siblings
        swatch.parentElement.querySelectorAll(".swatch").forEach((s) => {
            s.setAttribute("aria-checked", "false");
        });
        swatch.setAttribute("aria-checked", "true");
        this._syncLaserPreviewColor();

        // Find the matching ptav input and check it (this triggers price + image)
        const ptavId = swatch.dataset.ptavId;
        const input = this.el.querySelector(`input.ptav-input[data-ptav-id="${ptavId}"]`);
        if (input) {
            input.checked = true;
            input.dispatchEvent(new Event("change", { bubbles: true }));
        } else {
            // No PTAV input (color attribute might be on left only) — just swap image
            this._swapMainImage(swatch.dataset.imageUrl);
            const colorLabel = this.el.querySelector(".active-color-name");
            if (colorLabel) colorLabel.textContent = swatch.getAttribute("aria-label") || "";
        }
    },

    _swapMainImage(newSrc) {
        if (!this._mainImage || !newSrc) return;
        this._mainImage.classList.add("cross-fade-out");
        setTimeout(() => {
            this._mainImage.src = newSrc;
            this._mainImage.onload = () =>
                this._mainImage.classList.remove("cross-fade-out");
        }, 200);
    },

    _onCardKeyDown(ev) {
        // Arrow keys navigate within fieldset
        if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(ev.key))
            return;
        ev.preventDefault();
        const fieldset = ev.currentTarget.closest(".rc-dimension");
        if (!fieldset) return;
        const cards = Array.from(fieldset.querySelectorAll(".rc-card"));
        const idx = cards.indexOf(ev.currentTarget);
        const dir = ev.key === "ArrowUp" || ev.key === "ArrowLeft" ? -1 : 1;
        const next = cards[(idx + dir + cards.length) % cards.length];
        if (next) {
            next.focus();
            const input = next.querySelector("input");
            if (input && !input.disabled && input.type === "radio") {
                input.checked = true;
                input.dispatchEvent(new Event("change", { bubbles: true }));
            }
        }
    },

    _onHelpClick(ev) {
        ev.preventDefault();
        // Placeholder: in real impl we'd open a popover with apple_help_text
        console.log("Help requested for", ev.currentTarget.closest(".rc-dimension"));
    },

    // ─── Variant exclusion enforcement ───────────────

    _refreshAvailability() {
        const chosen = Array.from(
            this.el.querySelectorAll("input.ptav-input:checked")
        ).map((i) => parseInt(i.dataset.ptavId));

        this.el.querySelectorAll("input.ptav-input").forEach((inp) => {
            const id = parseInt(inp.dataset.ptavId);
            const exclusions = this._exclusionTable[id] || [];
            const isExcluded = exclusions.some((ex) => chosen.includes(ex));
            inp.disabled = isExcluded && !inp.checked;
            const card = inp.closest(".rc-card");
            if (card) card.classList.toggle("disabled", inp.disabled);
        });
    },

    // ─── Add to bag ──────────────────────────────────

    async _onAddToBag(ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        if (btn.disabled) return;
        btn.disabled = true;
        btn.classList.add("loading");

        try {
            const ptavIds = Array.from(
                this.el.querySelectorAll("input.ptav-input:checked")
            ).map((i) => parseInt(i.dataset.ptavId));

            const optionalIds = Array.from(
                this.el.querySelectorAll("input.optional-input:checked")
            ).map((i) => parseInt(i.dataset.productId));

            const pencilInput = this.el.querySelector("#pencil-engraving-input");
            const ipadInput = this.el.querySelector("#ipad-engraving-input");

            // Custom endpoint: server resolves dynamic variant from PTAV combo
            // and folds optional products into same sale.order
            const res = await rpc("/shop/buy-mac/cart/add", {
                product_template_id: this.productTmplId,
                product_template_attribute_value_ids: ptavIds,
                optional_product_ids: optionalIds,
                pencil_engraving_text: pencilInput ? pencilInput.value.trim() : null,
                ipad_engraving_text: ipadInput ? ipadInput.value.trim() : null,
            });

            if (res && res.error) {
                throw new Error(res.error);
            }

            this._showToast("已加入購物袋");
            this._openCartDrawer();
            window.dispatchEvent(
                new CustomEvent("apple-cart-updated", { detail: res })
            );
        } catch (e) {
            this._showToast(e.message || "加入失敗，請稍後再試", true);
        } finally {
            btn.disabled = false;
            btn.classList.remove("loading");
        }
    },

    _openCartDrawer() {
        const drawer = this.el.querySelector(".cart-drawer");
        const backdrop = this.el.querySelector(".drawer-backdrop");
        if (!drawer) return;
        drawer.removeAttribute("hidden");
        backdrop?.removeAttribute("hidden");
        // Force reflow before adding .open
        drawer.offsetHeight;
        drawer.classList.add("open");
        backdrop?.classList.add("open");
        // a11y: focus the close button when drawer opens
        const closeBtn = drawer.querySelector(".drawer-close");
        if (closeBtn) {
            setTimeout(() => closeBtn.focus(), 100);
        }
    },

    _showToast(message, isError) {
        const toast = document.createElement("div");
        toast.className = "apple-toast" + (isError ? " error" : "");
        toast.textContent = message;
        toast.setAttribute("role", "alert");
        this.el.appendChild(toast);
        toast.offsetHeight;
        toast.classList.add("show");
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    },
});
