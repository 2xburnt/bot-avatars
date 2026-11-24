"""Per-bot Slack identity on the shared Slack app.

Profiles routed to their own channel (``gateway.profile_routes``) share the default profile's
Slack app. This plugin makes every ``chat.postMessage`` into such a channel carry that
profile's ``username`` and ``icon_url`` (needs the ``chat:write.customize`` scope), so each
bot looks like itself. Message edits keep the identity Slack stored with the original post.

Settings (``plugins.entries.slack-identity.settings``)::

    profiles:
      burntsentry: {username: BurntSentry, icon_url: https://.../burntsentry.png}

A post that already sets ``username`` or ``icon_url`` / ``icon_emoji`` is left alone, as is any
channel without an enabled slack route to a listed profile.
"""
from __future__ import annotations

import functools
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PATCH_FLAG = "_slack_identity_patched"
_STATE: dict[str, Any] = {"profiles": {}, "routes": {}, "mtime": None, "path": None}


def _config_path() -> Path:
    from hermes_constants import get_default_hermes_root
    return Path(os.environ.get("HERMES_HOME") or get_default_hermes_root()) / "config.yaml"


def _routes() -> dict[str, str]:
    """channel id -> profile for enabled slack routes; re-read when config.yaml changes."""
    path = _config_path()
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return _STATE["routes"]
    if _STATE["mtime"] == mtime and _STATE["path"] == path:
        return _STATE["routes"]
    import yaml
    try:
        cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 - keep the last good map
        logger.warning("slack-identity: could not read %s", path, exc_info=True)
        return _STATE["routes"]
    routes: dict[str, str] = {}
    for r in ((cfg.get("gateway") or {}).get("profile_routes") or []):
        if not isinstance(r, dict) or r.get("enabled", True) is False:
            continue
        if str(r.get("platform", "")).lower() != "slack" or r.get("thread_id"):
            continue
        chat_id, profile = r.get("chat_id"), r.get("profile")
        if chat_id and profile:
            routes[str(chat_id)] = str(profile)
    _STATE.update(routes=routes, mtime=mtime, path=path)
    return routes


def identity_for(channel: Any) -> dict[str, str]:
    """``{"username", "icon_url"}`` for a routed channel of a listed profile, else ``{}``."""
    if not channel:
        return {}
    profile = _routes().get(str(channel))
    ident = _STATE["profiles"].get(profile) if profile else None
    if not isinstance(ident, dict):
        return {}
    out = {k: str(ident[k]) for k in ("username", "icon_url") if ident.get(k)}
    return out


def _patch_client() -> None:
    from slack_sdk.web.async_client import AsyncWebClient
    from slack_sdk.web.client import WebClient

    for cls in (AsyncWebClient, WebClient):
        orig = cls.chat_postMessage
        if getattr(orig, _PATCH_FLAG, False):
            continue
        cls.chat_postMessage = _wrap(orig)


def _wrap(orig):
    def apply(kwargs: dict) -> dict:
        if kwargs.get("username") or kwargs.get("icon_url") or kwargs.get("icon_emoji"):
            return kwargs
        try:
            extra = identity_for(kwargs.get("channel"))
        except Exception:  # noqa: BLE001 - identity is cosmetic; never block a send
            logger.warning("slack-identity: lookup failed", exc_info=True)
            return kwargs
        return {**kwargs, **extra} if extra else kwargs

    import inspect
    if inspect.iscoroutinefunction(orig):
        @functools.wraps(orig)
        async def wrapper(self, *args, **kwargs):
            return await orig(self, *args, **apply(kwargs))
    else:
        @functools.wraps(orig)
        def wrapper(self, *args, **kwargs):
            return orig(self, *args, **apply(kwargs))
    setattr(wrapper, _PATCH_FLAG, True)
    return wrapper


def register(ctx) -> None:
    profiles = ctx.get_config("profiles", None)
    if not isinstance(profiles, dict) or not profiles:
        logger.info("slack-identity: no profiles configured; not patching")
        return
    _STATE["profiles"] = profiles
    try:
        _patch_client()
    except Exception:  # noqa: BLE001
        logger.exception("slack-identity: could not patch slack_sdk; identities disabled")
        return
    logger.info("slack-identity: active for %s", ", ".join(sorted(profiles)))
