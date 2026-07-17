/** @odoo-module **/
import options from "@web_editor/js/editor/snippets.options";

// Shared: data-selector targets .s_categ_nav (this theme's own snippet and
// custom_homepage's), so this single registration covers every module's
// instance — see snippet_categ_nav.js which reads the resulting data-categ-ids.
options.registry.CategNavSelect = options.Class.extend({
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },

    /**
     * @override
     */
    async _renderCustomXML(uiFragment) {
        this.categories = await this.orm.searchRead(
            'product.public.category',
            [['parent_id', '=', false]],
            ['id', 'name'],
            { order: 'sequence, id' },
        );
        for (const categ of this.categories) {
            const checkboxEl = document.createElement('we-checkbox');
            checkboxEl.setAttribute('string', categ.name);
            checkboxEl.dataset.toggleCateg = String(categ.id);
            checkboxEl.dataset.categId = String(categ.id);
            checkboxEl.dataset.noPreview = 'true';
            uiFragment.appendChild(checkboxEl);
        }
    },

    /**
     * Adds/removes params.categId from the section's stored data-categ-ids
     * list. Empty widgetValue means this checkbox was just unchecked.
     */
    toggleCateg(previewMode, widgetValue, params) {
        const categId = parseInt(params.categId);
        const current = this._getSelectedIds();
        const next = widgetValue
            ? (current.includes(categId) ? current : [...current, categId])
            : current.filter((id) => id !== categId);
        this.$target[0].dataset.categIds = next.join(',');
    },

    /**
     * data-categ-ids unset/empty means "never customised" — the first 3
     * categories count as shown (matches the controller's own default,
     * see snippet_categ_nav in controllers/main.py).
     */
    _getSelectedIds() {
        const raw = this.$target[0].dataset.categIds;
        if (!raw) {
            return (this.categories || []).slice(0, 3).map((c) => c.id);
        }
        return raw.split(',').filter(Boolean).map(Number);
    },

    /**
     * @override
     */
    _computeWidgetState(methodName, params) {
        if (methodName === 'toggleCateg') {
            const categId = parseInt(params.categId);
            return this._getSelectedIds().includes(categId) ? String(categId) : '';
        }
        return this._super(...arguments);
    },
});

export default {
    CategNavSelect: options.registry.CategNavSelect,
};
