#!/usr/bin/env python3

import json
import csv
import os
from sys import stderr
from getpass import getpass
from datetime import datetime
from collections import defaultdict

import requests

from dict_wrapper import DictWrapper

config_file_addr = "config.json"
config = None


def extract_config(addr):
    with open(addr) as f:
        config = DictWrapper(json.load(f))
    for url in config.urls:
        if url != "root":
            config.urls.dictionary[url] = config.urls.root + config.urls.dictionary[url]
    if config.deadline:
        config.deadline = datetime.strptime(config.deadline, config.datetime_format)
    else:
        config.deadline = datetime.now()
    if not config.codes_folder_addr:
        config.codes_folder_addr = "."

    if not os.path.exists(config.codes_folder_addr):
        os.mkdir(config.codes_folder_addr)

    return config


def get_authentication_data():
    print("username:\t", end="", file=stderr)
    usrname = input()
    print("password:\t", end="", file=stderr)
    passwd = getpass()
    print("\r          ", file=stderr)
    return {"usrname": usrname, "passwd": passwd}


def get_submissions_raw_date(authentication_data):
    raw_db = {}

    cookiejar = requests.get(config.urls.root).cookies
    requests.post(
        config.urls.login,
        data={
            config.loggin_req_keys.usrname: authentication_data["usrname"],
            config.loggin_req_keys.passwd: authentication_data["passwd"]
        },
        cookies=cookiejar)
    for question in config.questions:
        res = requests.get(config.urls.export + question, cookies=cookiejar)
        print("loading %r results..." % question, file=stderr)
        raw_db[question] = json.loads(res.text)
    requests.get(config.urls.logout, cookies=cookiejar)

    for (question, submissions) in raw_db.items():
        for submission in submissions:
            submission[config.report_json_keys.datetime] = datetime.strptime(
                submission[config.report_json_keys.datetime],
                config.datetime_format)

    return raw_db


def extract_acceptable_submissions(raw_db):
    db = defaultdict(set)

    for (question, submissions) in raw_db.items():
        codes_folder_addr = config.codes_folder_addr + "/" + question + "/"
        if not os.path.exists(codes_folder_addr):
            os.makedirs(codes_folder_addr)
        for submission in submissions:
            if (
                    submission[config.report_json_keys.result] == config.report_json_accepted_flag
                    and submission[config.report_json_keys.datetime] <= config.deadline):
                with open(
                        codes_folder_addr
                        + submission[config.report_json_keys.usrname]
                        + "."
                        + config.file_extension.dictionary[submission[config.report_json_keys.lang]],
                        "w") as f:
                    print(submission[config.report_json_keys.code], file=f)
                db[question].add(submission[config.report_json_keys.usrname])

    return db


def make_output(db):
    with open(config.list_file_addr) as fin:
        with open(config.output_file_addr, "w") as fout:
            reader = csv.DictReader(fin)
            writer = csv.DictWriter(
                fout,
                reader.fieldnames + config.questions + [config.output_overall_score_key])
            writer.writeheader()
            for row in reader:
                row[config.output_overall_score_key] = 0
                for question in config.questions:
                    row[question] = [0, 1][row[config.list_usrname_key] in db[question]]
                    row[config.output_overall_score_key] += row[question]
                row[config.output_overall_score_key] = (
                    row[config.output_overall_score_key]
                    / len(config.questions)
                    * 100)
                writer.writerow(row)


def main():
    global config
    config = extract_config(config_file_addr)
    authentication_data = get_authentication_data()

    raw_db = get_submissions_raw_date(authentication_data)
    db = extract_acceptable_submissions(raw_db)
    make_output(db)


if __name__ == '__main__':
    main()
