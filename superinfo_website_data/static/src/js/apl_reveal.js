/* 蘋果培訓系列頁面：捲動淡入／滑入動畫還原（page-agnostic）
 *
 * 原站每頁各自內嵌 scroll-reveal script，會對 .section / .fade-in / .animate-* /
 * slide-in 等元素設初始 opacity:0，再由 observer 加上 visible/active/animate-in
 * 類別顯示。移植到 Odoo 後統一由此一支共用檔處理，並做「保險全顯示」：
 * 任何最終仍 computed opacity:0 的元素一律強制顯示，確保內容絕不會卡在隱形狀態。 */
(function () {
    "use strict";

    var REVEAL_CLASSES = ["visible", "active", "animate-in"];

    function revealEl(el) {
        for (var i = 0; i < REVEAL_CLASSES.length; i++) {
            el.classList.add(REVEAL_CLASSES[i]);
        }
    }

    function isHidden(el) {
        var cs = window.getComputedStyle(el);
        if (cs.display === "none" || cs.visibility === "hidden") {
            return false; // 由 display/visibility 控制者（如分頁面板）不在處理範圍
        }
        return parseFloat(cs.opacity) === 0;
    }

    function forceShow(el) {
        var cs = window.getComputedStyle(el);
        if (parseFloat(cs.opacity) === 0) {
            el.style.opacity = "1";
        }
        if (cs.transform && cs.transform !== "none") {
            el.style.transform = "none";
        }
    }

    function collectHidden() {
        var res = [];
        var nodes = document.querySelectorAll(".si-apl-page *");
        for (var i = 0; i < nodes.length; i++) {
            if (isHidden(nodes[i])) {
                res.push(nodes[i]);
            }
        }
        return res;
    }

    function init() {
        if (!document.querySelector(".si-apl-page")) {
            return;
        }
        // 候選 = 明確的動畫類別 ∪ 初始 computed opacity:0 的元素
        var explicit = [].slice.call(document.querySelectorAll(
            '.si-apl-page .fade-in, .si-apl-page [class*="animate-"], .si-apl-page [class*="slide-in"]'
        ));
        var candidates = explicit.slice();
        var hidden = collectHidden();
        for (var i = 0; i < hidden.length; i++) {
            if (candidates.indexOf(hidden[i]) === -1) {
                candidates.push(hidden[i]);
            }
        }
        if (!candidates.length) {
            return;
        }

        if (!("IntersectionObserver" in window)) {
            candidates.forEach(function (el) { revealEl(el); forceShow(el); });
            return;
        }

        var obs = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    revealEl(e.target);
                    obs.unobserve(e.target);
                }
            });
        }, { threshold: 0.05, rootMargin: "0px 0px -8% 0px" });

        candidates.forEach(function (el) { obs.observe(el); });

        // 保險：2 秒後全部標記為已顯示，再對仍隱形者強制顯示
        window.setTimeout(function () {
            candidates.forEach(revealEl);
            window.setTimeout(function () {
                collectHidden().forEach(forceShow);
            }, 200);
        }, 2000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
