#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_apple_assets.py
---------------------
Demo asset fetcher for theme_apple_shop. Downloads category card images
for the 8 Mac models from Apple's CDN.

URLs are extracted live from www.apple.com/tw/shop/buy-mac (Apple's CDN
URLs include hashes that change on each marketing-page rebuild — the
list below is captured 2026-05-04). Re-run this script when URLs go 404
to refresh the manifest.

DEMO ONLY — replace these with your own licensed product photography
before going to production.

Standard library only.

Usage:
  python3 tools/fetch_apple_assets.py            # download
  python3 tools/fetch_apple_assets.py --dry-run  # preview only
  python3 tools/fetch_apple_assets.py --force    # re-download existing
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15"
REFERER = "https://www.apple.com/tw/"

REPO_ROOT = Path(__file__).resolve().parent.parent
MAC_DIR = REPO_ROOT / "static" / "src" / "img" / "mac"
SITE_DIR = REPO_ROOT / "static" / "src" / "img" / "site"
MANIFEST = Path(__file__).resolve().parent / "apple_assets_manifest.json"

# Live URLs captured from www.apple.com/tw/shop/buy-mac (2026-05-04).
# Each Mac model has:
#   - card_url:  680x528 card image used on landing carousel
#   - main_url:  configurator hero image (where available)
MAC_ASSETS = {
    "macbook-neo": {
        "category_xml_id": "superinfo_website_data.categ_macbook_neo",
        "product_xml_id":  "theme_apple_shop.prod_macbook_neo",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-macbook-neo-202603?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=dzRRdVl2UHpmd3BrL2dpaGRDY2RKOFVIc0pMamhtQTdJT2hNaXc2a1F5UWw2T29GWFRmcGlRaHRKa2ZZeG54SDRHeXB5TnVsU3R6Qjd0Y2JzbURyWEVFbjlJVU41dmw4QVZJN1dUaHpNY0IrYWpGdS9XeFgvbS9ITnNYOEhYaG4",
    },
    "macbook-air": {
        "category_xml_id": "superinfo_website_data.categ_macbook_air",
        "product_xml_id":  "theme_apple_shop.prod_macbook_air",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-macbook-air-202503?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=dzRRdVl2UHpmd3BrL2dpaGRDY2RKN3dnWXpNRUFSbE1veTFaYXZqWDhWZ2w2T29GWFRmcGlRaHRKa2ZZeG54SDRHeXB5TnVsU3R6Qjd0Y2JzbURyWE56dkQ1M2pkMXloY0FLTkxsc2xNQXArYWpGdS9XeFgvbS9ITnNYOEhYaG4",
    },
    "macbook-pro": {
        "category_xml_id": "superinfo_website_data.categ_macbook_pro",
        "product_xml_id":  "theme_apple_shop.prod_macbook_pro",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-macbookpro-14-16-202410?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=dzRRdVl2UHpmd3BrL2dpaGRDY2RKL0tDcDdIN2J5MlRJbDZwdXNUam1wUDJ0SUdrYS9VNndoSUR6SjE2NTZ4Q3dzUlMrL0tMOEdKdERZZEhaV2pBNG5MYXhobkxkNHkydGdPaXdJd0ZJRmorbGwzUVNwZEFpcE1WQU1wNTVjU1c",
    },
    "imac": {
        "category_xml_id": "superinfo_website_data.categ_imac",
        "product_xml_id":  "theme_apple_shop.prod_imac",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-imac-202410?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=SXh2aE4zRm53L0l3NnhGK2wwZFpEeVFpZGxOY0d3emNHMmh4SnZVS1l0QTJzUm9kdjFCbFNETWhUL0NFUjdrYVJRTDhjbFg1ZXlSYWo3eW5aZUZxQjJvbklDSjVXM0pQY3RiODY0MDI2aUU",
    },
    "mac-mini": {
        "category_xml_id": "superinfo_website_data.categ_mac_mini",
        "product_xml_id":  "theme_apple_shop.prod_mac_mini",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-mac-mini-202410?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=MEl2WkNZRmkzTGhzejQ0SHE3b3FoNnQrZHdkUkkvM25CYTVJYWJQRk41QkMxQXc4S3pBZE5lUDJlTzVYSUYydFMwV0hhcmdVdXZzZ1NwTlFUaEgwTCthSGMrTVBBVlNQbW04TUlaTnlZU3c",
        "main_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-mini-chip-unselect-202601-gallery-1?wid=2880&hei=1845&fmt=p-jpg&qlt=80&.v=d1pXNGRPZVVoYmlPOFhNR3g4R2wxUGFyNWMrRXhVOURuN2tLWDJRa3lPaVFmZjd5T2R4eGRzZEl3a0hpNytPUUxNckZKekhaNGVhZVQvMTRuMXRSYTJ1Y0hhYzFCK0tzV3gwSFNTUHQzNHVYcWVvOFpHTzVHZHNZN2w4d2J4WVE",
    },
    "mac-studio": {
        "category_xml_id": "superinfo_website_data.categ_mac_studio",
        "product_xml_id":  "theme_apple_shop.prod_mac_studio",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-mac-studio-202503?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=MEl2WkNZRmkzTGhzejQ0SHE3b3FoeEhISXFsMjRaY2x5ZFpwbkptTldIN0RiOENhazh5Y0NacmRZMFN0dVNvZzJTaS9RTTYzTWg5VUhTM1Ara0JyS08zTzhSOUpOUnhYSEV2M3k5UWRwZkk",
    },
    "studio-display": {
        "category_xml_id": "superinfo_website_data.categ_studio_display",
        "product_xml_id":  "theme_apple_shop.prod_studio_display",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-studio-display-202603?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=dVp4cllZZXF6dklEWE1MaXJrMFFsWFE1bTY0LzdtNW13TjROaDVzaTdQTGZPOGdzbXFQKzNyOVN3L2NRSHJCNStFVlF6ZkRtZVJkbnBuR0wwNDgvSnJUbWtka3BEcEp5UWppL0FrTWlvRnQ5c2RrS21IU0RNY2daemxkbzhtY2M",
    },
    "studio-display-xdr": {
        "category_xml_id": "superinfo_website_data.categ_studio_display_xdr",
        "product_xml_id":  "theme_apple_shop.prod_studio_display_xdr",
        "card_url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-card-40-pro-display-202603?wid=680&hei=528&fmt=p-jpg&qlt=95&.v=UlltQkFYZW9PUVNxbGJESDBPdnR0S0c1aUV5YzRFYjJ5VHRxWllYQ2k3WWw2T29GWFRmcGlRaHRKa2ZZeG54SDRHeXB5TnVsU3R6Qjd0Y2JzbURyWEtUTXBibU9zRFdXcHBDby8xSEhEalIrYWpGdS9XeFgvbS9ITnNYOEhYaG4",
    },
}


ACCESSORY_ASSETS = {
    "magic_mouse": {
        "xml_id": "theme_apple_shop.prod_magic_mouse",
        "url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/MXK53?wid=890&hei=890&fmt=jpeg&qlt=90&.v=ZEl0L1RBWDFxdlRkZDBKUUlMQkVyWXExblZJSGFXSFVPMUE2c2RxMy8rTGhtOWE0YThxS1czK3JNYk5zY1dEQ21EZzNTUEF2RlJVTW05L3NQakl1L2c",
    },
    "magic_trackpad": {
        "xml_id": "theme_apple_shop.prod_magic_trackpad",
        "url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/MXK93?wid=890&hei=890&fmt=jpeg&qlt=90&.v=NitOQjNDc3ArZHEvd1E5QjFMMHArNHExblZJSGFXSFVPMUE2c2RxMy8rTGhtOWE0YThxS1czK3JNYk5zY1dEQ3I3SjhkazlaS0pJWmdudUxzVVNvSnc",
    },
    "magic_keyboard": {
        "xml_id": "theme_apple_shop.prod_magic_keyboard",
        "url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/MXCL3TA?wid=890&hei=890&fmt=jpeg&qlt=90&.v=eHNMT3JLQSs2RlR2SFNYL3JLWHR0MVhxaUMzRlo5aXdFdHpaYUhWcDUzdkpwRVBaWGpMb01kenNCVFZ1cktQc1JTUUVSMWJmbThhN2ZhMlRpR0RVclE",
    },
    "magic_keyboard_touchid": {
        "xml_id": "theme_apple_shop.prod_magic_keyboard_touchid",
        "url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/MXK73TA?wid=890&hei=890&fmt=jpeg&qlt=90&.v=WXRlUXFEMTlUdUhOUFEyUXZBZGxtbFhxaUMzRlo5aXdFdHpaYUhWcDUzdml3aWh6dythYVFkQzRrNHNQcUNsVk9GcktMQ3JxaWZHQXBQKzlvSjNEUEE",
    },
    "final_cut_pro": {
        "xml_id": "theme_apple_shop.prod_final_cut_pro",
        "url": "https://www.apple.com/v/final-cut-pro/w/images/overview/welcome/hero_endframe__r3cnyk748duq_large.jpg",
    },
    "logic_pro": {
        "xml_id": "theme_apple_shop.prod_logic_pro",
        "url": "https://www.apple.com/v/logic-pro/n/images/overview/welcome/hero_endframe__dc7irycb3gia_large.jpg",
    },
    "applecare": {
        "xml_id": "theme_apple_shop.prod_applecare_mac",
        "url": "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/mac-alp-applecare-plus-202603?wid=1220&hei=410&fmt=jpeg&qlt=90&.v=Uk1PMlhZeW5BYXBQTUwwdGE2a3EzcWJTWW1wYWJzNHZ1cmZUVTdDTFRQclM2S3ZwQmdzU3NBSjJQQWs5b2V1d3ZvdUZlR0V0VUdJSjBWaDVNVG95Yk1NM2tzTG5QZ3ZMOGZXYVppeUdSVkE",
    },
}


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": REFERER, "Accept": "image/*,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download(url, dest, dry_run=False, force=False):
    if not url:
        return False, "no url"
    if dest.exists() and not force:
        return False, "skip-existing"
    if dry_run:
        return True, "dry-run"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = http_get(url)
        if len(data) < 1024:
            return False, f"too small ({len(data)} bytes)"
        dest.write_bytes(data)
        return True, f"{len(data)} bytes"
    except Exception as e:
        return False, f"ERROR {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    print(f"[1/3] downloading {len(MAC_ASSETS)} Mac model card images ...")
    manifest = {"mac_categories": {}, "mac_products": {},
                "accessories": {}, "color_swatches": {}}

    for slug, info in MAC_ASSETS.items():
        # Download card image (used for both category hero and product image_1920)
        dest = MAC_DIR / slug / "card.jpg"
        ok, msg = download(info["card_url"], dest, args.dry_run, args.force)
        print(f"  {slug:<22} card: {msg}")

        rel = str(dest.relative_to(REPO_ROOT)) if dest.exists() else None

        manifest["mac_categories"][slug] = {
            "xml_id": info["category_xml_id"],
            "hero": rel,
        }
        manifest["mac_products"][slug] = {
            "xml_id": info["product_xml_id"],
            "image_1920": rel,
        }

        # Download larger main image (configurator hero) when available
        if info.get("main_url"):
            main_dest = MAC_DIR / slug / "main.jpg"
            ok2, msg2 = download(info["main_url"], main_dest, args.dry_run, args.force)
            print(f"  {slug:<22} main: {msg2}")
            if main_dest.exists():
                # Prefer the bigger main image for image_1920
                manifest["mac_products"][slug]["image_1920"] = str(
                    main_dest.relative_to(REPO_ROOT)
                )

    print(f"\n[2/3] downloading {len(ACCESSORY_ASSETS)} accessory images ...")
    acc_dir = REPO_ROOT / "static" / "src" / "img" / "accessories"
    for slug, info in ACCESSORY_ASSETS.items():
        ext = ".jpg" if "jpg" in info["url"].split("?")[0] or "jpeg" in info["url"] else ".png"
        # Use jpg by default; FCP/Logic are .jpg from URL path
        if "/v/" in info["url"]:
            ext = ".jpg"
        dest = acc_dir / f"{slug}{ext}"
        ok, msg = download(info["url"], dest, args.dry_run, args.force)
        print(f"  {slug:<28} {msg}")
        if dest.exists():
            manifest["accessories"][slug] = {
                "xml_id": info["xml_id"],
                "image_1920": str(dest.relative_to(REPO_ROOT)),
            }

    if not args.dry_run:
        MANIFEST.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n[3/3] manifest written: {MANIFEST}")
    else:
        print("\n[dry-run] no files written")


if __name__ == "__main__":
    sys.exit(main() or 0)
