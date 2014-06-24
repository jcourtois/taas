import os


def get_cloudcafe_env_dict(nova, keystone, taas_config, devstack):
    subprocess_env = os.environ.copy()
    subprocess_env.update(basic_environment_dictionary(nova, keystone,
                                                       taas_config))
    if devstack:
        subprocess_env.update(env_for_devstack)
    return subprocess_env


def subprocess_env_dict_from(env_dict):
    subprocess_env = os.environ.copy()
    for section, values in env_dict.items():
        for variable, value in values.items():
            environment_var = "CAFE_{0}_{1}".format(section, variable)
            subprocess_env[environment_var] = value
            print "export {}={}".format(environment_var, value)
    return subprocess_env


env_for_devstack = subprocess_env_dict_from({
    "flavors": {
        "primary_flavor": "42",
        "secondary_flavor": "84",
        "resize_enabled": "true"
    },

    "config_drive": {
        "openstack_meta_path": "/mnt/config/openstack/latest/"
                               "meta_data.json",
        "ec_meta_path": "/mnt/config/ec2/latest/meta-data.json",
        "base_path_to_mount": "/mnt/config",
        "mount_source_path": "/dev/disk/by-label/config-2",
        "min_size": "20",
        "max_size": "35"
    }
})


def basic_environment_dictionary(nova, keystone, taas_config):
    nova_user = keystone.users.find(name=nova.client.user)
    guest = taas_config['users']['guest'][0]

    return subprocess_env_dict_from(
        {
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
                "instance_auth_strategy": "key",  # ?
                "server_status_interval": "15",
                "server_build_timeout": "600",
                "server_resize_timeout": "1800",
                "network_for_ssh": "private",
                "ip_address_version_for_ssh": "4",  # ?
                "instance_disk_path": "/dev/xvda",  # ?
                "connection_retry_interval": "15",
                "connection_timeout": "600",
                "split_ephemeral_disk_enabled": "true",
                "resource_build_attempts": "3",  # ?
                "disk_format_type": "ext3",  # ?
                "personality_file_injection_enabled": "true",
                "default_file_path": "/",  # ?
                "expected_networks": '\'{"private":'
                                     '{"v4": true, "v6": false}}\'',
                "ephemeral_disk_max_size": "10",
                "default_injected_files": "",
            },
            "images": {
                "primary_image": taas_config['images'][0],
                "secondary_image": taas_config['images'][1],
                "image_status_interval": "15",
                "snapshot_timeout": "900",
                "can_get_deleted_image": "true",  # guess
                "primary_image_has_protected_properties": "false",
                "primary_image_default_user": "admin",  # guess
                "non_inherited_metadata_filepath": None
                # ^ guess; apparently this can be optional
            },

            "marshalling": {
                "serialize_format": "json",
                "deserialize_format": "json"
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
                "compute_endpoint_url": get_nova_endpoint(taas_config),
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
        })


def get_nova_endpoint(taas_config):
    nova_endpoint = "".join(taas_config['nova']['endpoints']['public']
                            .rsplit('/')[:-1])
    return nova_endpoint
