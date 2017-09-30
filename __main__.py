#!/usr/bin/env python3

import json
import csv
import os
from sys import stderr
from getpass import getpass
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

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
    late_policies = OrderedDict()
    for (dt, score) in config.late_policies.items():
        ((days,), (hours, minutes, seconds)) = (i.split(":") for i in dt.split(" "))
        (days, hours, minutes, seconds) = (int(i) for i in (days, hours, minutes, seconds))
        late_policies[timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)] = score
    config.late_policies = late_policies
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
    db = defaultdict(dict)

    for (question, submissions) in raw_db.items():
        codes_folder_addr = config.codes_folder_addr + "/" + question + "/"
        if not os.path.exists(codes_folder_addr):
            os.makedirs(codes_folder_addr)
        for submission in submissions:
            score = calculate_score(submission)
            if score:
                with open(
                        codes_folder_addr
                        + submission[config.report_json_keys.uid]
                        + "."
                        + config.file_extension.dictionary[submission[config.report_json_keys.lang]],
                        "w") as f:
                    print(submission[config.report_json_keys.code], file=f)
                db[question][submission[config.report_json_keys.uid]] = score

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
                    row[question] = float(
                        row[config.list_uid_key] in db[question]
                        and db[question][row[config.list_uid_key]])
                    row[config.output_overall_score_key] += row[question]
                row[config.output_overall_score_key] = (
                    row[config.output_overall_score_key]
                    / len(config.questions))
                writer.writerow(row)


def calculate_score(submission):
    if submission[config.report_json_keys.result] != config.report_json_accepted_flag:
        return 0
    late = submission[config.report_json_keys.datetime] - config.deadline
    for policy in config.late_policies:
        if late <= policy:
            return config.late_policies[policy]
            break
    return 0


def main():
    global config
    config = extract_config(config_file_addr)
    authentication_data = get_authentication_data()

    raw_db = get_submissions_raw_date(authentication_data)
    db = extract_acceptable_submissions(raw_db)
    make_output(db)


if __name__ == '__main__':
    main()
