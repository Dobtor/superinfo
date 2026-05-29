/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Compare table — adds optional sticky behaviour for table head when scrolled.
 * Currently a no-op placeholder; the table itself is server-rendered.
 */
publicWidget.registry.AppleCompareTable = publicWidget.Widget.extend({
    selector: ".apple-configurator .config-compare",

    start() {
        return this._super(...arguments);
    },
});
