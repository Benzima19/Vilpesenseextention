"""Vercel Python Function entrypoint: every /api/* request is routed here."""

from guardian.api.app import app  # noqa: F401
