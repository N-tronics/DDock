from json import dump, load
from sys import argv, exit
from os import getenv
from os.path import isfile, isdir, isabs

if __name__ == '__main__':
    if len(argv) < 3 and argv[1] != 'list':
        print('Usage: path [action] [value]')
        exit(1)

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

    argv = argv[1:]
    if argv[0] == 'add':
        if isabs(argv[1]) and isdir(argv[1]):
            conf['Path'].append(argv[1])
            print(f'PATH={getenv("PATH", "")}', end='')
            for path in conf['Path']:
                print(':' + path)
        else:
            print('Invalid Path given')
            exit(1)
    elif argv[0] == 'delete':
        try:
            path = int(argv[1])
            print(path)
            if path >= 0 and path < len(conf['Path']):
                conf['Path'].pop(path)
            else:
                raise ValueError
        except ValueError:
            print('Invalid Path index given')
            exit(1)
    elif argv[0] == 'list':
        for i, path in enumerate(conf['Path']):
            print(f'{i}: {path}')

    with open(DDS_CONF, 'w') as f:
        dump(conf, f, indent=4)
