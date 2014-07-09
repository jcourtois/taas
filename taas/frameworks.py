import logging
import sys
import os
import subprocess

from jinja2 import Template
from os.path import abspath, dirname, exists, join
import taas.cloudcafe_configs.grabber as grabber

LOG = logging.getLogger(__name__)


class Framework(object):

    def __init__(self, env, framework, test):
        self.env = env
        self.framework = framework
        self.test = test

    def populate_settings(self):
        LOG.info('Building configuration file')

        template_dir = join(abspath(dirname(__file__)), 'files/')
        example = '{0}.conf.example'.format(self.framework)

        with open(join(template_dir, example), 'r') as stream:
            template = Template(stream.read())

        self.settings = template.render(catalog=self.env.config['catalog'],
                                        images=self.env.config['images'],
                                        network=self.env.config['network'],
                                        router=self.env.config['router'],
                                        users=self.env.config['users'])

        with open('/opt/tempest/etc/tempest.conf', 'w') as stream:
            stream.write(self.settings)

    def test_from(self):
        raise NotImplementedError


class CloudCafe(Framework):

    def __init__(self, environment, framework, test, product,
                 special_config=None):
        super(CloudCafe, self).__init__(environment.config, framework, test)
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

    def __init__(self, config, framework, test):
        super(Tempest, self).__init__(config, framework, test)

    def test_from(self):
        LOG.info('Running Tempest tests for: {0}'.format(self.test))

        self.populate_settings()

        repo = 'https://github.com/openstack/tempest.git'
        branch = 'stable/havana'
        tempest_dir = '/opt/tempest'

        if not exists(tempest_dir):
            os.mkdir(tempest_dir)

        try:
            os.rmdir(tempest_dir)
        except OSError as exc:
            if exc.errno == os.errno.ENOTEMPTY:
                LOG.warning('Directory not empty: {0}'.format(tempest_dir))
        else:
            checkout = 'git clone -b {0} {1} {2}'.format(branch, repo,
                                                         tempest_dir)
            subprocess.check_call(checkout, shell=True)

        xunit_file = 'taas_results.xml'
        xunit_flag = '--with-xunit --xunit-file={0}'.format(xunit_file)

        tempest_cmd = (
            'python -u `which nosetests` --where='
            '{0}/tempest/api/{1} {2}'.format(tempest_dir, self.test,
                                             xunit_flag)
        )

        LOG.debug('Tempest command: {0}'.format(tempest_cmd))

        try:
            output = subprocess.check_output(tempest_cmd, shell=True,
                                             stderr=subprocess.STDOUT)
            return output
        except Exception as exc:
            LOG.error(exc)
