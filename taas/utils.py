import logging
import sys

from contextlib import contextmanager

LOG = logging.getLogger(__name__)


class Reporter(object):

    def __init__(self, name):
        self.name = name

    def setup(self):
        logger = logging.getLogger('taas')

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)

        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(fmt)
        ch.setFormatter(formatter)

        logger.setLevel(logging.DEBUG)
        logger.addHandler(ch)

        return logger


@contextmanager
def cleanup(stage):
    try:
        yield
    except (Exception, KeyboardInterrupt):
        LOG.error('Run failed', exc_info=True)
    finally:
        stage.destroy()
