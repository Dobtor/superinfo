/* 蘋果培訓系列頁面：捲動淡入動畫（復刻原站 .fade-in 行為）
 * 原站每頁各自內嵌 IntersectionObserver script，移植到 Odoo 後統一由此一支共用檔處理。
 * 任何 .si-apl-page .fade-in 進入視窗即加上 .visible；
 * 並在載入後做保險全顯示，確保即使 observer 失效內容也不會卡在 opacity:0。 */
(function () {
    "use strict";

    function revealAll(root) {
        (root || document).querySelectorAll(".si-apl-page .fade-in").forEach(function (el) {
            el.classList.add("visible");
        });
    }

    function init() {
        var nodes = document.querySelectorAll(".si-apl-page .fade-in");
        if (!nodes.length) {
            return;
        }
        if (!("IntersectionObserver" in window)) {
            revealAll();
            return;
        }
        var obs = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add("visible");
                    obs.unobserve(e.target);
                }
            });
        }, { threshold: 0.1, rootMargin: "0px 0px -40px 0px" });
        nodes.forEach(function (el) { obs.observe(el); });
        // 保險：3 秒後仍未顯示者一律顯示（避免內容卡在隱藏狀態）
        window.setTimeout(revealAll, 3000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
