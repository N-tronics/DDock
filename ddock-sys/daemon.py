# Import only required objects instead of an entire module
from flask import Flask, request
from json import dump, load
from socket import gethostbyname, gethostname
from subprocess import run, DEVNULL, PIPE, STDOUT
from os import getenv
from os.path import isfile

DDS_CONF = getenv('DDS_CONF', '/etc/dds.conf.json')
app = Flask(__name__)


@app.route('/', methods=['GET'])
def exec():
    # Load the conf file
    if isfile(DDS_CONF):
        with open(DDS_CONF) as f:
            conf = load(f)
    else:
        conf = {
            'Path': [],
            'Cwd': '/',
            'Env': {}
        }
    # Check if the stored CWD is valid
    if run(f"cd {conf['Cwd']}", shell=True, stdout=DEVNULL, stderr=DEVNULL, executable='bash', cwd='/').returncode:
        conf['Cwd'] = '/'
        with open(DDS_CONF, 'w') as f:
            dump(conf, f, indent=4)
        return {
            'exitcode': 1,
            'result': 'Stored CWD is not a valid directory. Defaulting to /'
        }

    # Parse the environment variables
    envs = {k: (getenv(k, '') + v['Value'] if conf['Env'][k]['Concat']
                else v['Value']) for k, v in tuple(conf['Env'].items())}
    envs['PATH'] = getenv('PATH', '')
    for path in conf['Path']:
        envs['PATH'] += ':' + path

    # Parse the request body
    cmd = request.form.to_dict()['cmd']
    # If the command is a change directory, add '; pwd' to it to print the new dir to stdout
    is_cd = cmd.split()[0] == 'cd'
    if is_cd:
        cmd += '; pwd'

    # Execute the command
    output = run(cmd, shell=True, text=True, stdout=PIPE,
                 stderr=STDOUT, executable='bash', env=envs, cwd=conf['Cwd'])
    res = {'exitcode': output.returncode, 'result': output.stdout}
    # If the command was a change directory and it was a success, store the directory in the conf file
    if is_cd and output.returncode == 0:
        conf['Cwd'] = output.stdout[:-1]
        with open(DDS_CONF, 'w') as f:
            dump(conf, f, indent=4)
        res['result'] = 'CWD: ' + res['result']
    return res


if __name__ == '__main__':
    # Run the application on the container's IP address on port 1000
    app.run(host=gethostbyname(gethostname()), port=1000)
