#!/usr/bin/env python3

import json
import csv
from sys import stderr
from getpass import getpass

import requests

from dict_wrapper import DictWrapper

config_file_addr = "config.json"


def main():
    with open(config_file_addr) as f:
        config = DictWrapper(json.load(f))
    for url in config.urls:
        if url != "root":
            config.urls.dictionary[url] = config.urls.root + config.urls.dictionary[url]

    print("username:\t", end="", file=stderr)
    usrname = input()
    print("password:\t", end="", file=stderr)
    passwd = getpass()
    print("\r          ", file=stderr)

    db = {}

    cookiejar = requests.get(config.urls.root).cookies
    requests.post(config.urls.login, data={config.loggin_req_key.usrname: usrname, config.loggin_req_key.passwd: passwd}, cookies=cookiejar)
    for question in config.questions:
        res = requests.get(config.urls.export + question, cookies=cookiejar)
        print("loading %r results..." % question, file=stderr)
        db[question] = json.loads(res.text)
    requests.get(config.urls.logout, cookies=cookiejar)


if __name__ == '__main__':
    main()
