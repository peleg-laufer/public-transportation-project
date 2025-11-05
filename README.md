# public-transportation-project
A python and SQL project of an app giving clients real info about public transportation lines in israel. 

**Link to project:** https://github.com/peleg-laufer/public-transportation-project

## How to run:

download the files from the link or clone the repo to your device

**Server Setup:**

1. make sure you have internet connection

2. run moovit_server

3. now the program will download the needed files and transfer all the data to a new SQL server

4. after it is finished the console will say "waiting" (waiting for a client)

**Client:**

1. open the client program code (moovit_client.py)

2. make sure the port and ip (self.server_port, self.server_ip in moovit_client.py) matches the server's machine ip and port (machine's ip, self.port in moovit_server.py)

3. run moovit_client.py


## How It's Made:

**Tech used:** Python, SQLite, Socket, Threading

The project was written as a graduating high school project in Python. Self learned SQL, Git to make it.

The project was written in 2020 which means no AI involved.

## Optimizations

At first the search for routes in the DB took 10-20 minutes which is way too much. Optimized it by adding INDEX for the columns needed, that makes a binary tree for that column and shortens the search time.
Shortened the overall search time to 20 secs-2 mins.

## Lessons Learned:

Learned how to learn. while teaching myself how to use SQL I have learned a lot of skills regarding self learning of new technologies.
