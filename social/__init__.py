from __future__ import absolute_import

# from more.cel import app

from .cel import app as celery_app

__all__ = ['celery_app']
