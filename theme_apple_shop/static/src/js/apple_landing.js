/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AppleMacLandingCarousel = publicWidget.Widget.extend({
    selector: ".section-models",
    events: {
        "click .track-prev": "_onPrev",
        "click .track-next": "_onNext",
    },

    start() {
        this._track = this.el.querySelector(".models-track");
        return this._super(...arguments);
    },

    _scrollAmount() {
        const card = this._track && this._track.querySelector(".model-card");
        if (!card) return 300;
        const style = getComputedStyle(this._track);
        const gap = parseFloat(style.gap) || 16;
        return card.offsetWidth + gap;
    },

    _onPrev() {
        if (!this._track) return;
        this._track.scrollBy({ left: -this._scrollAmount(), behavior: "smooth" });
    },

    _onNext() {
        if (!this._track) return;
        this._track.scrollBy({ left: this._scrollAmount(), behavior: "smooth" });
    },
});
