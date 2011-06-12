import string, cgi, time, traceback
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urlparse
import re

def processLogs(**options):
    #get list of file
    entries = []
    for cur,dirs,files in os.walk(os.path.join("..","Logs")):
        for fname in files:
            r = options.get("FileName",".*")
            if re.search(r,fname):
                for line in  file(os.path.join(cur,fname)):
                    print line.split("|",4)
                    date,pid,level,pos,msg = line.split("|",4)
                    # process stuff against **options
                    entries.append([date,pid,level,pos,msg,fname])
            #2011-06-10 16:11:44,043|136320734516992|10|Core:<module>:172|End of core\n
    
    #construct the ordered version 
    entries.sort()

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
    out = []
    
    for no,line in enumerate(entries):
        e = {}
        for n,val in enumerate(line):
            key = ["date","pid","level","line","msg","file"][n]
            if n != 4:
                e[key]=cgi.escape(val)
            else:
                e[key]=map(cgi.escape,val.split("\t"))
        out.append(e)
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
