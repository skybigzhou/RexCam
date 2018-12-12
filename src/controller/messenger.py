import sys
import os
from src.socket_utils import *
from threading import Thread

def send_message():
    # TODO: find ip address from metadata
    ip = 'localhost'
    conn = create_client_socket(ip, 2)

    # TODO: what instruction to send
    ins = "None Instruction Right Now"
    conn.send(ins)

    res = conn.recv(1024)
    if res == "ACK":
        print("[CRTL] Receive ACK from remote")
        conn.close()


def trigger():
    server = create_server_socket(2)

    def handle_client_connection(conn):
        # msg format = |...ip...|..func..|..res...|
        msg = conn.recv(1024)
        ip, func, res = msg.split(",")
        print("[CRTL] Get Results {0:20} from [ip:{1}]. Start {2} ...".format(res, ip, func))

        # TODO: deal with instruction
        send_message()

        conn.send("ACK")
        conn.close()

    while True:
        print("[CRTL] Controller start listening")
        conn, address = server.accept()
        print("[CRTL] Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target = handle_client_connection, name = "Trigger")
        client_handler.start()



def main():
    listener = Thread(target = trigger, name="TriggerListener")
    # rolling
    while True:
        pass


if __name__=="__main__":
    main()