# Import only required objects instead of entire modules
from optparse import OptionParser
from sys import exit
from json import load, dump
from os import getenv
from os.path import isfile

if __name__ == '__main__':
    # Get the path to the config file
    DDS_CONF = getenv('DDS_CONF', '/etc/dds.conf.json')
    if isfile(DDS_CONF):
        with open(DDS_CONF) as f:
            conf = load(f)
    else:
        conf = {
            'Path': [],
            'Cwd': '/',
            'Env': {}
        }

    # Parse all options
    parser = OptionParser()
    parser.add_option('-c', '--concatenate', action='store_true', dest='concat',
                      default=False, help='Concatenate existing value with given value')
    parser.add_option('-d', '--delete', action='store_true',
                      dest='delete', default=False, help='Delete given variable entry')
    parser.add_option('-l', '--list', action='store_true', dest='list',
                      default=False, help='Lists all custom environment variables')
    options, args = parser.parse_args()

    # Load the config file
    with open(DDS_CONF) as f:
        conf = load(f)
        envs = conf['Env']

    # Process command
    if options.delete:
        if len(args) < 1:
            print('Improper usage. Entry to delete not given')
            exit(1)
        envs.pop(args[0])
    elif options.list:
        for var, val in tuple(envs.items()):
            print(
                f'{var}={val["Value"]}; {getenv(var) + val["Value"] if val["Concat"] else val["Value"]}')
    else:
        if len(args) < 2:
            print('Improper usage. Complete values are not given')
            exit(1)
        if args[0] == 'PATH':
            print('Please use \'path\' cli instead to manage PATH entries')
            exit(1)
        envs[args[0]] = {
            'Value': args[1],
            'Concat': options.concat
        }
        print(f'{args[0]}={args[1]}')

    # Write the updated conf to the file
    conf['Env'] = envs
    with open(DDS_CONF, 'w') as f:
        dump(conf, f, indent=4)
