import os
import docker
import discord
import threading as thread
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DDOCK_TOKEN = os.getenv('DDOCK_TOKEN')

ddock = commands.Bot(command_prefix='$ ')
dockClient = docker.from_env()

running_handlers = {}


class Docker:
    @staticmethod
    def startContainer(user):
        existingContainers = dockClient.containers.list(all=True)
        if user in [cont.name for cont in existingContainers]:
            container = dockClient.containers.get(user)
        else:
            container = dockClient.containers.create(
                'ubuntu:latest', 'sleep infinity', detach=True, name=user)
        if container.status != 'running':
            container.start()

        return container

    @staticmethod
    def containerExec(container, cmd):
        res = container.exec_run(f'bash -c "source /root/.bashrc; cd $PWD; {cmd}"')
        return res[0], res[1].decode('utf-8')

    @staticmethod
    def containerCd(container, dir):
        result = Docker.containerExec(container, f'cd {dir}; pwd')
        if result[0]: return result

        Docker.containerExec(container, f'echo \'export PWD={result[1]}\' > /root/.bashrc')
        return (result[0], result[1])


class ReqHandler(thread.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


async def send_reply(code, res, msg):
    try:
        await msg.channel.send(f'```Exit Code: {code}``` ```{res}```', reference=msg)
    except discord.errors.HTTPException:
        await msg.channel.send(f'Could not send output log.```Exit Code: {code}```', reference=msg)

async def request_handler(msg, cmd, parent_loop):
    print('processing request')
    container = Docker.startContainer(msg.author.name)

    if cmd.split()[0] == 'cd':
        code, res = Docker.containerCd(container, ' '.join(cmd.split()[1:]))
    else:
        code, res = Docker.containerExec(container, cmd)
    container.stop()

    print(f'done with req: {res}')
    asyncio.run_coroutine_threadsafe(send_reply(code, res, msg), parent_loop)


@ddock.event
async def on_ready():
    print(f'{ddock.user.name} has connected to Discord!')

@ddock.event
async def on_message(msg):
    if msg.author == ddock.user:
        return
    print(f'parent: {thread.get_ident()}')

    if not msg.content.startswith(ddock.command_prefix): return
    cmd = msg.content[len(ddock.command_prefix):].replace('"', '\\"')
    print(cmd)

    global running_handlers

    if msg.author.name not in running_handlers:
        running_handlers[msg.author.name] = ReqHandler()
        running_handlers[msg.author.name].start()
    asyncio.run_coroutine_threadsafe(request_handler(msg, cmd, asyncio.get_event_loop()), running_handlers[msg.author.name].loop)
    print(thread.active_count())

ddock.run(DDOCK_TOKEN)
