import ConfigParser
import os


def import_config(product, config):
    parser = ConfigParser.SafeConfigParser(allow_no_value=True)
    filepath = os.path.abspath('{}/{}'.format(product, config))

    with open(filepath) as config_file:
        parser.readfp(config_file)
    return parser._sections
