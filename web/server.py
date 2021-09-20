#!/usr/bin/python


import http.server
import socketserver
import os
import sys
import inspect
import configparser

currentframe = inspect.currentframe()
assert currentframe
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(currentframe)))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import rando


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_cors_headers(self):
        # Required for stupid default behavior in browsers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,ConfLength,Seed")
        # Required for a separate stupid behavior
        self.send_header("Access-Control-Expose-Headers", "Seed")

    def do_GET(self):
        self.do_POST()

    def do_POST(self):
        self.send_response(200)
        self.send_cors_headers()
        data_len = int(self.headers["Content-Length"])
        conf_len = int(self.headers["ConfLength"])
        print(data_len)
        data = self.rfile.read(data_len)
        confStr = data[:conf_len].decode("utf-8")
        print(confStr)
        gameData = bytearray(data[conf_len:])
        print(len(gameData))
        conf = configparser.ConfigParser()
        conf.read_string(confStr)
        inputSeed = self.headers.get("Seed", None)
        seed = rando.randomize(gameData, conf, inputSeed)
        self.send_header("Seed", str(seed))
        self.end_headers()
        self.wfile.write(gameData)
        print(seed)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        print("options BS")


if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
