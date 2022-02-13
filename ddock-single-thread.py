import os
import docker
import discord
from time import sleep
from discord.ext import commands
from dotenv import load_dotenv
import requests as r

# Load the .env file which contains the bot token
load_dotenv()
DDOCK_TOKEN = os.getenv('DDOCK_TOKEN')


class DDockDaemon:
    # Helper class to interface with docker
    def __init__(self):
        self.dockerClient = docker.from_env()
        self.image = 'ddock-sys'
        self.tag = 'v1-8'

    def startContainer(self, user: str):
        """
        Starts a container for a user

        :param user: A discord user name
        :return: Running container object
        """
        # If the user did not previously have a container, create one
        if user in [cont.name for cont in self.dockerClient.containers.list(all=True)]:
            container = self.dockerClient.containers.get(user)
        else:
            container = self.dockerClient.containers.create(f'{self.image}:{self.tag}', detach=True, name=user)

        # Start the container and and wait for it to fully start
        container.start()
        while not container.attrs['State']['Running']: container.reload()

        return container

    def containerExec(self, ip_addr: int, cmd: str) -> dict:
        """
        Executes a command inside the container by performing an HTTP GET request to the running daemon

        :param ip_addr: IP address of the container to contact
        :param cmd: Command to execute
        :return: The result of the command
        """
        # Try to contact the container for 10 X 0.1 = 1s. If the container failed to respond, exit with failure
        for _ in range(10):
            try:
                res: r.Response = r.get('http://' + ip_addr + ':1000', data={'cmd': cmd})
                return res.json()
            except r.exceptions.ConnectionError:
                pass
            sleep(0.1)
        return {'exitcode': 1, 'result': 'Could not start container\n'}


# The bot client and Daemon client
ddock = commands.Bot(command_prefix='$ ')
ddd = DDockDaemon()

@ddock.event
async def on_ready():
    print(f'{ddock.user.name} has connected to Discord!')

@ddock.event
async def on_message(msg):
    # Ignore the event if the message was sent by the bot or does not end with the command prefix '$ '
    if msg.author == ddock.user or not msg.content.startswith(ddock.command_prefix):
        return

    # Start the user's container
    container = ddd.startContainer(msg.author.name)
    # Execute the command inside the container and stop the container
    res: dict = ddd.containerExec(container.attrs['NetworkSettings']['IPAddress'], msg.content[len(ddock.command_prefix):])
    container.stop()
    # Populate the result if it was empty
    if len(res['result']) == 0: res['result'] = ' '

    # Send the result
    try:
        await msg.channel.send(f'```Exit Code: {res["exitcode"]}``````{res["result"]}```', reference=msg)
    except discord.errors.HTTPException:
        await msg.channel.send(f'Could not send output log.```Exit Code: {res["exitcode"]}```')


if __name__ == '__main__':
    ddock.run(DDOCK_TOKEN)
