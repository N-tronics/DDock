import os
import docker
import discord
import threading
import asyncio
import requests as req
import time
import dotenv
from discord.ext import commands

# Create clients and set constants
dotenv.load_dotenv()
ddock = commands.Bot(command_prefix='$ ')
docker_client = docker.from_env()
DDOCK_TOKEN = os.getenv('DDOCK_TOKEN')
IMAGE = 'ddock-sys'
TAG = 'v2-1'


def start_container(user: str):
    # Get the container object. If the container doesn't exist, create a new one
    try:
        container = docker_client.containers.get(user)
    except docker.errors.NotFound:
        container = docker_client.containers.create(f'{IMAGE}:{TAG}', detach=True, name=user)
    container.start()
    # Wait till the container starts
    while not container.attrs['State']['Running']:
        container.reload()
        time.sleep(0.1)

    return container


async def send_result(msg, res):
    try:
        await msg.channel.send(f'```Exit Code: {res["exitcode"]}``````{res["result"]}```', reference=msg)
    except discord.errors.HTTPException:
        await msg.channel.send(f'Could not send output log.```Exit Code: {res["exitcode"]}```', reference=msg)


def init_thread(msg, parent_loop):
    # Start container and try to connect to the API for 2 seconds.
    container = start_container(msg.author.name)
    for _ in range(20):
        try:
            res = req.get(
                f'http://{container.attrs["NetworkSettings"]["IPAddress"]}:1000',
                data={'cmd': msg.content[len(ddock.command_prefix):]}
            ).json()
            if len(res['result']) == 0: res['result'] = ' '
            break
        except req.exceptions.ConnectionError:
            pass
        time.sleep(0.1)
    else:
        res = {
            'exitcode': 1,
            'result': 'Could not connect to container'
        }
        container.stop()
    # Send the message from a coroutine running in the parent loop
    asyncio.run_coroutine_threadsafe(send_result(msg, res), parent_loop)


@ddock.event
async def on_ready():
    print(f'{ddock.user.name} has connect to Discord!')


@ddock.event
async def on_message(msg):
    # If the author of the message is the bot or the message doesn't start with the command prefix, return
    if msg.author == ddock.user or not msg.content.startswith(ddock.command_prefix):
        return

    # Start a new thread to manage the execution of the command. Pass the main event loop as discord messages can only be sent from the main loop
    thread = threading.Thread(target=init_thread, args=(msg, asyncio.get_event_loop()))
    thread.start()


if __name__ == '__main__':
    ddock.run(DDOCK_TOKEN)
