import wx
import socket
import threading
import select
import SocketServer
import SimpleHTTPServer
import platform
import os
import subprocess
import urllib
import ConfigParser
import shutil
import cStringIO
import zlib
from wx import ImageFromStream, BitmapFromImage
from wx import EmptyIcon

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
        if self.method == 'CONNECT':
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
        print '%s' % self.client_buffer[:end]#debug
        data = (self.client_buffer[:end + 1]).split()
        self.client_buffer = self.client_buffer[end + 1:]
        return data

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTPVER + ' 200 Connection established\n' +\
                         'Proxy-agent: %s\n\n' % VERSION)
        self.client_buffer = ''
        self._read_write()

    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find('/')
        host = self.path[:i]
        path = self.path[i:]
        self._connect_target(host)
        self.target.send('%s %s %s\n' % (self.method, path, self.protocol) +\
                         self.client_buffer)
        self.client_buffer = ''
        self._read_write()

    def _connect_target(self, host):
        i = host.find(':')
        if i != -1:
            port = int(host[i + 1:])
            host = host[:i]
        else:
            port = 80
        (soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
        if host in host_dir:
            address = (host_dir[str(host)], port)
        self.target = socket.socket(soc_family)
        self.target.connect(address)

    def _read_write(self):
        time_out_max = self.timeout / 3
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


    def start(self, host='127.0.0.1', port=9999, IPv6=False, timeout=30,
              handler=ConnectionHandler):
        print "Start proxy server"

        self.server = SocketServer.ThreadingTCPServer((host, port), handler)
        self.server.allow_reuse_address = True
        self.server.socket.setblocking(0)
        #self.server.socket.settimeout(1)
        proxy_thread = threading.Thread(target=self.server.serve_forever)
        #proxy_thread.setDaemon(True)
        proxy_thread.start()

    def stop(self):
        if self.server is not None:
            print "Stop proxy server"
            self.server.shutdown()
            self.server.server_close()


class WebServer():
    global mylog
    mylog = ""

    def __init__(self):
        self.server = None

    def start(self, host='127.0.0.1', port=9000):
        #mylog = "Start web server"
        print "Start web server"
        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        self.server = SocketServer.TCPServer((host, port), handler)
        self.server.allow_reuse_address = True
        #self.server.socket.setblocking(0)
        httpd_thread = threading.Thread(target=self.server.serve_forever)
        httpd_thread.setDaemon(True)
        httpd_thread.start()

    def stop(self):
        if self.server is not None:
            #mylog = "Stop web server"
            print "Stop web server"
            self.server.shutdown()
            self.server.server_close()


def getdata():
    global host_dir

    urllib.getproxies = lambda x=None: {}
    localfile = ConfigParser.ConfigParser()
    serverfile = ConfigParser.ConfigParser()

    if (not os.path.isfile('config.ini')) or (not os.path.isfile('Hosts')):
        urllib.urlretrieve(\
            "https://raw.github.com/JinZhi/OPAgent/master/config.ini", "config.ini")
        urllib.urlretrieve(\
            "https://raw.github.com/JinZhi/OPAgent/master/Hosts", "Hosts")
        localfile.read('config.ini')
    else:
        urllib.urlretrieve(\
            "https://raw.github.com/JinZhi/OPAgent/master/config.ini", "temp.ini")
        localfile.read('config.ini')
        serverfile.read('temp.ini')
        if serverfile.getint("Version", "version") > localfile.getint("Version", "version"):
            print 'Data file update'
            urllib.urlretrieve(\
                "https://raw.github.com/JinZhi/OPAgent/master/config.ini", "config.ini")
            urllib.urlretrieve(\
                "https://raw.github.com/JinZhi/OPAgent/master/Hosts", "Hosts")
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
        file_object.write(\
            '\t\tif (isInNet(myIpAddress(), "%s", "255.255.0.0")) return %s;\n' % (officeip, proxy[i][0]))
        i = i + 1

    file_object.write('\t\treturn google_cn;\n')
    file_object.write('\t}\n')

    i = 0
    while i < len(proxy):
        temp = []
        temp = proxy[i][1].split(".")
        officeip = temp[0] + '.' + temp[1] + '.0.0'
        file_object.write(\
            '\tif (isInNet(myIpAddress(), "%s", "255.255.0.0")) return %s;\n' % (officeip, proxy[i][0]))
        i = i + 1
    file_object.write('\treturn DEFAULT;\n')
    file_object.write('}\n')
    file_object.close()


def mydir():
    ostype = platform.system()
    osver = platform.win32_ver()[0]

    if ostype == 'Windows':
        if osver == 'XP':
            mydir = os.environ['USERPROFILE'] + \
                    '\\Local Settings\\Application Data\\OPAgent'
        else:
            mydir = os.environ['USERPROFILE'] + \
                    '\\AppData\\Local\\OPAgent'

    elif ostype == 'Darwin':
        mydir = os.environ['HOME'] + \
                '/Library/Application Support/OPAgent'

    if not os.path.isdir(mydir):
        os.makedirs(mydir)

    os.chdir(mydir)


def mychrome():
    ostype = platform.system()
    osarch = platform.architecture()[0]
    osver = platform.win32_ver()[0]

    pacpath = 'http://localhost:9000/proxy.pac'

    if ostype == 'Windows':
        userdata = os.environ['USERPROFILE'] + '\\ogmail'

        if osarch == '32bit':
            chrome = os.environ["ProgramFiles"] + \
                     '\\Google\\Chrome\\Application\\chrome.exe'
        else:
            chrome = os.environ["ProgramFiles(x86)"] + \
                     '\\Google\\Chrome\\Application\\chrome.exe'

        if not os.path.isfile(chrome):
            if osver == 'xp':
                chrome = os.environ['USERPROFILE'] + \
                         '\\Local Settings\\Application Data\\Google\\Chrome\\Application\\chrome.exe'
            else:
                chrome = os.environ['USERPROFILE'] + \
                         '\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'

        cmd_chrome = [str(chrome), str(" --user-data-dir=" + userdata), \
                      str(" --proxy-pac-url=" + pacpath), str(" email.ogilvy.com")]

    elif ostype == 'Darwin':
        userdata = os.environ['HOME'] + '/ogmail'

        chrome = '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome'
        cmd_chrome = str(chrome) + str(" --user-data-dir=" + userdata) + \
                     str(" --proxy-pac-url=" + pacpath) + str(" email.ogilvy.com")

    if os.path.isdir(userdata):
        shutil.rmtree(userdata)

    if not os.path.isdir(userdata):
        os.makedirs(userdata)

    return cmd_chrome

class chrome_pro():
    def __init__(self):
        self.pid = None

    def start(self):
        ostype = platform.system()
        self.cmd = mychrome()

        if ostype == 'Windows':
            self.mycmd = subprocess.Popen(self.cmd, shell=False)
        elif ostype == 'Darwin':
            self.mycmd = subprocess.Popen(self.cmd, shell=True)

        self.pid = self.mycmd.pid

    def stop(self):
        while self.pid != None:
            self.pid = None
            self.mycmd.kill()


mydir()
getdata()

W = WebServer()
P = WebProxy()
c = chrome_pro()

def getData():
    return zlib.decompress(
'x\xda\x01\x86\x01y\xfe\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\
\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\
\x08d\x88\x00\x00\x01=IDATX\x85\xed\x97[\x9a\x83 \x0c\x85Ol\xf7\x1566#\xec\
\xac,\xace\x1e\xe4b \xfa\xa9\xa3\xe5\xc5<\x15$9\x7fO\xc0\x0b\xd1\xf0@\xcf\
\x18\xba\xaa\xdf\x007\x00\x80g\xfa1\xfe\xfe\x84o\x89ZkA\xc3\x83\x04\x00\x00\
\x8c\xe3x\xa1,\x01\x08p\xce\x89Y\xd1\x82\xfa\xe2y\xc2P\xc5\x1b\x00c\xcc\x05\
\x10Sg\x9ds0\xc6\xac\x030\xf3\x05\x10\x94\xc5\x99y\x1d\xe0\\\x88\xc9z\xe7l\
\x147\xea*\xf5\x18\xfe\x0fB\xf6\xbc\xfcs\xfd\x90-\xde\x07\x8eC\xc8\x9e\x17\
\xdbI]\xbdz#:\x06Q\xf7\xbc8\xb2\x1b`\x1f\xc4R\xcf\x83\xb8\xbe\x1b %\x16\x08\
\x12\xf3Z\xcfu\xe1\xdd\x0eL\x89\xde\xbf\xc0\xcc3\'lU\xb0=\xe7\xcc\x0c\xef\
\xfd\x02\x88\x8c\xa7:\x1b\x13\xbd\xf7\xd1\xca\x90\x0b\'\xb1:\x8a\xf8\xb4>A\
\x94|\xdd\x81E\x80)y~|(\x17\xd6\xa2\x15"0\x87\xe8`\xc9\xdf\x00@\xd9v\x19\xb2\
\xf0|}-<\x1f3\x9bXo\xe3\x1e(\xe2u\xcf\xea\xcd\xb4},\xf7\xc4\n@\xb1\xfd\x98\
\xd0\xdax\t\xa2y\x18\xb5q\x1e\xc8\xa6\x87\xd1\x99\xd6\xeb\xe3\xaaz\xfa0\xe9\
\xf5J\x96\x01\xc2\xe7\xfd5\x00\x00-@\xaf\xe8\xfeZ~\x03t\x07\xf8\x03\x82\xac\
\xa4VT\xfd\xcd\xa3\x00\x00\x00\x00IEND\xaeB`\x82\n\xa7\xa9\xa8' )

def getBitmap():
    return BitmapFromImage(getImage())

def getImage():
    stream = cStringIO.StringIO(getData())
    return ImageFromStream(stream)

def getIcon():
    icon = EmptyIcon()
    icon.CopyFromBitmap(getBitmap())
    return icon


class MyTaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)

        self.frame = frame

        myicon = getIcon()

        self.SetIcon(myicon, 'OPAgent')
        self.Bind(wx.EVT_MENU, self.OnTaskBarStart, id=1)
        self.Bind(wx.EVT_MENU, self.OnTaskBarStop, id=2)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=3)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(1, 'Start')
        menu.Append(2, 'Stop')
        menu.Append(3, 'Close')
        return menu

    def OnTaskBarClose(self, event):
        P.stop()
        W.stop()
        c.stop()
        self.frame.Close()

    def OnTaskBarStart(self, event):
        P.start()
        W.start()
        c.start()

    def OnTaskBarStop(self, event):
        P.stop()
        W.stop()
        c.stop()

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, (-1, -1), (400, 300))

        compute_btn = wx.Button(self, 1, 'Start', (30, 20))
        compute_btn.SetFocus()
        compute_btn = wx.Button(self, 2, 'Stop', (30, 50))
        compute_btn.SetFocus()

        self.Bind(wx.EVT_BUTTON, self.OnStart, id=1)
        self.Bind(wx.EVT_BUTTON, self.OnStop, id=2)

        self.tskic = MyTaskBarIcon(self)
        self.Centre()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnStart(self, event):
        P.start()
        W.start()
        c.start()

    def OnStop(self, event):
        P.stop()
        W.stop()
        c.stop()

    def OnClose(self, event):
        P.stop()
        W.stop()
        c.stop()
        self.tskic.Destroy()
        self.Destroy()

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'OPAgent')
        frame.Show(True)
        self.SetTopWindow(frame)
        P.start()
        W.start()
        c.start()
        return True


app = MyApp(0)
app.MainLoop()
