import threading
from tests.serv_socket import echo_server
from scket import simple_client

HOST = ''
port = 5000

srver = threading.Thread(target=echo_server)
client = threading.Thread(target=simple_client)
