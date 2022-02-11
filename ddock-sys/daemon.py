from flask import Flask, request
from json import dump, load
from socket import gethostbyname, gethostname
from subprocess import run, DEVNULL, PIPE, STDOUT
from sys import exit

CONFIG_FILE = '/etc/ddd.conf.json'

with open(CONFIG_FILE) as f:
    config = load(f)

if run(f"cd {config['Cwd']}", shell=True, stdout=DEVNULL, stderr=DEVNULL, executable='bash', cwd='/').returncode:
    exit(1)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def exec():
    cmd = request.form.to_dict()['cmd']
    is_cd = cmd.split()[0] == 'cd'
    cmd = '. ~/.profile; ' + cmd
    if is_cd:
        cmd += '; pwd'
    output = run(cmd, shell=True, text=True, stdout=PIPE, stderr=STDOUT, executable='bash', cwd=config['Cwd'])
    res = {'exitcode': output.returncode, 'result': output.stdout}
    if is_cd and not output.returncode:
        config['Cwd'] = output.stdout[:-1]
        with open(CONFIG_FILE, 'w') as f:
            dump(config, f, indent=4)
        res['result'] = 'CWD: ' + res['result']
    return res

app.run(host=gethostbyname(gethostname()), port=1000)
