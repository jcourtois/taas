import json
import logging
import sys
import os
import subprocess

from jinja2 import Template
from os.path import abspath, dirname, exists, join
import taas.cloudcafe_configs.grabber as grabber

LOG = logging.getLogger(__name__)


class Framework(object):

    def __init__(self, environment, framework, test):
        self.env = environment
        self.framework = framework
        self.test = test

    def populate_settings(self):
        LOG.info('Building configuration file')

        template_dir = join(abspath(dirname(__file__)), 'files/')
        example = '{0}.conf.example'.format(self.framework)

        with open(join(template_dir, example), 'r') as stream:
            template = Template(stream.read())

        self.settings = template.render(catalog=self.env.catalog,
                                        images=self.env.images,
                                        network=self.env.network,
                                        router=self.env.router,
                                        users=self.env.users
                                        )

        conf_dir = '/opt/tempest/etc/'
        if not exists(conf_dir):
            os.makedirs(conf_dir)

        with open(join(conf_dir, 'tempest.conf'), 'w') as stream:
            stream.write(self.settings)

    def test_from(self):
        raise NotImplementedError


class CloudCafe(Framework):

    def __init__(self, environment, framework, test, product,
                 special_config=None):
        super(CloudCafe, self).__init__(environment, framework, test)
        self.special_config = special_config
        self.product = product
        self.env = environment

    def test_from(self):
        env_dict = grabber.get_cloudcafe_environment(env=self.env,
                                                     product=self.product,
                                                     special_config=
                                                     self.special_config)
        p = subprocess.Popen(
            "cafe-runner {product} reference.json.config -f".format(
                product=self.product),
            env=env_dict, shell=True)

        for line in iter(p.stdout.readline, ''):
            line = line.replace('\r', '').replace('\n', '')
            print line
            sys.stdout.flush()


class Tempest(Framework):

    def __init__(self, environment, framework, test):
        super(Tempest, self).__init__(environment, framework, test)

    def test_from(self):
        LOG.info('Running Tempest tests for: {0}'.format(self.test))

        repo = 'https://github.com/openstack/tempest.git'
        tempest_dir = '/opt/tempest'

        if not exists(tempest_dir):
            checkout = 'git clone {0} {1}'.format(repo, tempest_dir)
            subprocess.check_call(checkout, shell=True)

        tests_file = abspath('results.json')
        tests_dir = join(tempest_dir, 'tempest/api/%s' % self.test)
        flags = '--with-json --json-file={0}'.format(tests_file)
        tempest_cmd = 'nosetests --where={0} {1}'.format(tests_dir, flags)

        self.populate_settings()

        LOG.info('Running Tempest tests for: {0}'.format(self.test))

        try:
            subprocess.check_output(tempest_cmd, shell=True,
                                    stderr=subprocess.STDOUT)
        except Exception as exc:
            LOG.error(exc.output)

        with open(tests_file, 'r') as fp:
            return json.dumps(json.load(fp), sort_keys=True, indent=4,
                              separators=(',', ': '))
