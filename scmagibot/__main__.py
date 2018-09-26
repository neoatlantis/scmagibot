#!/usr/bin/env python3

import os
import sys
import argparse
import logging

import yaml

from .bot import SCMAGI


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                     level=logging.INFO)

parser = argparse.ArgumentParser(prog="python3 -m scmagibot")
parser.add_argument(
    "config", metavar="CONFIG_FILE", help="Config file as YAML.")

args = parser.parse_args()

config = yaml.load(open(args.config, "r").read())
config["workdir"] = os.path.realpath(os.path.join(
    os.path.dirname(args.config),
    config["workdir"]
))

magi = SCMAGI(config)

##############################################################################

from .paged_messages import PagedMessages

pagedMessages = PagedMessages(magi)


@magi.command("start")
def start(bot, update):
    pagedMessages.sendMessage(chatID=update.message.chat_id)



from telegram.ext.filters import Filters

@magi.messageFilter(Filters.all)
def message(bot, update):
    #print(update)
    pass
