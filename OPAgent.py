import socket, threading, select, SocketServer, SimpleHTTPServer
import platform, os, shutil, subprocess, urllib, ConfigParser


BUFLEN = 8192
VERSION = 'Python Proxy'
HTTPVER = 'HTTP/1.1'

class ConnectionHandler(SocketServer.BaseRequestHandler):
    global BUFLEN
    global host_dir

    def handle(self):
        self.client = self.request
        
        self.client_buffer = ''
        self.timeout = 30
        self.method, self.path, self.protocol = self.get_base_header()
        if self.method=='CONNECT':
            self.method_CONNECT()
        elif self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT',
                             'DELETE', 'TRACE'):
            self.method_others()
        self.client.close()
        self.target.close()

    def get_base_header(self):
        while 1:
            self.client_buffer += self.client.recv(BUFLEN)
            end = self.client_buffer.find('\n')
            if end != -1:
                break
        print '%s'%self.client_buffer[:end]#debug
        data = (self.client_buffer[:end+1]).split()
        self.client_buffer = self.client_buffer[end+1:]
        return data

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTPVER+' 200 Connection established\n'+
                         'Proxy-agent: %s\n\n'%VERSION)
        self.client_buffer = ''
        self._read_write()        

    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find('/')
        host = self.path[:i]        
        path = self.path[i:]
        self._connect_target(host)
        self.target.send('%s %s %s\n'%(self.method, path, self.protocol)+
                         self.client_buffer)
        self.client_buffer = ''
        self._read_write()

    def _connect_target(self, host):
        i = host.find(':')
        if i!=-1:
            port = int(host[i+1:])
            host = host[:i]
        else:
            port = 80
        (soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
        if host in host_dir:
            address = (host_dir[str(host)], port)
        self.target = socket.socket(soc_family)
        self.target.connect(address)

    def _read_write(self):
        time_out_max = self.timeout/3
        socs = [self.client, self.target]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
                    if in_ is self.client:
                        out = self.target
                    else:
                        out = self.client
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break



class WebProxy():
    def __init__(self):
        self.server = None


    def start(self, host='127.0.0.1', port=9999, IPv6=False, timeout=60,
                      handler=ConnectionHandler):

        print "Start proxy server"

        self.server = SocketServer.ThreadingTCPServer((host, port), handler)
        self.server.allow_reuse_address = True
        self.server.socket.setblocking(0)
        proxy_thread = threading.Thread(target=self.server.serve_forever)
        #proxy_thread.setDaemon(True)
        proxy_thread.start()

    def stop(self):
        if self.server is not None:
            print "Stop proxy server"
            self.server.shutdown()
            self.server.server_close()


class WebServer():
    def __init__(self):
        self.server = None

    def start(self,host = '127.0.0.1', port=9000):

        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        self.server = SocketServer.TCPServer((host, port), handler)
        self.server.allow_reuse_address = True
        #self.server.socket.setblocking(0)
        httpd_thread = threading.Thread(target=self.server.serve_forever)
        httpd_thread.setDaemon(True)
        httpd_thread.start()

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()

def getdata():
    global host_dir

    urllib.getproxies = lambda x=None: {}
    localfile = ConfigParser.ConfigParser()
    serverfile = ConfigParser.ConfigParser()

    if (not os.path.isfile('config.ini')) or (not os.path.isfile('Hosts')):
        urllib.urlretrieve("https://raw.github.com/JinZhi/OPAgent/master/config.ini", "config.ini")
        urllib.urlretrieve("https://raw.github.com/JinZhi/OPAgent/master/Hosts", "Hosts")
        localfile.read('config.ini')
    else:
        urllib.urlretrieve("https://raw.github.com/JinZhi/OPAgent/master/config.ini", "temp.ini")
        localfile.read('config.ini')
        serverfile.read('temp.ini')
        if serverfile.getint("Version", "version") > localfile.getint("Version", "version"):
            print 'Data file update'
            urllib.urlretrieve("https://raw.github.com/JinZhi/OPAgent/master/config.ini", "config.ini")
            urllib.urlretrieve("https://raw.github.com/JinZhi/OPAgent/master/Hosts", "Hosts")
        os.remove(os.path.basename('temp.ini'))

    infile = file('Hosts', 'r')
    googleurl = []
    host_dir = {}

    for line in infile:
        if (line == '' or line.startswith(";") or line.startswith("#") or line.startswith("\n")):
            continue
        else:
            temp = []
            line = line.replace('\n', '')
            temp = line.split('\t')
            host_dir[str(temp[1])] = temp[0]
            googleurl.append(temp[1])

    googlehost = []

    i = 0
    while i < len(googleurl):
        temp1 = googleurl[i].split('.')
        if 'hk' in temp1:
            temp2 = '.' + temp1[-3] + '.' + temp1[-2] + '.' + temp1[-1]
        else:
            if len(temp1) > 2:
                temp2 = '.' + temp1[-2] + '.' + temp1[-1]
            else:
                temp2 = temp1[-2] + '.' + temp1[-1]
        if temp2 not in googlehost:
            googlehost.append(temp2)
        i = i + 1

    localfile.read('config.ini')

    proxy = localfile.items("Proxy")
    file_object = open('proxy.pac', 'w')
    file_object.write("function FindProxyForURL(url, host) {\n")

    i = 0
    while i < len(proxy):
        file_object.write('\t%s = "PROXY %s; DIRECT";\n' % proxy[i])
        i = i + 1
    file_object.write('\tgoogle_cn = "PROXY 127.0.0.1:9999; DIRECT";\n')
    file_object.write('\tDEFAULT = "DIRECT";\n')

    i = 0
    while i < len(googlehost):
        if i == 0:
            file_object.write('\tif (dnsDomainIs(host, \'' + googlehost[i] + '\') ||\n')
        else:
            if i == len(googlehost) - 1:
                file_object.write('\t    dnsDomainIs(host, \'' + googlehost[i] + '\'))\n')
            else:
                file_object.write('\t    dnsDomainIs(host, \'' + googlehost[i] + '\') ||\n')
        i = i + 1

    file_object.write('\t{\n')
    i = 0
    while i < len(proxy):
        temp = []
        temp = proxy[i][1].split(".")
        officeip = temp[0] + '.' + temp[1] + '.0.0'
        file_object.write('\t\tif (isInNet(myIpAddress(), "%s", "255.255.0.0")) return %s;\n' % (officeip, proxy[i][0]))
        i = i + 1

    file_object.write('\t\treturn google_cn;\n')
    file_object.write('\t}\n')

    i = 0
    while i < len(proxy):
        temp = []
        temp = proxy[i][1].split(".")
        officeip = temp[0] + '.' + temp[1] + '.0.0'
        file_object.write('\tif (isInNet(myIpAddress(), "%s", "255.255.0.0")) return %s;\n' % (officeip, proxy[i][0]))
        i = i + 1
    file_object.write('\treturn DEFAULT;\n')
    file_object.write('}\n')
    file_object.close()

def mychrome():
    ostype = platform.system()
    osarch = platform.architecture()[0]

    pacpath = 'http://localhost:9000/proxy.pac'

    if ostype == 'Windows':
        userdata = os.environ['USERPROFILE'] + '\\ogmail'

        print pacpath

        if osarch == '32bit':
            chrome = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
        else:
            chrome = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'

        cmd_chrome = [str(chrome), str(" --user-data-dir=" + userdata), str(" --proxy-pac-url=" + pacpath),
                      str(" mail.ogilvy.com")]

    elif ostype == 'Darwin':
        userdata = os.environ['HOME'] + '/ogmail'

        chrome = '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome'
        #chrome = 'open /Applications/Google\\ Chrome.app --args '
        cmd_chrome = str(chrome) + str(" --user-data-dir=" + userdata) + str(" --proxy-pac-url=" + pacpath) + str(
            " mail.ogilvy.com")

    if os.path.isdir(userdata):
        shutil.rmtree(userdata)

    if not os.path.isdir(userdata):
        os.makedirs(userdata)

    #subprocess.Popen(cmd_chrome, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #cmd=subprocess.Popen(cmd_chrome, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    cmd = subprocess.check_call(cmd_chrome, shell=True)

    return cmd

if __name__ == '__main__':
    w=WebServer()
    p=WebProxy()

    w.stop()
    p.stop()

    getdata()

    w.start()
    p.start()

    c = mychrome()

    if c == 0:
        w.stop()
        p.stop()
    exit
