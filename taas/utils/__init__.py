import logging
import sys

LOG = logging.getLogger(__name__)


def retrieve(client, resource, name, **kwargs):
    director = getattr(client, '%ss' % resource)
    try:
        return director.create(name, **kwargs)
    except Exception:
        LOG.exception('Creation failed')
        sys.exit(1)
