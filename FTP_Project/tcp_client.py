from socket import*
import os , sys

dir = os.getcwd()
HOME = dir                              #--- will hold the dir for the root of the program
ROOT = dir + "/ftpclient/ftproot/"      #--- will hold the dir for the root of the ftpclient folder
RECV_BUFFER = 1024
PORT = 2039
next_data_port = 1
DATA_PORT_MIN = 12000
DATA_PORT_MAX = 12499


CMD_QUIT = "QUIT"                       #--- quits the server
CMD_HELP = "HELP"                       #--- displays help file
CMD_LOGIN = "LOGIN"                     #--- logs in into server
CMD_LOGOUT = "LOGOUT"                   #--- logs out current user
CMD_LS = "LS"                           #--- displays contents of CWD
CMD_DELETE = "DELETE"                   #--- deletes a specific file
CMD_PWD = "PWD"                         #--- diplays the current working directory
CMD_CON = "CONNECT"                     #--- connects to the server
CMD_CDUP = "CDUP"                       #--- moves up in the directory  
CMD_CCD = "CCD"                         #--- changes the directory in the client side
CMD_SCD = "SCD"                         #--- changes the directory in the server side
CMD_RETR = "GET"                        #--- gets a file copy from server CWD into client CWD
CMD_STOR = "PUT"                        #--- places a file copy from client CWD into server CWD
CMD_TEST = "TEST"
CMD_PORT = "PORT"

def tcp_connection( addr , port , sock):
   
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    con = False
    try:
        sock.connect((addr , port ))
        con = True
        sock.send(addr.encode())

    except ConnectionRefusedError:
        print("Connection Error. Try again!")
        con = False


    return sock , con


def main():

    dir = os.getcwd()
    root = dir + "/ftpclient/ftproot/"
    os.chdir(root)

    logged = False      # Will keep track if there is a user logged on
    userName = ''       # Will keep track of the user that is logged on
    connection = False  # Will keep track if there is a connection made
    cmd = ''

    print("Welcome to the TCP Client\n")
    cSock = socket(AF_INET , SOCK_STREAM)

    while (cmd != CMD_QUIT ):

        command = input("\nFTP>> ")
        tokens = command.split()
        cmd , logged , cSock , userName , connection = evaluateCommands(tokens,logged,cSock,userName,connection)

    print("\nThank you for using FTP Client")


def evaluateCommands( tokens , logged , sock , userName , connection):

    cmd = tokens[0].upper()

    if (cmd == CMD_CON):

        host = gethostname()
        host_address = gethostbyname(host)
       
        sock , connection = tcp_connection( '127.0.0.1' , PORT , sock )

        if (connection == True):
            serverReply = sock.recv(RECV_BUFFER).decode()
            print("Server: " + str(serverReply) )

        if (connection == False):
            cmd = ''

        return "" , logged , sock , userName , connection
    #------

    if (cmd == CMD_QUIT):

        logged = False

        if( connection == True):
            sock.send( "QUIT".encode() )

        return "QUIT" , logged , sock , userName , connection
    #------
    if (cmd == CMD_HELP):

        temp = os.getcwd()
        os.chdir(HOME)

        try:

            file = open("ftpserver/conf/help.txt" , "r")
            line = file.readline()
            while (line != ''):
                print(line)
                line = file.readline()

        except FileNotFoundError:
            print("FIle not found")

        file.close()
        os.chdir(temp)

        return "" , logged , sock , userName , connection


    #-----
    if (cmd == CMD_LOGIN):

        reply = False

        if (connection == True):
            reply , logged , sock , userName =_login( tokens , logged , sock , userName )

        else:
            print("Need a connection to login.")
            print("Try to connect first...")
        
        return reply , logged , sock , userName , connection
    
    #Logs out the current user
    if (cmd == CMD_LOGOUT):

        _logout(userName)
        logged = False
        userName = ""
        sock.send("LOGOUT".encode())

        return "" , logged , sock , userName , connection

    # this will retuen the current directory in either the server or the client
    # User can select.
    if (cmd == CMD_PWD):

        if ( len(tokens) == 2):

            clientOrServer = tokens[1].lower()

            if(clientOrServer == 'client'):
                print("\nClient Current Working Dir: ")
                print(os.getcwd())
                return "" , logged , sock , userName , connection

            if(clientOrServer == 'server' and connection == True):
                print("\nServer Current Working Dir: ")
                sock.send("PWD".encode())
                reply = sock.recv(RECV_BUFFER).decode()
                reply_tokens = reply.split()
                
                if (reply_tokens[0] == "530"):
                    print("Need to be logged in ")
                else:
                    print(reply)

                return "" , logged , sock , userName , connection    
           
            else:
                print("\n: cwd [ client ] || [ server ]. Please specify.")
                print("Also, there must be a server conenction in order to execute 'cwd [ server ]'")

        else:
            print("\n : cwd [ client ] | [ server ]. Please specify.")
            print("Also, there must be a server conenction in order to execute 'cwd [ server ]'")

        return "" , logged , sock , userName , connection

    if (cmd == CMD_CDUP):

        if ( len(tokens) == 2):

            clientOrServer = tokens[1].lower()

            if(clientOrServer == 'client'):
                os.chdir(ROOT)
                print("\nClient Current Working Dir: ")
                print(os.getcwd())
                return "" , logged , sock , userName , connection

            if(clientOrServer == 'server' and connection == True):
                print("\nServer Current Working Dir: ")
                sock.send("CDUP".encode())
                cwd = sock.recv(RECV_BUFFER).decode()
                print(cwd)
                return "" , logged , sock , userName , connection    
           
            else:
                print("\nCWD works on [ client ] or [ server ].")
                print("Also, there must be a server conenction in order to get the CWD on [ server ]")

        else:
            print("\n : cwd [ client ] | [ server ]. Please specify.")
            print("Also, there must be a server conenction in order to execute 'cwd [ server ]'")

        return "" , logged , sock , userName , connection

    if (cmd == CMD_LS):

        if (logged == True):
            if ( len(tokens) ==1 ):
                ls = os.listdir(os.getcwd())
                print("\nClient Dir: " + str(os.getcwd()))
                print("\n" + str(ls))
                return "" , logged , sock , userName , connection

            else:
                cli_ser = tokens[1].lower()

                if(cli_ser == "client" ):
                    ls = os.listdir(os.getcwd())
                    print("\nClient Dir: " + str(os.getcwd()))
                    print("\n" + str(ls))
                    return "" , logged , sock , userName , connection

                if(cli_ser == "server" ):
                    sock.send("LS".encode())
                    directory = sock.recv(RECV_BUFFER).decode()
                    print("\nServer Ls: ")
                    print("\n" + str(directory))
                    return "" , logged , sock , userName , connection

        print("Need to log in to navigate dirs.")

        return "" , logged , sock , userName , connection

    #--- changes the dir for client
    if (cmd == CMD_CCD):

        input = tokens[1]
        curdir = os.getcwd()
        dir = curdir + input
        os.chdir(dir)
        print(os.getcwd())

        return "" , logged , sock , userName , connection

    if (cmd == CMD_RETR):

        file_to_open = tokens[1]

        if (connection == False and logged == False):

            print("\nThere needs to be a connecion to the server to use this command.")
            print("Please connect to the server")
            return "" , logged , sock , userName , connection

        data_channel = ftp_new_dataport(sock) #this should be connected when I reach here

        d_channel , addr = data_channel.accept()

        msg = "RETR " + file_to_open
        sock.send( msg.encode() )

        file2 = open( file_to_open , "w")

        while True:

            file = d_channel.recv(RECV_BUFFER).decode()
            tokens = file.split()
            code = tokens[0]
            
            if(code == "150"):

                print("ERROR: File not found...")
                file2.close()
                os.remove(str(file_to_open))

                return "" , logged , sock , userName , connection
               
            if(len(file) < RECV_BUFFER ):
                file2.write(file)        
                break

            else:
                file2.write(file) 

        file2.close()
        d_channel.close()

        print("\n File [ " + file_to_open + " ] has been transfered to the current working directory")
        print("from the remote server.\n")
        

        return "" , logged , sock , userName , connection

    if (cmd == CMD_STOR):

        if (connection == False and logged == False):
            print("\nThere needs to be a connecion to the server to use this command.")
            print("Please connect to the server")
            return "" , logged , sock , userName , connection

        file_to_open = tokens[1]
        
        try:
            f = open( file_to_open , "r" )
            f.close()

        except FileNotFoundError:
            msg = "FIle [ " + file_to_open + " ] not found in your current directory"
            print(msg)

            return "" , logged , sock , userName , connection

        data_channel = ftp_new_dataport(sock) #this should be connected when I reach here
        d_channel , addr = data_channel.accept()    

        msg = "STOR " + file_to_open
        sock.send( msg.encode() )

        with open(file_to_open, 'r') as file_to_send:
            for data in file_to_send:
                d_channel.sendall(data.encode())
            
        file_to_send.close()
        print("CLOSED FILE")

        d_channel.close()

        return "" , logged , sock , userName , connection

    if (cmd == CMD_SCD):

        if(len(tokens) == 2):

            dir_to_change = tokens[1]
            msg = "SCD " + dir_to_change
            sock.send(msg.encode())
            reply = sock.recv(RECV_BUFFER).decode()
            print(reply)

        else:

            print("\nParameters for this command are SCD [ dir ] \nPlease try again.")

        return "" , logged , sock , userName , connection

    if (cmd == CMD_TEST):

        temp = os.getcwd()
        os.chdir(HOME)

        print(os.getcwd())
        test_file = open("tests/file1.txt" , 'r')

        while (cmd != CMD_QUIT ):

            command = test_file.readline()
            tokens = command.split()
            cmd , logged , sock , userName , connection = evaluateCommands(tokens,logged,sock,userName,connection)

        test_file.close()
        print("Finished Test run!")
        os.chdir(temp)

        return "" , logged , sock , userName , connection

    #--- valid commands above this line
    else:
        print("Invalid Command.")
        return "" , logged , sock , userName , connection



def _logout(userName):

    if(userName == ""):
        print("No user is logged on...")
    else:
        print("Loggin out " + userName + ".")
        logged = False


def _login(tokens , logged , sock , userName  ):

    user = ''
    pw = ''

    if(userName != ""):
        print("\nSession already in use...")
        print("Logout to change users.")

        return "" , logged , sock , userName

    else:

        if(len(tokens) == 1):
            
            user = input("Please Enter UserName: ")
            msg = "USER " + user
            sock.send(msg.encode())
            
            pw = input("Please Enter Password: ")
            msg2 = "PASS " + pw
            sock.send(msg2.encode())
            print("\nAttempting to connect user [ " + user + " ]")
            answer = sock.recv(RECV_BUFFER).decode()

            ans_tokens = answer.split()
            ans = ans_tokens[0]
            
            if(ans == "230"):
                userName = user
                print("\nLogin Successful! Welcome, " + userName + ".")
                user = userName
                dir = ROOT + user + "/"
                os.chdir(dir)
                logged = True

            else:
                print("Invalid username or password...")
                print("Try again!")            

            return "" , logged , sock , userName

        if(len(tokens) == 3):

            user = tokens[1]
            pw = tokens[2]
            print("\nAttempting to connect user [ " + user + " ]")
            msg = "USER " + user
            sock.send(msg.encode())
            msg = "PASS " + pw
            sock.send(msg.encode())
            answer = sock.recv(RECV_BUFFER).decode()
        
            ans_tokens = answer.split()
            ans = ans_tokens[0]

            if(ans == "230"):
                userName = user
                print("Login Successful! Welcome, " + userName + ".")
                user = userName
                dir = ROOT + user + "/"
                os.chdir(dir)
                logged = True

            else:
                print("Invalid username or password...")
                print("Try again!")
            
            return answer , logged , sock , userName


        return "Invalid Login, try again" , logged , sock , userName

def ftp_new_dataport(ftp_socket):

    global next_data_port

    dport = next_data_port

    next_data_port = next_data_port + 1 #for next next
    dport = (DATA_PORT_MIN + dport) % DATA_PORT_MAX

    print(("Preparing Data Port: 127.0.0.1 " + str(dport)))

    data_socket = socket(AF_INET, SOCK_STREAM)
    # reuse port
    data_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    data_socket.bind(('127.0.0.1' , dport))
    data_socket.listen( 1 )
    '''
    #the port requires the following
    #PORT IP PORT
    #however, it must be transmitted like this.
    #PORT 192,168,1,2,17,24
    #where the first four octet are the ip and the last two form a port number.
    host_address_split = host_address.split('.')
    high_dport = str(dport // 256) #get high part
    low_dport = str(dport % 256) #similar to dport << 8 (left shift)
    port_argument_list = host_address_split + [high_dport,low_dport]
    port_arguments = ','.join(port_argument_list)
    '''
    cmd_port_send = CMD_PORT + ' ' + str(dport) + '\r\n'
    print(cmd_port_send)

    try:
        ftp_socket.send(cmd_port_send.encode())

    except socket.timeout:
        print("Socket timeout. Port may have been used recently. wait and try again!")
        return None

    except socket.error:
        print("Socket error. Try again")
        return None
    msg = ftp_socket.recv(RECV_BUFFER).decode()
    print(msg)

    return data_socket


main()
