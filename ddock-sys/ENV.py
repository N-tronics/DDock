# Import only required objects instead of entire modules
from optparse import OptionParser
from sys import exit
from json import load, dump
from os import getenv

if __name__ == '__main__':
    # Get the path to the config file
    DDD_CONF = getenv('DDD_CONF', '/etc/ddd.conf.json')

    # Parse all options
    parser = OptionParser()
    parser.add_option('-c', '--concatenate', action='store_true', dest='concat', default=False, help='Concatenate existing value with given value')
    parser.add_option('-d', '--delete', action='store_true', dest='delete', default=False, help='Delete given variable entry')
    parser.add_option('-l', '--list', action='store_true', dest='list', default=False, help='Lists all custom environment variables')
    options, args = parser.parse_args()

    # Load the config file
    with open(DDD_CONF) as f:
        others = load(f)
        envs = others['Env']

    # Process command
    if options.delete:
        if len(args) < 1:
            print('Improper usage. Entry to delete not given')
            exit(1)
        envs.pop(args[0])
    elif options.list:
        for var, val in tuple(envs.items()):
            print(f'{var}={val["Value"]}; {getenv(var) + val["Value"] if val["Concat"] else val["Value"]}')
    else:
        if len(args) < 2:
            print('Improper usage. Complete values are not given')
            exit(1)
        envs[args[0]] = {
            'Value': args[1],
            'Concat': options.concat
        }

    # Write the updated conf to the file
    others['Env'] = envs
    with open(DDD_CONF, 'w') as f:
        dump(others, f, indent=4)
