/** @odoo-module **/
import { registry } from "@web/core/registry";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AppleCategCarousel = publicWidget.Widget.extend({
    selector: '.s_apple_categ_carousel',
    disabledInEditableMode: true,

    _detectCategId(wrapper) {
        // Explicit override on the element takes priority
        const explicit = wrapper.dataset.categId;
        if (explicit && explicit !== '0') return explicit;
        // Auto-detect from /shop/category/<slug>-<id> URL pattern
        const match = window.location.pathname.match(/\/shop\/category\/[^/]+-(\d+)/);
        if (match) return match[1];
        return '0';
    },

    start() {
        const wrapper = this.el.querySelector('.apple-categ-carousel-wrapper');
        if (!wrapper) return this._super(...arguments);
        const categId = this._detectCategId(wrapper);
        fetch(`/theme_apple_shop/snippet/categ_carousel?categ_id=${categId}`)
            .then(r => r.text())
            .then(html => {
                wrapper.innerHTML = html;
                this._initCarousel();
            });
        return this._super(...arguments);
    },

    _initCarousel() {
        const track = this.el.querySelector('.models-track');
        const prevBtn = this.el.querySelector('.track-prev');
        const nextBtn = this.el.querySelector('.track-next');
        const thumb = this.el.querySelector('.models-scrollbar-thumb');
        const bar = this.el.querySelector('.models-scrollbar');

        if (!track) return;

        const syncThumb = () => {
            if (!thumb || !bar) return;
            const ratio = track.scrollWidth > track.clientWidth
                ? track.clientWidth / track.scrollWidth : 1;
            if (ratio >= 1) { bar.style.display = 'none'; return; }
            bar.style.display = '';
            thumb.style.width = (ratio * 100) + '%';
            thumb.style.left = (track.scrollLeft / track.scrollWidth * 100) + '%';
        };

        track.addEventListener('scroll', syncThumb);
        syncThumb();

        if (prevBtn) prevBtn.addEventListener('click', () =>
            track.scrollBy({ left: -320, behavior: 'smooth' }));
        if (nextBtn) nextBtn.addEventListener('click', () =>
            track.scrollBy({ left: 320, behavior: 'smooth' }));

        if (thumb && bar) {
            let dragging = false, startX = 0, startScroll = 0;
            thumb.addEventListener('mousedown', e => {
                dragging = true; startX = e.clientX;
                startScroll = track.scrollLeft;
                thumb.classList.add('dragging');
            });
            document.addEventListener('mousemove', e => {
                if (!dragging) return;
                const dx = e.clientX - startX;
                track.scrollLeft = startScroll + dx * (track.scrollWidth / bar.clientWidth);
            });
            document.addEventListener('mouseup', () => {
                dragging = false; thumb.classList.remove('dragging');
            });
        }
    },
});
