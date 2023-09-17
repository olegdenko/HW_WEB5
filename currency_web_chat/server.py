import asyncio
import logging
import websockets
import platform
import names
import aiofiles
from aiopath import AsyncPath
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime

from get_currency import get_exchange

stop_event = asyncio.Event()


class Server:
    def __init__(self):
        self.shutdown = False

    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "killall":
                await self.send_to_clients("Server is shutting down...")
                await self.stop_server()
            elif message.startswith("exchange"):
                parts = message.split()
                if len(parts) == 2 and parts[1].isdigit():
                    days = min(int(parts[1]), 10)
                else:
                    days = 0

                r = await get_exchange(days)
                await self.send_to_clients(f"The currency were: {r} - {days} ago.")
                await self.log_exchange_to_file(ws.name, days)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def stop_server(self):
        for ws in self.clients:
            await ws.close()
        stop_event.set()

    async def log_exchange_to_file(self, username, days):
        date_str = datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        log_message = (
            f"{date_str} {username} executed 'exchange' command for {days} days."
        )
        async with aiofiles.open("exchange.log", mode="a") as log_file:
            await log_file.write(log_message + "\n")


def handle_exit():
    logging.info("Server is shutting down...")
    stop_event.set()
    loop.stop()


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await stop_event.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
