import http.server
import socketserver
import sys
import urllib.parse
import threading
import time
import json

PORT = int(sys.argv[1])

userTimestamp = {}
userExecutionOperation = {}
TIMEOUT = 13  # 13秒超时

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == '/q':
            params = urllib.parse.parse_qs(parsed_path.query)
            u = params.get('u', [None])[0]
            o = params.get('o', [None])[0]
            t = params.get('t', [None])[0]
            e = params.get('e', [None])[0]

            key = f"{u};{o};{t}"
            swapped_key = f"{o};{u};{t}"
            userTimestamp[key] = time.time()
            userExecutionOperation[key] = e
            if swapped_key in userExecutionOperation:
                # 返回对方的操作
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {
                    'opponentExecutionCsv': userExecutionOperation[swapped_key]
                }
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(202)
                self.end_headers()
        else:
            super().do_GET()

def cleanup_thread():
    while True:
        current_time = time.time()
        keys_to_delete = []
        for key, timestamp in userTimestamp.items():
            if current_time - timestamp > TIMEOUT:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del userExecutionOperation[key]
            del userTimestamp[key]
        time.sleep(5)

cleanup = threading.Thread(target=cleanup_thread)
cleanup.start()

Handler = CustomHandler

with ThreadedHTTPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

