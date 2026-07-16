/** @odoo-module **/
import options from "@web_editor/js/editor/snippets.options";

options.registry.ProductSwiperCategory = options.Class.extend({
    /**
     * Stores the picked product.public.category id on the section, read by
     * snippet_product_swiper.js at render time.
     */
    setCategId(previewMode, widgetValue) {
        this.$target[0].dataset.categId = widgetValue || '0';
    },

    /**
     * @override
     */
    _computeWidgetState(methodName, params) {
        if (methodName === 'setCategId') {
            return this.$target[0].dataset.categId || '';
        }
        return this._super(...arguments);
    },
});

export default {
    ProductSwiperCategory: options.registry.ProductSwiperCategory,
};
