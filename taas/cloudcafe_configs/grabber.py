import ConfigParser
import os
import logging
from IPython import embed

LOG = logging.getLogger(__name__)


def get_cloudcafe_environment(env, product, special_config=None):
    gatherer = ClientInfoGatherer(env)
    LOG.info("Loading base configuration file: cloudcafe_configs/{}/{}"
             "".format(product, "base"))
    environment = import_config(product, "base")

    if special_config:
        LOG.info("Loading config override file: cloudcafe_configs/{}/{}"
                 "".format(product, special_config))
        override = import_config(product, special_config)
        for section in environment:
            for option in environment[section]:
                environment[section][option] = (override[section][option] or
                                                environment[section][option])

    for section in environment:
        for option in environment[section]:
            if environment[section][option] is None:
                value = gatherer.get_from_clients(section, option)
                environment[section][option] = value
                LOG.info("env[{section}][{option}] was not defined; overriding"
                         " it with '{value}', gathered from OS client info."
                         .format(section=section, option=option, value=value))

    subprocess_env = os.environ.copy()
    subprocess_env.update(python_dict_to_environment_var_dict(environment))
    return subprocess_env


def python_dict_to_environment_var_dict(env_dict):
    subprocess_env = os.environ.copy()
    for section, values in env_dict.items():
        for variable, value in values.items():
            if variable != "__name__":
                environment_var = "CAFE_{0}_{1}".format(section, variable)
                subprocess_env[environment_var] = value
                print "export {}={}".format(environment_var, value)
    return subprocess_env


def import_config(product, config):
    parser = ConfigParser.SafeConfigParser(allow_no_value=True)
    filepath = os.path.abspath(
        'taas/cloudcafe_configs/{product}/{config}.config'.format(
            product=product, config=config))

    with open(filepath) as config_file:
        parser.readfp(config_file)
    return parser._sections


class ClientInfoGatherer:
    def __init__(self, env):
        self.env = env
        self._info_from_clients = self._load_info_from_clients()

    def get_from_clients(self, section, option):
        try:
            return self._info_from_clients[section][option]
        except KeyError:
            LOG.warning("Client info did not have the information for {}{}"
                        .format(section, option))

    def _load_info_from_clients(self):
        nova = self.env.nova
        keystone = self.env.keystone
        guest = self.env.config['users']['guest'][0]

        nova_user = keystone.users.find(name=nova.client.user)

        return {
            "OPENCAFE_ENGINE": {
                "config_directory": "~/taas/taas/cloudcafe_configs",
                "log_directory": "/logz",
                "data_directory": "/stuff",
                "logging_verbosity": "STANDARD",
                "master_log_file_name": "my_logz",

            },

            "user_auth_config": {
                "strategy": "keystone",
                "endpoint": keystone.auth_url
            },

            "images": {
                "primary_image": self.env.config['images'][0]['id'],
                "secondary_image": self.env.config['images'][1]['id'],
            },

            "compute": {
                "hypervisor": nova.hypervisors.list()[0]
                .hypervisor_type.lower()
            },

            "compute_admin_auth_config": {
                "endpoint": nova.client.auth_url,
                "strategy": nova.client.auth_system
            },

            "compute_endpoint": {
                "compute_endpoint_name": "nova",
                "compute_endpoint_url": self._get_nova_endpoint(),
                #  ^ not in example config
                "region": "RegionOne"
            },

            "compute_admin_endpoint": {
                "compute_endpoint_name": "nova",
                "region": "RegionOne"
            },

            "user": {
            # this is an admin user;
            # according to the reference config, should not be
                "username": nova_user.name,
                "password": nova.client.password,  # not sure if this is right
                "tenant_id": nova_user.tenantId,
                "user_id": nova_user.id,
                "project_id": nova.projectid
                # ^ what does this mean
                # and why is it set to the admin have it
            },

            "compute_admin_user": {
                "username": nova_user.name,
                "password": nova.client.password,
                "tenant_name": keystone.tenants.find(
                    id=nova_user.tenantId).name
            },

            "compute_secondary_user": {
                "username": guest['name'],
                "password": guest['password'],
                "tenant_name": keystone.tenants.find(
                    id=guest['ids']['tenant']).name
            }
        }

    def _get_nova_endpoint(self):
        nova_endpoint = "".join(self.env.config['catalog']['nova']['endpoints'
                                ]['public']
                                .rsplit('/')[:-1])
        return nova_endpoint
