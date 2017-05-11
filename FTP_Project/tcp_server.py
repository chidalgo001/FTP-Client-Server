
from socket import*
import threading
import os
import sys

# global variable
tList = []
MAX_DIR = ''
#--- constants

HOME = os.getcwd()
PORT = 2039
DATA_PORT_MIN = 12000
DATA_PORT_MAX = 12499
FTP_SERVICE_PORT = 2154
next_port = 1
localhost = '127.0.0.1'
BUFFER = 1024

#---

def commands( tokens , logon , sock , root , dir , status , dataSock):

    cmd = tokens[0].upper()
    global MAX_DIR

    if( cmd == "QUIT" ):
        _quit(sock)

        return "QUIT" , logon , sock , root , dir , status , dataSock
    
    # will search for a user in the users.cfg file
    if( cmd == "USER" ):

        user = tokens[1]
        dir = root + user + "/"

        command = sock.recv(BUFFER).decode()
        pwd = command.split()
        password = pwd[1]

        found , pw , status = searchsn( user )
        
        if (found == True and pw == password):
            print("\nClient User: " + user + " has logged on")
            print("User Status: \n" + status)

            if(status == "blocked"):
                sock.send("530 Not logged in".encode())
                print("\nNOTE: User is Blocked")

            elif (status == "notallowed"):
                sock.send("530 Not logged in".encode())
                print("\nNOTE: User is not allowed")

            else:
                sock.send("230 User logged in".encode())
                logon = True
                os.chdir(dir)
      
        else:

            print("\nUser Not Found")
            sock.send("False".encode())
    
        if( status == "user"):
            MAX_DIR = os.getcwd()

        else:
            MAX_DIR = root

        print(MAX_DIR)
        return "USER" , logon , sock , root , dir , status , dataSock

    #------

    if ( cmd == "LOGOUT"):

        dir = root #--- READ! this could be a problem for the threads
        os.chdir(HOME)
        logon = False
        status  = " "

        return "LOGOUT" , logon , sock , root , dir , status , dataSock

    #------

    if ( cmd == "PWD" ):
        
        if (logon == False):
            print("Client tried to access dir with no login")
            sock.send("530 Not logged in".encode())

        else:
            print("Client requested CWD.")
            sock.send(os.getcwd().encode())

        return "CWD" , logon , sock , root , dir , status , dataSock
    
    #-----

    if ( cmd == "CDUP" ):

        try:
            dir = MAX_DIR   
            os.chdir( dir )
            print("Client requested CDUP.")
            sock.send( os.getcwd().encode() )

        except FileNotFoundError:

            print("Error in directory request")
            sock.send("Error in directory request".encode())

        return "CDUP" , logon , sock , root , dir , status , dataSock

    #-----

    if ( cmd == "SCD"):
        
        temp = dir
        newDir = tokens[1]
        dir = dir + newDir
     
        try:
            
            os.chdir(dir)
            sock.send("good".encode())
            print(dir)

        except FileNotFoundError:

            print("Error in directory request")
            sock.send("Error in directory request".encode())
            dir = temp

        return "CDUP" , logon , sock , root , dir , status , dataSock
    
    #-----

    if ( cmd == "LS" ):

        ls = os.listdir( os.getcwd() )
        sock.send( str(ls).encode() )
        print(ls)
        return "LS" , logon , sock , root , dir , status , dataSock
    
    #-----

    if ( cmd == "RETR"):

        file = tokens[1]

        try:

            with open(file, 'r') as file_to_send:
                for data in file_to_send:
                    dataSock.sendall(data.encode())
            
            file_to_send.close()
            print("CLOSED FILE")

        except FileNotFoundError:

            msg = "150 FIle Not Found"
            dataSock.send(msg.encode())

        return "RETR" , logon , sock , root , dir , status , dataSock

    if ( cmd == "STOR"):

        filename = tokens[1]
        file = open( filename , 'w' )

        while True:

            input = dataSock.recv(BUFFER).decode()
            if(len(input) < BUFFER ):
                file.write(input)        
                break

            else:
                file.write(input) 

        return "STOR" , logon , sock , root , dir , status , dataSock

    if ( cmd == "PORT"):

        dataSock = socket(AF_INET , SOCK_STREAM)
        dataSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        data_port = tokens[1]

        try:
            print("Creating data port")
            data_port = int(data_port)

            dataSock.connect((localhost , data_port))

            msg = "Connected on data port: " + str(data_port)
            print(msg)
            sock.send(msg.encode())
            print("Data channel created on port " + str(data_port))

        except ConnectionRefusedError:
            print("Connection Error. Try again!")

        return "PORT" , logon , sock , root , dir , status , dataSock

    else:

        return "Invalid Command" , logon , sock , root , dir , status , dataSock


# helper function that will look for the user name in the file
def searchsn( username ):
    
    temp = os.getcwd()

    try:

        
        os.chdir(HOME)
        file = open("ftpserver/conf/users.cfg" , "r")
        found = False

        record = file.readline()#this will read line by line
        sn = record.split()
        user = sn[0]

        while ( user != username and record != "" ):
        
            record = file.readline()
            if(record != ""):
                sn = record.split()
                user = sn[0]
            if( user == username ):
                found = True
    
        pw = sn[1]
        status = sn[2]
        file.close()
        os.chdir(temp)
        if (found == True or user == username):
            return True , pw , status

    except FileNotFoundError:
        print("error loggin in")
        os.chdir(temp)

        return False , "" , ""

def _quit(sock):
    print("Quit")

def joinAll():
    global tList 
    for t in tList:
        t.join()   

def servThread( cSock , addr):

    dir = threading.local()
    root = threading.local()
    #HOME = threading.local()
    loggedon = threading.local()
    con = threading.local()
    sentence = threading.local()

    dir = os.getcwd()
    root = dir + "/ftpserver/ftproot/"
    HOME = root
    print("THREAD HOME: " , dir)
    
    dataSock = ''
   # dataSock = socket(AF_INET , SOCK_STREAM)
   # dataSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    loggedon = False

    status = " "

    #--------------------------------
    con = cSock.recv(1024).decode()
    #print("Client connection: " + con)

    cSock.send("Connected!".encode())
    #this should be the first time it gets a command

    sentence = cSock.recv(2048).decode()

    tokens = sentence.split()
    command,loggedon,sSock,root,dir,status,dataSock = commands( tokens,loggedon,cSock,root,dir,status,dataSock)

    print("Client input: " , command)

    while (command != "QUIT"):
    
        sentence = cSock.recv(1024).decode()
        tokens = sentence.split()
        command,loggedon,sSock,root,dir,status,dataSock = commands( tokens,loggedon,cSock,root,dir,status,dataSock )
        print("Client input: " , command)
        if (command == "LOGOUT"):
            os.chdir(HOME)
            dir = HOME

    
    print("\nClient 'QUIT' cmd was received...")
    cSock.close()
    #sys.exit(0)
    



def main():

    dir = os.getcwd()
    root = dir + "/ftpserver/ftproot/"
    ##os.chdir(root)
    
    HOME = root

    host = gethostname()
    host_address = gethostbyname(host)

    try:

        global tList
        serverSock = socket(AF_INET , SOCK_STREAM)
        serverSock.bind((localhost , PORT))
        serverSock.listen(1) 

        print("\nThe server is ready to receive... ")
        
        
        #while True:
  
        clientSock , addr = serverSock.accept()
        os.chdir(dir)
        t = threading.Thread(target = servThread , args = (clientSock , addr))
        t.start()
        tList.append(t)
        print("Thread Started")
        #-------

    except KeyboardInterrupt:
        joinAll()

    sys.exit(0)

    


main()