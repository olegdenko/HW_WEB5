import asyncio
import logging
import websockets
import platform
import names
import aiohttp
import json

from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK


API = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5"


async def get_exchange():
    async with aiohttp.ClientSession() as session:
        async with session.get(API) as response:
            # result, *_ = list(filter(lambda el: el['ccy'] == 'USD', response))
            data = await response.json()
            result = json.dumps(data)
            # return f"USD: buy: {result['buy']}, sale: {result['sale']}"
            print(result)
            return result


class Server:
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
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                r = await get_exchange()
                await self.send_to_clients(r)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main())
    print(r)
