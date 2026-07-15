/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

// Shared across modules: matched by .s_product_swiper (every product-swiper
// snippet template carries this class, e.g. custom_homepage's own
// s_homepage_product_swiper), not just this theme's own snippet.
publicWidget.registry.ProductSwiper = publicWidget.Widget.extend({
    selector: '.s_product_swiper',
    disabledInEditableMode: true,

    _detectCategId() {
        // Explicit override set via the editor's "商品分類" picker (on the
        // outer section, same as slidesPerView/delay) takes priority.
        const explicit = this.el.dataset.categId;
        if (explicit && explicit !== '0') return explicit;
        // Otherwise auto-detect from /shop/category/<slug>-<id> URL pattern
        const match = window.location.pathname.match(/\/shop\/category\/[^/]+-(\d+)/);
        if (match) return match[1];
        return '0';
    },

    start() {
        const wrapper = this.el.querySelector('.product-swiper-wrapper');
        if (!wrapper) return this._super(...arguments);
        const categId = this._detectCategId();
        fetch(`/theme_apple_shop/snippet/product_swiper?categ_id=${categId}`)
            .then(r => r.text())
            .then(html => {
                wrapper.innerHTML = html;
                this._initSwiper(wrapper);
            });
        return this._super(...arguments);
    },

    _initSwiper(wrapper) {
        const swiperEl = wrapper.querySelector('.product-swiper');
        if (!swiperEl || !window.Swiper) return;
        // Slide Per View / Delay are set via the editor options panel on the
        // outer .s_product_swiper section (this.el), not on the wrapper.
        const slidesPerView = parseInt(this.el.dataset.slidesPerView) || 4;
        const delay = parseInt(this.el.dataset.delay);
        this._swiper = new window.Swiper(swiperEl, {
            slidesPerView: 'auto',
            spaceBetween: 16,
            navigation: {
                nextEl: wrapper.querySelector('.swiper-button-next'),
                prevEl: wrapper.querySelector('.swiper-button-prev'),
            },
            breakpoints: {
                991: {
                    slidesPerView: slidesPerView,
                },
            },
            ...(delay ? {
                autoplay: {
                    delay: delay,
                    disableOnInteraction: false,
                    pauseOnMouseEnter: true,
                },
            } : {}),
        });
    },

    /**
     * @override
     */
    destroy() {
        // Swiper attaches touch/pointer listeners directly on the fetched
        // slides; without tearing it down, those listeners keep intercepting
        // clicks (swallowing them before the editor's snippet-select handler
        // sees them) once the page goes into edit mode. Only release the
        // Swiper instance here — leave the fetched markup in place, since
        // disabledInEditableMode means start() won't run again to rebuild it.
        if (this._swiper) {
            this._swiper.destroy(true, true);
            this._swiper = undefined;
        }
        this._super(...arguments);
    },
});
