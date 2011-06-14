import string, cgi, time, traceback
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urlparse
import re

history = [] # [[date,pid,level,pos,msg,fname],...]
            

def cacheLogs():
    #get list of file
    global history
    history=[]
    
    for cur,dirs,files in os.walk(os.path.join("..","Logs")):
        for fname in files:
            for line in  file(os.path.join(cur,fname)):
                date,pid,level,pos,msg = line.split("|",4)
                history.append([date,pid,level,pos,msg,fname])
            #2011-06-10 16:11:44,043|136320734516992|10|Core:<module>:172|End of core\n
    
    #construct the ordered version 
    history.sort()
cacheLogs()

def processLogs(**options):
    # <div class="log %i">
    #     <span class="date">2011-06-10 10:15:58,477</span>
    #     <span class="pid">107322765797120</span>
    #     <span class="level">10</span>
    #     <span class="line">Foo.py:myFunc:123</span>
    #     <span class="msg">
    #           <span>This is the message</span>
    #           <span>This is another line in the message</span>
    #     </span>
    # </span>
    ops = {
        "maxid":-1,
        "minid":0,
        "before":"x",
        "after":"",
        "pid":"",
        "minlevel":0,
        "maxlevel":50,
        "msg":".*",
        "file":".*"}
    expect = map(lambda (x,y):(x,type(y)),ops.items())
    ops.update(options)#overwrite defaults with whatevers provided
    try:
        print expect
        for k,t in expect:
            ops[k]=t(ops[k])       
        print "\n\t".join(map(str,ops.items()))
    except:
        print "Failed sanity check."
        return "[]"


    out = []
    global history
    for no,line in enumerate(history[ops["minid"]:ops["maxid"]]):
        no = no + ops["minid"]
        try:
            e = {"id":no}
            for n,val in enumerate(line):
                key = ["date","pid","level","line","msg","file"][n]
                if   n==5:
                    if re.search(ops["file"],val):
                        e[key]=val
                    else:
                        e=None
                elif n==4:
                    if re.search(ops["msg"],val):
                        e[key]=map(cgi.escape,val.split("\t"))
                    else:
                        e = None
                elif n==3:
                    if re.search(ops["file"],val):
                        e[key]=map(cgi.escape,val.split(":"))
                    else:
                        e = None
                elif n==2:
                    if ops["minlevel"]<int(val)<ops["maxlevel"]:
                        e[key]=int(val)
                    else:
                        e = None
                elif n==1:
                    if not ops["pid"] or ops["pid"]==val:
                        e[key]=cgi.escape(val)
                    else:
                        e = None
                else:
                    print ops["after"],"--<--",val,"--<--",ops["before"]
                    if ops["after"]<val<ops["before"]:
                        e[key]=cgi.escape(val)
                    else:
                        e = None

                if e == None:
                    break
            if e:
                out.append(e)
        except:
            print "Error parsing line:"
            print no,line
            pass
    #in the future this version should cache the output, and timestamps, only recomputing as necessary
    return json.dumps(out)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print "get:",self.path
        try:
            if "/?"== self.path[:2]:
                args = dict(urlparse.parse_qsl(self.path.split("?")[1]))
                output = processLogs(**args)
                if args.has_key("callback"):
                    output = args["callback"]+"("+output+")"
            else:
                if not self.path[1:]:
                    self.path+="index.html"
                print "file:",self.path[1:]
                output = file(self.path[1:]).read()

            self.send_response(200)
            self.send_header("Content-type","text/html")
            self.end_headers()
            self.wfile.write(output)
            self.wfile.close()
        except:
            class c:
                output = ""
                def write(s,l):
                    s.output+=l

            x = c()
            traceback.print_exc(file=x)
            self.send_error(404,x.output) 
    def do_POST(self):
        return

def main(port):
    server = None
    try:
        while not server:
            try:
                server = HTTPServer(('',port),Handler)
            except:
                print "Could not start server on port %i, trying port %i"%(port,port+1)
                port = port + 1
                server = None
        print "Serving on port",port
        server.serve_forever()
    except:
        server.socket.close()
    print "Finished."

if __name__=="__main__":
    main(10240)
