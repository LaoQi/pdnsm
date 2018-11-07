#!/bin/env python3

import tornado.ioloop
import tornado.web
import argparse
import logging
import json
import os

class Hosts:
    def __init__(self, path):
        self.path = path
        self.body = {}

    def parser(self, line):
        result = []
        temp = ""
        for c in line:
            if c in "#\r\n":
                if len(temp) > 0:
                    result.append(temp)
                    temp = ""
                break
            if c in "\t ":
                if len(temp) > 0:
                    result.append(temp)
                    temp = ""
            else:
                temp = temp + c
        if len(result) < 2: 
            return None
        return (result[0], " ".join(result[1:]))

    def load(self):
        if not os.path.exists(self.path):
            logging.warning("cannot read hosts file at {}".format(self.path))
            return
        with open(self.path, "r") as f:
            for line in f:
                result = self.parser(line)
                if result:
                    self.body[result[1]] = result[0]

    def put(self, domain, ip, old = None):
        if not domain or not ip:
            return False
        if old:
            self.body.pop(old)
        self.body[domain] = ip
        return True

    def delete(self, domain):
        if domain not in self.body:
            return False
        self.body.pop(domain)
        return True

    def write(self):
        with open(self.path, "w", newline = None) as f:
            for (k, v) in self.body.items():
                f.write("{} {}\n".format(v, k))
    
    def backup(self):
        if not os.path.exists(self.path):
            logging.warning("cannot read hosts file at {}".format(self.path))
            return
        backup = "{}.backup".format(self.path)
        if not os.path.exists(backup):
            os.rename(self.path, backup)

    def detail(self):
        return list(map(lambda x: dict(ip=x[1], domain=x[0]), self.body.items()))


class IndexHandler(tornado.web.StaticFileHandler):
    pass

class ApiHandler(tornado.web.RequestHandler):

    def initialize(self, hosts):
        self._hosts = hosts

    def get(self, action):
        self._dispatch_action(action)

    def post(self, action):
        self._dispatch_action(action)

    def put(self, action):
        self._dispatch_action(action)

    def delete(self, action):
        self._dispatch_action(action)
    
    def _dispatch_action(self, action):
        method = {
            "get-hosts": self.get_hosts,
            "put-hosts": self.put_hosts,
            "del-hosts": self.del_hosts,
        }.get(action)
        if not method:
            raise tornado.web.HTTPError(404)
        method()

    def put_hosts(self):
        ip = self.get_body_argument('ip', None)
        domain = self.get_body_argument('domain', None)
        old = self.get_body_argument('old', None)

        result = self._hosts.put(domain=domain, ip=ip, old=old)
        if result:
            self._hosts.backup()
            self._hosts.write()
            self.write('ok')
        else:
            self.write('error')

    def del_hosts(self):
        domain = self.get_body_argument('domain', None)
        result = self._hosts.delete(domain)
        if result:
            self._hosts.backup()
            self._hosts.write()
            self.write('ok')
        else:
            self.write('error')

    def get_hosts(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(self._hosts.detail()))

if __name__ == "__main__":
    parser = argparse.ArgumentParser("pdnsm", description="DNS WebUI service")
    parser.add_argument("-p", "--port", type=int, default=8000, help="set port")
    parser.add_argument("-f", "--hosts", type=str, default="/etc/hosts", help="Hosts file path")
    parser.add_argument("-v", "--verbosity", action="store_true", help="increase output verbosity")
    parser.add_argument("-d", "--debug", action="store_true", help="increase output verbosity")
    args = parser.parse_args()

    debug = False
    if args.verbosity:
        logging.basicConfig(level=logging.INFO)
    if args.debug:
        debug = True
        logging.basicConfig(level=logging.DEBUG)

    hosts = Hosts(os.path.abspath(args.hosts))
    hosts.load()
    settings = {
        "static_path": os.path.abspath(os.path.join(os.path.dirname(__file__), 'public')),
        # "debug": debug,
	}
    logging.info(settings)
    app = tornado.web.Application([
        (r"/api/(.*)", ApiHandler, dict(hosts=hosts)),
        (r"/(.*)", IndexHandler, 
            dict(
                path=os.path.abspath(os.path.join(os.path.dirname(__file__), 'public')), 
                default_filename="index.html",
            )),
    ], **settings)
    app.listen(args.port)
    tornado.ioloop.IOLoop.current().start()