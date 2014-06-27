import logging
import os
import subprocess

from jinja2 import Template
from os.path import abspath, dirname, exists, join

LOG = logging.getLogger(__name__)


class Framework(object):

    def __init__(self, config, framework, test):
        self.config = config
        self.fwrk = framework
        self.test = test

    def populate_settings(self):
        LOG.info('Building configuration file')

        template_dir = join(abspath(dirname(__file__)), 'files/')
        example = '{0}.conf.example'.format(self.fwrk)

        with open(join(template_dir, example), 'r') as stream:
            template = Template(stream.read())

        self.settings = template.render(catalog=self.config['catalog'],
                                        images=self.config['images'],
                                        network=self.config['network'],
                                        router=self.config['router'],
                                        users=self.config['users'])

        with open('/opt/tempest/etc/tempest.conf', 'w') as stream:
            stream.write(self.settings)

    def test_from(self):
        raise NotImplementedError


class CloudCafe(Framework):

    def __init__(self, config, framework, test):
        super(CloudCafe, self).__init__(config, framework, test)

    def test_from(self):
        pass
        # load environment variables
        # run test

    # def export_variables(self, section, values):
    #     for variable, value in values.items():
    #         export = "CAFE_{0}_{1}".format(section, variable)
    #         os.environ[export] = value

    def export_variables(section, values):
        for variable, value in values.items():
            export = "CAFE_{0}_{1}".format(section, variable)
            print "export {}={}".format(export, value)


    def get_images(self):
        images = nova.images.list()
        primary = images[0]
        secondary = images[1]
        return primary, secondary

    def config():
        # endpoint = self.get_endpoint()
        # admin_user, admin_password, admin_tenant = self.get_admin_user()
        # admin_tenant_id, admin_user_id, admin_project_id = self.get_admin_ids(
        #     admin_user, admin_password, admin_tenant)
        # second_user, second_password, second_tenant = self.get_non_admin_user()
        # primary_image_id, secondary_image_id = self.get_image_ids()
        # if self.deployment.has_feature("neutron"):
        #     network_id = self.get_network_id(network_name)
        #     networks = "{'%s':{'v4': True, 'v6': False}}" % network_name
        # else:
        #     # How connectivity works in cloudcafe for novanet needs work
        #     # May not be possible atm due to floating ips
        #     network_name = "public"
        #     network_id = "0000" * 5
        #     networks = "{'%s':{'v4': True, 'v6': False}}" % network_name
        #
        # endpoint_versioned = "{0}/v2.0".format(endpoint)
        # admin_endpoint_versioned = endpoint_versioned.replace("5000", "35357")


        args = {
            "OPENCAFE_ENGINE": {
                "config_directory": "~/.cloudcafe/configs",
                "log_directory": "/logz",
                "data_directory": "/stuff",
                "logging_verbosity": "STANDARD",
                "master_log_file_name": "my_logz",

            },

            "user": {
                "username": "admin",
                "password": "secrete",
                "tenant_name": "admin"
            },

            "user_auth_config": {
                "strategy": "keystone",
                "endpoint": "http://192.168.4.1:5000/v2.0"
            },

            "compute_endpoint": {
                "compute_endpoint_name": "nova",
                "compute_endpoint_url": "http://192.168.4.1:8774/v2/08e7b64a9814479597c1082946f402a4",
                "region": "RegionOne"
            },
            "compute": {
                "hypervisor": "qemu" # nova.hypervisors.list[0].hypervisor_type.lower()
            },
            "flavors": {
                "primary_flavor": "1",
                "secondary_flavor": "2",
                "resize_enabled": "true"
            },
            "servers": {
                "personality_file_injection_enabled": "true",
                "instance_disk_path": "/dev/xvda",
                "split_ephemeral_disk_enabled": "true",
                "instance_auth_strategy": "key",
                "server_status_interval": "15",
                "server_build_timeout": "600",
                "server_resize_timeout": "1800"
                "network_for_ssh=private",
                "ip_address_version_for_ssh": "4",
                "connection_retry_interval": "15",
                "connection_timeout": "600",
                "resource_build_attempts": "1",
                "disk_format_type": "ext3",
                "default_file_path": "/",
                "expected_networks": '{"private": {"v4": true, "v6": false}}'
            },
            "images": {
                "primary_image_has_protected_properties": "false",
                "primary_image": "76591c9e-9a1e-472d-ac3a-588f2e7f2849",
                "secondary_image": "609ead48-726b-4f77-ae7a-a27e4528263a",
            },
            "marshalling": {
                "serialize_format": "json",
                "deserialize_format": "json"
            }

        }

        for section, values in args.items():
            export_variables(section, values)




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
            LOG.error(exc.output)
