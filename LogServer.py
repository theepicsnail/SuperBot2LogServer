import string, cgi, time, traceback
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urlparse
import re
index ="""
<!DOCTYPE HTML> 
<html> 
  <head> 
    <title>Tawlk</title> 
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js" type="text/javascript"></script> 
    <script type="text/javascript"> 
        $.getJSON("http://udderweb.com:10240/?callback=?",
  function(data) {
    $.each(data, function(i,item){
      console.log(item.msg)
      $('<li>' + item.msg + '</li>').appendTo("#log");
    });
  }); 
    </script> 
  </head> 
  <body> 
    <ul id="log"></ul> 
  </body> 
</html> """


def processEntry(data,**options):
    return True
def processLogs(**options):
    #get list of file
    entries = []
    for cur,dirs,files in os.walk("Logs"):
        for fname in files:
            r = options.get("FileName",".*")
            if re.search(r,fname):
                entries.extend(filter(lambda x: processEntry(x,**options),file(os.path.join(cur,fname)).readlines()))
            #2011-06-10 16:11:44,043|136320734516992|10|Core:<module>:172|End of core\n
    
    #construct the ordered version 
    entries.sort()

    # <div class="log %i">
    #     <span class="date">2011-06-10 10:15:58,477</span>
    #     <span class="pid">107322765797120</span>
    #     <span class="level">10</span>
    #     <span class="line">Foo.py:myFunc:123</span>
    #     <span class="msg">This is the message</span>
    # </span>
    out = []
    
    for no,line in enumerate(entries):
        e = {}
        for n,val in enumerate(line.strip().split("|",4)):
            key = ["date","pid","level","line","msg"][n]
            e[key]=val
        out.append(e)
    #in the future this version should cache the output, and timestamps, only recomputing as necessary
    return json.dumps(out)



class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print "get:",self.path
        try:
            if self.path=="/favicon.ico":
                raise Exception()
            if self.path=="/":
                global index
                output = index
            elif "?" in self.path:
                args = dict(urlparse.parse_qsl(self.path.split("?")[1]))
                print "A",args
                output = processLogs(**args)
                if args.has_key("callback"):
                    output = args["callback"]+"("+output+")"
                

            self.send_response(200)
            self.send_header("Content-type","text/html")
            self.end_headers()
            self.wfile.write(output)
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
