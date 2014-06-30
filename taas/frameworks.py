import logging
import os
import subprocess

from jinja2 import Template
from os.path import abspath, dirname, exists, join

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

    def __init__(self, config, framework, test):
        super(CloudCafe, self).__init__(config, framework, test)

    def test_from(self):
        self.load_env()
        # load environment variables
        # run test

    # def export_variables(self, section, values):
    #     for variable, value in values.items():
    #         export = "CAFE_{0}_{1}".format(section, variable)
    #         os.environ[export] = value

    def export_variables(self, section, values):
        for variable, value in values.items():
            export = "CAFE_{0}_{1}".format(section, variable)
            print "export {}={}".format(export, value)

    def get_images(self):
        images = self.env.nova.images.list()
        primary = images[0].id
        secondary = images[1].id
        return primary, secondary

    def load_env(self):
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
        primary_img, secondary_imd = self.get_images()

        users = self.env.config['users']
        user1 = users['guest'][0]
        nova = self.env.nova
        keystone = self.env.keystone

        args = {
            "OPENCAFE_ENGINE": {
                "config_directory": "~/.cloudcafe/configs",
                "log_directory": "/logz",
                "data_directory": "/stuff",
                "logging_verbosity": "STANDARD",
                "master_log_file_name": "my_logz",

            },

            "user_auth_config": {
                "strategy": "keystone",
                "endpoint": keystone.auth_url
            },
            "flavors": {
                "primary_flavor": "1",
                "secondary_flavor": "2",
                "resize_enabled": "true"
            },
            "servers": {
                "personality_file_injection_enabled": "true",
                "instance_disk_path": "/dev/xvda",  # ?
                "split_ephemeral_disk_enabled": "true",
                "instance_auth_strategy": "key",  # ?
                "server_status_interval": "15",
                "server_build_timeout": "600",
                "server_resize_timeout": "1800",
                "network_for_ssh": "private",
                "ip_address_version_for_ssh": "4",  # ?
                "connection_retry_interval": "15",
                "connection_timeout": "600",
                "resource_build_attempts": "3",  # ?
                "disk_format_type": "ext3",  # ?
                "default_file_path": "/",  # ?
                "expected_networks": '\'{"private":'
                                     '{"v4": true, "v6": false}}\'',
                "ephemeral_disk_max_size": "10",
                "default_injected_files": "",
            },
            "images": {
                "primary_image_has_protected_properties": "false",
                "primary_image": primary_img,
                "secondary_image": secondary_imd,
                "image_status_interval": "15",
                "snapshot_timeout": "900",
                "can_get_deleted_image": "true",  # guess
                "primary_image_default_user": "admin",  # guess
                "non_inherited_metadata_filepath": None  # guess; apparently this can be optional
            },

            "marshalling": {
                "serialize_format": "json",
                "deserialize_format": "json"
            },

            # "config_drive": {
            #     "openstack_meta_path": "<path_to_openstack/latest/meta_data.json>",
            #     "ec_meta_path": "<path_to_ec2/latest/meta-data.json>",
            #     "base_path_to_mount": "<config_drive_path>",
            #     "mount_source_path": "<mount_source_path>",
            #     "min_size": "<min_size>",
            #     "max_size": "<max_size>"
            # }

        }

        nova_user = keystone.users.find(name=nova.client.user)

        compute = {
            "compute": {
                "hypervisor": nova.hypervisors.list()[0]
                .hypervisor_type.lower()
            },

            "compute_admin_auth_config": {
                "endpoint": nova.client.management_url,
                "strategy": nova.client.auth_system
            },

            "compute_endpoint": {
                "compute_endpoint_name": "nova",
                "compute_endpoint_url": nova.client.auth_url,  # not in example config
                "region": "RegionOne"
            },

            "compute_admin_endpoint": {
                "compute_endpoint_name": "nova",
                "region": "RegionOne"
            },

            "user": {  # this is an admin user; according to the reference config, should not be
                "username": nova_user.name,
                "password": nova.client.password,  # not sure if this is right
                "tenant_id": nova_user.tenantId,
                "user_id": nova_user.id,
                "project_id": nova.projectid  # what does this mean and why is it set to the admin have it
            },

            "compute_admin_user": {
                "username": nova_user.name,
                "password": nova.client.password,
                "tenant_name": keystone.tenants.find(
                    id=nova_user.tenantId).name
            },

            "compute_secondary_user": {
                "username": user1['name'],
                "password": user1['password'],
                "tenant_name": keystone.tenants.find(
                    id=user1['ids']['tenant']).name
            }
        }

        args.update(compute)

        for section, values in args.items():
            self.export_variables(section, values)


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
