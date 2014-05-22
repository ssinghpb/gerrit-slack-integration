#!/usr/bin/env python
#
# Copyright (c) 2014, Aleksey Didik <aleksey.didik@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
    Gerrit Slack Integration Webhook
"""

__author__ = "Aleksey Didik"
__author_email__ = "aleksey.didik@gmail.com"

# Configuration section

# Gerrit parameters is necessary to retrive commit message and author
# Gerrit SSH port
GERRIT_PORT = 29418
# Gerrit host
GERRIT_SERVER = "localhost"


SLACK_WEBHOOK_URL = "https://company.slack.com/services/hooks/incoming-webhook?token=<token>"

# Mapping #channel to Gerrit projects.
# One channel can be mapped on several projects.
# Use regexp for 
# E.g. to map all projects to general and #web channel 
# to projects web-project and web-design set:
#     {"gerrit": [".*"], "web": ["web-project", "web-design"]}
CHANNEL_MAPPING = {"#general": [".*"]}

# emoji icon to be used in a message.
# set value "" to use Slack defined icon
ICON_EMOJI = ":white_check_mark:"

# End of coniguration section

import json
import time
import urllib
import urllib2
import subprocess
import re
from optparse import OptionParser


def getCommitInfo(commit_hash):
    try:
        result = json.loads(subprocess.check_output(
                ["ssh", "-p", str(GERRIT_PORT), GERRIT_SERVER, "gerrit",
                 "query", "--commit-message", "--format", "json",
                 commit_hash]).split("\n")[0])
        return (result["commitMessage"], result["owner"]["name"])
    except Exception, e:
        return ("Failed getting commit message, %s: %s" % (
                    e.__class__.__name__, e),
                int(time.time()), "unknown user", "unknown@example.com")


def webhook(channel, project, branch, name, change_url, message, submitter):  

    data = {
        "channel" : channel,
        "pretext": "@{0} has merged change <{1}|{2}>".format(submitter, change_url, message.splitlines()[0]),
        "color": "#00D000",
        "fields": [
            {
                "title": "Author",
                "value": name,
                "short": "true"
            },
            {
                "title": "Project",
                "value": project,                
            },
            {
                "title": "Branch",
                "value": branch,                
            },
        ],
        "link_names": 1,        
        "fallback" : "@{0} has merged change {1}\n Branch: {2}\n Link: {3}".format(submitter, message, branch, change_url)
    }
    if ICON_EMOJI != "":
        data["icon_emoji"] = ICON_EMOJI

    urllib2.urlopen(SLACK_WEBHOOK_URL, urllib.urlencode({"payload": json.dumps(data)})).read()


def main():
    parser = OptionParser(usage="usage: %prog <required options>")
    parser.add_option("--change", help="Change identifier")
    parser.add_option("--change-url", help="Change url")
    parser.add_option("--project", help="Project path in Gerrit")
    parser.add_option("--branch", help="Branch name")
    parser.add_option("--topic", help="Topic name")
    parser.add_option("--submitter", help="Submitter")
    parser.add_option("--commit", help="Git commit hash")
    options, args = parser.parse_args()

    message,name = getCommitInfo(options.commit)    

    for channel in CHANNEL_MAPPING: 
        for project_re in CHANNEL_MAPPING[channel]:
            if  re.compile(project_re).match(options.project):
                    webhook(channel, options.project, options.branch, name, options.change_url, message, options.submitter)

if __name__ == "__main__":
    main()
