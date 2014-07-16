import logging
import re

from keystoneclient.v2_0.client import Client as keystone_client
from neutronclient.v2_0.client import Client as neutron_client
from novaclient.v1_1 import client as nova_client
from uuid import uuid4 as uuid

LOG = logging.getLogger(__name__)


class Environment(object):

    def __init__(self, username, password, auth_url):
        self.catalog = {}
        self.users = []
        self.tenant = None
        self.network = None
        self.router = None

        self.keystone = keystone_client(
            username=username,
            password=password,
            tenant_name=username,
            auth_url=auth_url
        )
        self.neutron = neutron_client(
            username=username,
            password=password,
            tenant_name=username,
            auth_url=auth_url
        )
        self.nova = nova_client.Client(
            username=username,
            api_key=password,
            project_id=username,
            auth_url=auth_url
        )

    def create_tenant(self):
        LOG.info('Creating tenant')
        self.tenant = self.keystone.tenants.create(tenant_name=str(uuid()))

    def create_users(self, password='secrete'):
        LOG.info('Creating users')
        for each in xrange(2):
            user = self.keystone.users.create(str(uuid()), password=password)
            self.provision_role(user)
            self.users.append(user)

    def provision_role(self, user):
        LOG.info('Provisioning user role')
        roles = self.keystone.roles.list()
        role = [role for role in roles if '_member_' in role.name][0]
        try:
            self.keystone.roles.add_user_role(user, role, tenant=self.tenant)
        except Exception as exc:
            LOG.warning('User {0} has correct role'.format(user.name, exc))

    def get_catalog(self):
        LOG.info('Gathering service catalog')
        endpoints = self.keystone.endpoints.list()
        services = self.keystone.services.list()

        _catalog = {}
        for endpoint in endpoints:
            for service in services:
                if endpoint.service_id in service.id:
                    self.catalog[service.name] = {
                        'service_id': service.id,
                        'description': service.description,
                        'ip_address': re.search(
                            r'[0-9]+(?:\.[0-9]+){3}',
                            endpoint.adminurl
                        ).group(0),
                        'endpoints': {
                            'admin': endpoint.adminurl,
                            'internal': endpoint.internalurl,
                            'public': endpoint.publicurl
                        }}
        return _catalog

    def get_images(self):
        LOG.info('Gathering image metadata')
        images = (image for image in self.nova.images.list())
        try:
            self.images = [next(images) for each in xrange(2)]
        except StopIteration as exc:
            LOG.error('Insufficient amount of images: {0}'.format(exc))

    def create_network(self):
        LOG.info('Creating network')
        payload = {"network": {"name": str(uuid()),
                               "shared": True}}
        self.network = self.neutron.create_network(payload)['network']

    def create_router(self):
        LOG.info('Creating router')
        payload = {"router": {"name": str(uuid()),
                              "admin_state_up": True}}
        self.router = self.neutron.create_router(payload)['router']

    def build(self):
        LOG.info('Building testing environment')
        self.get_catalog()
        self.get_images()
        self.create_tenant()
        self.create_users()
        self.create_network()
        self.create_router()

    def destroy(self):
        LOG.info('Destroying testing environment')
        if self.tenant:
            self.keystone.tenants.delete(self.tenant)
        if self.users:
            for user in self.users:
                self.keystone.users.delete(user)
        if self.network:
            self.neutron.delete_network(self.network['id'])
        if self.router:
            self.neutron.delete_router(self.router['id'])
        LOG.info('Done!')
