import json
import sys
# import xml.etree as xml

from os.path import dirname, join
from paste.httpserver import serve
from pyramid.config import Configurator
from pyramid.response import Response

from .. import runner

sys.path.append(join(dirname(__file__), '..'))


def get_not_defined(request):
    return Response("GET is not defined at this time.")


def test_tempest(request):
    request_dict = json.loads(request.body)
    results = runner.main(framework='tempest', **request_dict)
    return Response(results, content_type='application/json')


def test_cloudcafe(request):
    request_dict = json.loads(request.body)
    results = runner.main(framework='cloudcafe', **request_dict)
    return Response(results, content_type='application/json')


if __name__ == '__main__':
    config = Configurator()

    config.add_route('tempest', '/tempest/test')
    config.add_route('cloudcafe', '/cloudcafe/test')

    config.add_view(test_tempest,
                    route_name='tempest', request_method='POST')

    config.add_view(get_not_defined,
                    route_name='tempest', request_method='GET')

    config.add_view(test_cloudcafe,
                    route_name='cloudcafe', request_method='POST')

    config.add_view(get_not_defined,
                    route_name='cloudcafe', request_method='GET')

    app = config.make_wsgi_app()
    serve(app, host='0.0.0.0', port='5000')
