import socket, select
import os
import subprocess
import json
import hashlib
import thread
import time
import sys	
import glob 



RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
CONNECTION_LIST=[]
UDPCONNECTION_LIST=[]




def server():
	# List to keep track of socket descriptors
	CONNECTION_LIST = []
	UDPCONNECTION_LIST = []
	RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
	PORT = 50000
	 
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# this has no effect, why ?
	server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_socket.bind(("0.0.0.0", PORT))
	server_socket.listen(10)
 
	# Add server socket to the list of readable connections
	CONNECTION_LIST.append(server_socket)
 
	print "Server started on port " + str(PORT)
	
	


	while 1:
		# Get the list sockets which are ready to be read through select
		read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
 
		for sock in read_sockets:
			#New connection
			if sock == server_socket:
				# Handle the case in which there is a new connection recieved through server_socket
				sockfd, addr = server_socket.accept()
				CONNECTION_LIST.append(sockfd)
				print "Client (%s, %s) connected" % addr             
			#Some incoming message from a client
			else:
				# Data recieved from client, process it
				try:
					#In Windows, sometimes when a TCP program closes abruptly,
					# a "Connection reset by peer" exception will be thrown
					data = sock.recv(RECV_BUFFER)
					print data
					qry = json.loads(data)
					print qry['id']
					
					if qry['id'] == "1":
						response = ""
						proc = subprocess.Popen(['ls -l'], stdout=subprocess.PIPE, shell=True)
						(out, err) = proc.communicate()
						response = str(out)
						sock.send(response)

					if qry['id'] == "3":
						print "hi"
						response = ""
						x = ""
						x = 'ls -l '+qry['args']
						print x
						proc = subprocess.Popen([x], stdout=subprocess.PIPE, shell=True)
						(out, err) = proc.communicate()
						response = str(out)
						sock.send(response)

					if qry['id'] == "4":
						timestamp = str(os.path.getmtime(qry['args']))
						filename = str(qry['args'])
						md5hash = str(hashlib.md5(filename).hexdigest())
						resp_json = {'filename' : filename , 'md5hash' : md5hash , 'timestamp': timestamp}

						response = json.dumps(resp_json)
						sock.send(response)

					if qry['id'] == "5":
						resp_json = []
						for file in os.listdir("."):
							print file
							timestamp = str(os.path.getmtime(file))
							filename = str(file)
							md5hash = str(hashlib.md5(open(filename,'rb').read()).hexdigest())
							resp_json.append({'filename' : filename , 'md5hash' : md5hash , 'timestamp': timestamp})

						print resp_json
						response = json.dumps(resp_json)
						sock.send(response)						

					if qry['id'] == "6":
						f = open(qry['args'],'rb')
						l = f.read(RECV_BUFFER)
						sock.send(l)
						print "l=" + l
						while (l):
							l = f.read(RECV_BUFFER)
							sock.send(l)
						f.close()

					if qry['id'] == "7":
						f = open(qry['args'],'rb')
						l = f.read(RECV_BUFFER)
						#UDP
						try :
							s_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
							print 'Socket created'
						except socket.error, msg :
							print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
							sys.exit()


						# Bind socket to local host and port
						try:
							s_udp.bind(('localhost', 50001))
						except socket.error , msg:
							print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
							sys.exit()
							 
						print 'Socket bind complete'

						d = s_udp.recvfrom(RECV_BUFFER)
						addr = d[1]
						print addr

						while (l):
							# read_sockets,write_sockets,error_sockets = select.select(UDPCONNECTION_LIST,[],[])
							# print write_sockets, read_sockets
							# if(write_sockets[0] == s_udp):
							s_udp.sendto(l , addr)
							l = f.read(RECV_BUFFER)
						f.close()
						s_udp.close()



				except:
					print "Client (%s, %s) is offline" % addr
					sock.close()
					CONNECTION_LIST.remove(sock)
					continue
	 
	server_socket.close()

def client_connect(s):
	try :
		s.connect(('localhost', 60000))
		print "client connected"
		return 
	except :
		time.sleep(3)
		client_connect(s)


def client_manual():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# s.settimeout(2)
	 
	# connect to remote host
	
	client_connect(s)
	CONNECTION_LIST.append(s)

	prompt()
	



def client_auto():
	while(True):
		print "===============SYNCING==============="
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# s.settimeout(2)
		 
		# connect to remote host
		
		client_connect(s)
		CONNECTION_LIST.append(s)

		result=""
		qry = {'id' : '5'}
		n = json.dumps(qry)
		print n
		cmd = n
		s.send(cmd)
		read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
		if(read_sockets[0] == s):
			while True:
				output = s.recv(RECV_BUFFER)

				result+=output
				if len(output) < RECV_BUFFER:
					break
				
		op = json.loads(result)

		cur_files = os.listdir(".")
		for item in op:
			print item['filename'], item['md5hash'], item['timestamp']
			if item['filename'] not in cur_files:
				qry = {'id' : '6' , 'args' : item['filename']}
				n = json.dumps(qry)
				cmd = n
				s.send(cmd)
				read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])

				if(read_sockets[0] == s):
					with open(item['filename'], 'wb') as f:
						print 'file opened'
						k=s.recv(4)
						while True and k!="NULL":
							print('receiving data...')
							data = s.recv(RECV_BUFFER)
							# write data to a file
							f.write(data)
							if len(data) < RECV_BUFFER:
								break
					f.close()
				print "Downloaded"

			else:
				ind = cur_files.index(item['filename'])	
				print str(hashlib.md5(open(cur_files[ind],'rb').read()).hexdigest()), item['md5hash']
				if(str(hashlib.md5(open(cur_files[ind],'rb').read()).hexdigest()) == item['md5hash'] ):
					continue

				else:
					if(float(os.path.getmtime(cur_files[ind])) < float(item['timestamp'])):
						print "here"
						qry = {'id' : '6' , 'args' : item['filename']}
						n = json.dumps(qry)
						print n
						cmd = n
						s.send(cmd)
						read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])

						if(read_sockets[0] == s):
							with open(item['filename'], 'wb') as f:
								print 'file opened'
								k=s.recv(4)
								while True and k!="NULL":
									print('receiving data...')
									data = s.recv(RECV_BUFFER)
									# write data to a file
									f.write(data)
									if len(data) < RECV_BUFFER:
										break
							f.close()
						print "Downloaded"
		time.sleep(5)	



	 


def prompt():
	result = ""
	global CONNECTION_LIST, RECV_BUFFER
	s=CONNECTION_LIST[0]
	inp = raw_input("Prompt > ")
	query = inp.split(' ')
	print query
	if(query[0] == "index"):
		if(query[1] == "longlist"):
			qry = {'id' : '1'}
			n = json.dumps(qry)
			print n
			cmd = n
			s.send(cmd)
			read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
			if(read_sockets[0] == s):
				while True:
					output = s.recv(RECV_BUFFER)	
					result+=output
					if len(output) < RECV_BUFFER:
						break
					
			print result

	# if(query[1] == "shortlist"):

		if(query[1] == "regex"):
			qry = {'id' : '3' , 'args' : query[2]}
			n = json.dumps(qry)
			print n
			cmd = n
			s.send(cmd)
			read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
			if(read_sockets[0] == s):
				while True:
					output = s.recv(RECV_BUFFER)	
					result+=output
					if len(output) < RECV_BUFFER:
						break
					
			print result

	if(query[0] == "hash"):
		if(query[1] == "verify"):
			qry = {'id' : '4' , 'args' : query[2]}
			n = json.dumps(qry)
			print n
			cmd = n
			s.send(cmd)
			read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
			if(read_sockets[0] == s):
				while True:
					output = s.recv(RECV_BUFFER)
	
					result+=output
					if len(output) < RECV_BUFFER:
						break
					
			op = json.loads(result)
			print op['filename'], op['md5hash'], op['timestamp']

		if(query[1] == "checkall"):
			qry = {'id' : '5'}
			n = json.dumps(qry)
			print n
			cmd = n
			s.send(cmd)
			read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
			if(read_sockets[0] == s):
				while True:
					output = s.recv(RECV_BUFFER)
	
					result+=output
					if len(output) < RECV_BUFFER:
						break
					
			op = json.loads(result)

			for item in op:
				print item['filename'], item['md5hash'], item['timestamp']

	

	if(query[0] == "download"):
		if(query[1] == "TCP"):
			qry = {'id' : '6' , 'args' : query[2]}
			n = json.dumps(qry)
			print n
			cmd = n
			s.send(cmd)
			read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])

			if(read_sockets[0] == s):
				with open(query[2], 'w+b') as f:
					print 'file opened'
					k = s.recv(4)
					

					while True and k!="NULL":
						print('receiving data...')
						data = s.recv(RECV_BUFFER)
						# write data to a file
						f.write(data)
						if len(data) < RECV_BUFFER:
							break

				f.close()
					
			print "Downloaded"



		if(query[1] == "UDP"):
			qry = {'id' : '7' , 'args' : query[2]}
			n = json.dumps(qry)
			print n
			cmd = n
			s.send(cmd)
			try:
				s_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			except socket.error:
				print 'Failed to create socket'
				sys.exit()
			UDPCONNECTION_LIST.append(s_udp)
			s_udp.sendto("SEND", ('localhost', 60001))
			k = s_udp.recvfrom(4)
			print k
			with open(query[2], 'wb') as f:
				print 'file opened'
				while True and k!="":
					print('receiving data...')
					# read_sockets,write_sockets,error_sockets = select.select(UDPCONNECTION_LIST,[],[])
					# if(read_sockets[0] == s_udp)
					data = s_udp.recvfrom(RECV_BUFFER)
					print data[1]
					# write data to a file
					f.write(data[0])
					if len(data[0]) < RECV_BUFFER:
						break
			s_udp.close()            
			f.close()
					
			print "Downloaded"
			read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
			if(read_sockets[0] == s):
				while True:
					output = s.recv(RECV_BUFFER)
	
					result+=output
					if len(output) < RECV_BUFFER:
						break
					
			op = json.loads(result)
			if(op['md5hash'] == str(hashlib.md5(open(query[2],'rb').read()).hexdigest())):
				print "HASH MATCHES"
			else:
				print "HASH MISMATCH"

	if(query[0] == "sync"):
		qry = {'id' : '5'}
		n = json.dumps(qry)
		print n
		cmd = n
		s.send(cmd)
		read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])
		if(read_sockets[0] == s):
			while True:
				output = s.recv(RECV_BUFFER)

				result+=output
				if len(output) < RECV_BUFFER:
					break
				
		op = json.loads(result)

		cur_files = os.listdir(".")
		for item in op:
			print item['filename'], item['md5hash'], item['timestamp']
			if item['filename'] not in cur_files:
				qry = {'id' : '6' , 'args' : item['filename']}
				n = json.dumps(qry)
				cmd = n
				s.send(cmd)
				read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])

				if(read_sockets[0] == s):
					with open(item['filename'], 'wb') as f:
						print 'file opened'
						while True:
							print('receiving data...')
							data = s.recv(RECV_BUFFER)
							# write data to a file
							f.write(data)
							if len(data) < RECV_BUFFER:
								break
					f.close()
				print "Downloaded"

			else:
				ind = cur_files.index(item['filename'])	
				print str(hashlib.md5(open(cur_files[ind],'rb').read()).hexdigest()), item['md5hash']
				if(str(hashlib.md5(open(cur_files[ind],'rb').read()).hexdigest()) == item['md5hash'] ):
					continue

				else:
					if(float(os.path.getmtime(cur_files[ind])) < float(item['timestamp'])):
						print "here"
						qry = {'id' : '6' , 'args' : item['filename']}
						n = json.dumps(qry)
						print n
						cmd = n
						s.send(cmd)
						read_sockets,write_sockets,error_sockets = select.select(CONNECTION_LIST,[],[])

						if(read_sockets[0] == s):
							with open(item['filename'], 'wb') as f:
								print 'file opened'
								while True:
									print('receiving data...')
									data = s.recv(RECV_BUFFER)
									# write data to a file
									f.write(data)
									if len(data) < RECV_BUFFER:
										break
							f.close()
						print "Downloaded"

	prompt()




def print_time( threadName, delay):
   count = 0
   while count < 5:
      time.sleep(delay)
      count += 1
      print "%s: %s" % ( threadName, time.ctime(time.time()) )

try:
	print sys.argv
	thread.start_new_thread( server, () )
	if(sys.argv[1] == "auto"):
		thread.start_new_thread( client_auto, () )
	elif(sys.argv[1] == "manual"):
		thread.start_new_thread( client_manual, () )


except:
	print "Error: unable to start thread"

while 1:
   pass