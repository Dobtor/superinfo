/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Image stage + thumbnail row coordinator.
 *
 * Click thumb → swap main image (cross-fade)
 * Hover thumb → preview swap (optional)
 */
publicWidget.registry.AppleImageCarousel = publicWidget.Widget.extend({
    selector: ".apple-configurator .config-image-area",
    events: {
        "click .thumb": "_onThumbClick",
        "mouseenter .thumb": "_onThumbHover",
    },

    start() {
        this._mainImage = this.el.querySelector(".main-image");
        return this._super(...arguments);
    },

    _swap(newSrc) {
        if (!this._mainImage || !newSrc) return;
        if (this._mainImage.src.endsWith(newSrc)) return;
        this._mainImage.classList.add("cross-fade-out");
        setTimeout(() => {
            this._mainImage.src = newSrc;
            this._mainImage.onload = () =>
                this._mainImage.classList.remove("cross-fade-out");
        }, 180);
    },

    _onThumbClick(ev) {
        const thumb = ev.currentTarget;
        this.el.querySelectorAll(".thumb").forEach((t) => t.classList.remove("active"));
        thumb.classList.add("active");
        const url = thumb.dataset.imageUrl || thumb.querySelector("img")?.src;
        this._swap(url);
    },

    _onThumbHover(ev) {
        // Optional: preview hover swap. Disabled by default to avoid jank.
    },
});
