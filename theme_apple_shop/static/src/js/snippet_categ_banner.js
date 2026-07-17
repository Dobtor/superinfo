/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CategBanner = publicWidget.Widget.extend({
    selector: '.s_categ_banner',
    disabledInEditableMode: true,

    _detectCategId() {
        // Explicit override set via the editor's "指定分類" picker (on the
        // outer section) takes priority.
        const explicit = this.el.dataset.categId;
        if (explicit && explicit !== '0') return explicit;
        // Otherwise auto-detect from /shop/category/<slug>-<id> URL pattern
        // — matches the banner to whatever category page it's shown on.
        const match = window.location.pathname.match(/\/shop\/category\/[^/]+-(\d+)/);
        if (match) return match[1];
        return '0';
    },

    start() {
        const wrapper = this.el.querySelector('.categ-banner-wrapper');
        if (!wrapper) return this._super(...arguments);
        const categId = this._detectCategId();
        fetch(`/theme_apple_shop/snippet/categ_banner?categ_id=${categId}`)
            .then(r => r.text())
            .then(html => { wrapper.innerHTML = html; });
        return this._super(...arguments);
    },
});
