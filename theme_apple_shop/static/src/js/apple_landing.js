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
        this._scrollbar = this.el.querySelector(".models-scrollbar");
        this._thumb = this.el.querySelector(".models-scrollbar-thumb");

        if (this._track && this._thumb) {
            // Scroll → move thumb
            this._onScroll = this._syncThumb.bind(this);
            this._track.addEventListener("scroll", this._onScroll, { passive: true });

            // Click on track bar (not thumb) → jump scroll
            this._scrollbar.addEventListener("click", this._onBarClick.bind(this));

            // Drag thumb
            this._thumb.addEventListener("mousedown", this._onThumbMousedown.bind(this));
            this._thumb.addEventListener("touchstart", this._onThumbTouchstart.bind(this), { passive: true });

            // Initial state
            this._syncThumb();
        }

        return this._super(...arguments);
    },

    destroy() {
        if (this._track && this._onScroll) {
            this._track.removeEventListener("scroll", this._onScroll);
        }
        this._super(...arguments);
    },

    // ─── Scroll amount per arrow click ────────────────
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

    // ─── Scrollbar sync ───────────────────────────────
    _syncThumb() {
        if (!this._track || !this._thumb || !this._scrollbar) return;

        const scrollMax = this._track.scrollWidth - this._track.clientWidth;
        if (scrollMax <= 0) {
            // All cards fit — hide the scrollbar
            this._scrollbar.style.display = "none";
            return;
        }

        this._scrollbar.style.display = "";

        const barW = this._scrollbar.offsetWidth;
        // Thumb width proportional to visible / total
        const ratio = this._track.clientWidth / this._track.scrollWidth;
        const thumbW = Math.max(40, Math.round(barW * ratio));
        this._thumb.style.width = thumbW + "px";

        // Thumb position
        const scrollRatio = this._track.scrollLeft / scrollMax;
        const maxLeft = barW - thumbW;
        this._thumb.style.left = Math.round(scrollRatio * maxLeft) + "px";
    },

    // ─── Click on bar (not thumb) → jump ──────────────
    _onBarClick(e) {
        if (e.target === this._thumb) return;
        const rect = this._scrollbar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const thumbW = this._thumb.offsetWidth;
        const barW = this._scrollbar.offsetWidth;
        const targetLeft = Math.max(0, Math.min(clickX - thumbW / 2, barW - thumbW));
        const scrollMax = this._track.scrollWidth - this._track.clientWidth;
        this._track.scrollTo({
            left: (targetLeft / (barW - thumbW)) * scrollMax,
            behavior: "smooth",
        });
    },

    // ─── Mouse drag ───────────────────────────────────
    _onThumbMousedown(e) {
        e.preventDefault();
        const startX = e.clientX;
        const startLeft = this._thumb.offsetLeft;
        const barW = this._scrollbar.offsetWidth;
        const thumbW = this._thumb.offsetWidth;
        const scrollMax = this._track.scrollWidth - this._track.clientWidth;

        this._thumb.classList.add("dragging");

        const onMove = (mv) => {
            const dx = mv.clientX - startX;
            const maxLeft = barW - thumbW;
            const newLeft = Math.max(0, Math.min(startLeft + dx, maxLeft));
            this._thumb.style.left = newLeft + "px";
            this._track.scrollLeft = (newLeft / maxLeft) * scrollMax;
        };
        const onUp = () => {
            this._thumb.classList.remove("dragging");
            document.removeEventListener("mousemove", onMove);
            document.removeEventListener("mouseup", onUp);
        };
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
    },

    // ─── Touch drag ───────────────────────────────────
    _onThumbTouchstart(e) {
        const startX = e.touches[0].clientX;
        const startLeft = this._thumb.offsetLeft;
        const barW = this._scrollbar.offsetWidth;
        const thumbW = this._thumb.offsetWidth;
        const scrollMax = this._track.scrollWidth - this._track.clientWidth;

        this._thumb.classList.add("dragging");

        const onMove = (mv) => {
            const dx = mv.touches[0].clientX - startX;
            const maxLeft = barW - thumbW;
            const newLeft = Math.max(0, Math.min(startLeft + dx, maxLeft));
            this._thumb.style.left = newLeft + "px";
            this._track.scrollLeft = (newLeft / maxLeft) * scrollMax;
        };
        const onEnd = () => {
            this._thumb.classList.remove("dragging");
            this._thumb.removeEventListener("touchmove", onMove);
            this._thumb.removeEventListener("touchend", onEnd);
        };
        this._thumb.addEventListener("touchmove", onMove, { passive: true });
        this._thumb.addEventListener("touchend", onEnd);
    },
});
