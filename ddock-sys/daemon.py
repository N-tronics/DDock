# Import only required objects instead of an entire module
from flask import Flask, request
from json import dump, load
from socket import gethostbyname, gethostname
from subprocess import run, DEVNULL, PIPE, STDOUT
from os import getenv

DDD_CONF = getenv('DDD_CONF', '/etc/ddd.conf.json')
app = Flask(__name__)

@app.route('/', methods=['GET'])
def exec():
    # Load the config file
    with open(DDD_CONF) as f:
        config = load(f)
    # Check if the stored CWD is valid
    if run(f"cd {config['Cwd']}", shell=True, stdout=DEVNULL, stderr=DEVNULL, executable='bash', cwd='/').returncode:
        config['Cwd'] = '/'
        with open(DDD_CONF, 'w') as f:
            dump(config, f, indent=4)
        return {
            'exitcode': 1,
            'result': 'Stored CWD is not a valid directory. Defaulting to /'
        }

    # Parse the environment variables
    envs = {k:(getenv(k, '') + v['Value'] if config['Env'][k]['Concat'] else v['Value']) for k, v in tuple(config['Env'].items())}

    # Parse the request body
    cmd = request.form.to_dict()['cmd']
    # If the command is a change directory, add '; pwd' to it to print the new dir to stdout
    is_cd = cmd.split()[0] == 'cd'
    if is_cd:
        cmd += '; pwd'

    # Execute the command
    output = run(cmd, shell=True, text=True, stdout=PIPE, stderr=STDOUT, executable='bash', env=envs, cwd=config['Cwd'])
    res = {'exitcode': output.returncode, 'result': output.stdout}
    # If the command was a change directory and it was a success, store the directory in the config file
    if is_cd and output.returncode == 0:
        config['Cwd'] = output.stdout[:-1]
        with open(DDD_CONF, 'w') as f:
            dump(config, f, indent=4)
        res['result'] = 'CWD: ' + res['result']
    return res

if __name__ == '__main__':
    # Run the application on the container's IP address on port 1000
    app.run(host=gethostbyname(gethostname()), port=1000)
