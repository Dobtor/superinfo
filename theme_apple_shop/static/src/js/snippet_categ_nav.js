/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AppleCategNav = publicWidget.Widget.extend({
    selector: '.s_apple_categ_nav',
    disabledInEditableMode: true,

    start() {
        const wrapper = this.el.querySelector('.apple-categ-nav-wrapper');
        if (!wrapper) return this._super(...arguments);
        fetch('/theme_apple_shop/snippet/categ_nav')
            .then(r => r.text())
            .then(html => { wrapper.innerHTML = html; });
        return this._super(...arguments);
    },
});
