from .environment import Environment
from .frameworks import CloudCafe, Tempest
from .utils import cleanup, Reporter
import argh

LOG = Reporter(__name__).setup()


def main(endpoint, username='admin', password='secrete', framework='tempest',
         test='', product='compute', special_config=None):

    environment = Environment(username, password, endpoint)
    with cleanup(environment):
        environment.build()

        if 'tempest' in framework:
            framework = Tempest(environment, framework, test)
        else:
            framework = CloudCafe(environment, framework, test, product,
                                  special_config)

        results = framework.test_from()
        return results


if __name__ == '__main__':
    argh.dispatch_command(main)
