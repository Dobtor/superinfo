/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

// Shared across modules: matched by .s_categ_nav_photo (every category-photo-
// nav snippet template carries this class, e.g. custom_homepage's own
// s_homepage_categ_nav_photo), not just this theme's own snippet.
publicWidget.registry.CategNavPhoto = publicWidget.Widget.extend({
    selector: '.s_categ_nav_photo',
    disabledInEditableMode: true,

    start() {
        const wrapper = this.el.querySelector('.categ-nav-wrapper');
        if (!wrapper) return this._super(...arguments);
        // Set via the editor's "顯示分類" checklist (on the outer section);
        // empty means "show all top-level categories" (default).
        const categIds = this.el.dataset.categIds || '';
        fetch(`/theme_apple_shop/snippet/categ_nav_photo?categ_ids=${categIds}`)
            .then(r => r.text())
            .then(html => { wrapper.innerHTML = html; });
        return this._super(...arguments);
    },
});
