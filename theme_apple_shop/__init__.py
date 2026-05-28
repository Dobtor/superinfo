# -*- coding: utf-8 -*-
import logging

from . import controllers
from . import models

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Run asset sync + PTAV pricing setup once on first install.

    Replaces the previous <function/> calls in data/post_install.xml,
    which were fragile under Odoo 18's call_kw semantics. A Python hook
    runs in the same install transaction but isolates exceptions:
    if the asset manifest is missing or any image is malformed, the
    module still installs cleanly.
    """
    # 1. Force-delete cached asset bundles so the next request recompiles
    #    and includes our SCSS/JS. Without this, Cloudflare (cache-control:
    #    immutable, max-age=1y) keeps serving the pre-install bundle URL
    #    forever — even after the module is properly installed.
    try:
        attachments = env['ir.attachment'].sudo().search([
            ('name', '=like', 'web.assets_%'),
        ])
        n = len(attachments)
        attachments.unlink()
        _logger.info("apple shop: invalidated %s cached asset bundles", n)
    except Exception as e:
        _logger.warning("apple asset bundle invalidation failed: %s", e)

    Template = env['product.template'].sudo()
    try:
        Template._sync_apple_assets_from_manifest()
    except Exception as e:
        _logger.warning("apple asset sync skipped: %s", e)
    try:
        Template._setup_apple_price_extras()
    except Exception as e:
        _logger.warning("apple price_extra setup skipped: %s", e)
