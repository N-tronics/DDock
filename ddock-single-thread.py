import os
import docker
import discord
from time import sleep
from discord.ext import commands
from dotenv import load_dotenv
import requests as r

load_dotenv()
DDOCK_TOKEN = os.getenv('DDOCK_TOKEN')


class DDockDaemon:
    def __init__(self):
        self.dockerClient = docker.from_env()

    def startContainer(self, user):
        existingContainers = self.dockerClient.containers.list(all=True)
        if user in [cont.name for cont in existingContainers]:
            container = self.dockerClient.containers.get(user)
        else:
            container = self.dockerClient.containers.create('ddock-sys:v1-4', detach=True, name=user)

        container.start()
        while not container.attrs['State']['Running']: container.reload()

        return container

    def containerExec(self, ip_addr, cmd):
        for _ in range(10):
            try:
                res = r.get('http://' + ip_addr + ':1000', data={'cmd': cmd})
                return res.json()
            except r.exceptions.ConnectionError:
                pass
            sleep(0.1)
        return {'exitcode': 1, 'result': 'Could not start container\n'}


ddock = commands.Bot(command_prefix='$ ')
ddd = DDockDaemon()

@ddock.event
async def on_ready():
    print(f'{ddock.user.name} has connected to Discord!')

@ddock.event
async def on_message(msg):
    if msg.author == ddock.user:
        return

    if not msg.content.startswith(ddock.command_prefix): return

    container = ddd.startContainer(msg.author.name)
    res = ddd.containerExec(container.attrs['NetworkSettings']['IPAddress'], msg.content[len(ddock.command_prefix):])
    container.stop()
    if len(res['result']) == 0: res['result'] = ' '
    try:
        await msg.channel.send(f'```Exit Code: {res["exitcode"]}``` ```{res["result"]}```', reference=msg)
    except discord.errors.HTTPException:
        await msg.channel.send(f'Could not send output log.```Exit Code: {res["exitcode"]}```')


ddock.run(DDOCK_TOKEN)
