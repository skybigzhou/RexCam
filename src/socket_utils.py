import socket
import time
import SocketServer
import struct
import os
import thread
import commands


def return_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 80))
	return s.getsockname()[0]


def send_file(conn, model_path):
	try:
		assert os.path.isfile(model_path)
		fileinfo_size = struct.calcsize('128sl')

		fhead = struct.pack('128sl', os.path.basename(model_path), os.stat(model_path).st_size)
		conn.send(fhead)
		
		f = open(model_path, "rb")
		while True:
			filedata = f.read(1024)
			if not filedata:
				break
			conn.send(filedata)
		f.close()
	except Exception:
		print "No Such File"


def recv_file(conn, model_path):
	# conne.settimeout(60)
	# print "Start Receiving"

	fileinfo_size = struct.calcsize('128sl')
	buf = conn.recv(fileinfo_size)
	if buf:
		filename, filesize = struct.unpack('128sl', buf)
		filename_f = filename.strip('\00')
		recv_size = 0

		file = open(model_path, "wb")
		
		while not recv_size == filesize:
			if filesize - recv_size > 1024:
				raw_data = conn.recv(1024)
				recv_size = recv_size + len(raw_data)
			else:
				raw_data = conn.recv(filesize - recv_size)
				recv_size = filesize

			file.write(raw_data)

		file.close()
		

def create_server_socket():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	host = return_local_ip()
	port = 5555
	s.bind((host, port))
	s.listen(5)
	return s


def create_client_socket(ip):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	port = 5555
	s.connect((ip, port))
	return s
