#!/usr/bin/env python3

import os
import time
import shelve
from logging import info

from telegram.ext import *

from .acl import SCMAGIAccessControl



class SCMAGIDatabase:

    def __init__(self, config):
        basepath = lambda *i: os.path.join(config["workdir"], *i)
        opendb = lambda f: shelve.open(basepath(f), flag="c", writeback=True)
        self.messages = opendb("messages.db")
        self.acl = opendb("acl.db")
        self.__initMessages()
        self.updateKeys()

    def __initMessages(self):
        if len(self.messages) == 0:
            info("Empty message database found. Fill with welcome messages.")
            self.addMessage("""Welcome to use SCMAGI bot. This is the
            first message. To view other messages, use the buttons below.""")
            self.addMessage("""You may now start a private chat with me,
            where I'll present you with more options.""")

    def editMessage(self, msgid, message=None, tags=None):
        if not msgid in self.messages:
            info("/edit: Editing a non-exist message. Failed.")
            return False
        record = self.messages[msgid]
        if message:
            record["message"] = message
        if tags:
            record["tags"] = tags
        self.messages[msgid] = record
        info("Edited message id: %s" % msgid)
        return True

    def deleteMessage(self, msgid):
        if not msgid in self.messages: return False
        del self.messages[msgid]
        self.updateKeys()
        return True

    def addMessage(self, message, tags=[]):
        msgid = os.urandom(16).hex()
        self.messages[msgid] = {
            "message": message,
            "tags": tags,
            "timestamp": time.time(),
        }
        self.updateKeys()
        return msgid

    def updateKeys(self):
        self.keys = []
        keys = [(k, self.messages[k]["timestamp"]) for k in self.messages]
        keys.sort(key=lambda e: e[1])
        self.keys = [e[0] for e in keys]

    def navigateKey(self, start=None, direction=1):
        if not self.keys: return "" 
        if not start: return self.keys[0]
        upperBound = len(self.keys) - 1
        if start in self.keys:
            index = self.keys.index(start)
            index += direction
            if index < 0: index = upperBound
            if index > upperBound: index = 0
            return self.keys[index]
        else:
            if direction > 0: return self.keys[upperBound]
            return self.keys[0]


class SCMAGI:

    def __init__(self, config):
        self.config = config
        self.updater = Updater(token=config["token"])
        self.dispatcher = self.updater.dispatcher

        self.core = self.updater.bot
        self.__initCore()

        self.database = SCMAGIDatabase(config)
        self.acl = SCMAGIAccessControl(self)
        
        info("Initialized. Start polling loop.")
        self.updater.start_polling()

    def __initCore(self):
        me = self.core.getMe()
        if not me["is_bot"]:
            raise Exception("I'm not a bot. Try with another account.")
        self.username = me["username"]
        self.id = me["id"]
        info("SCMAGI connected with Telegram as bot @%s (id: %s)." %
            (self.username, self.id))
        

    def __wrapCallback(self, func):
        def callback(bot, update, **args):
            if not self.acl.checkAccess(update):
                # TODO send denial message when in private chat
                if update.callback_query:
                    bot.answerCallbackQuery(
                        update.callback_query.id,
                        "Not authorized to perform this action."
                    )
                return
            func(bot, update, **args)
        return callback

    def command(self, command, **argv):
        def decorator(func):
            callback = self.__wrapCallback(func)
            self.dispatcher.add_handler(
                CommandHandler(command, callback, **argv))
        return decorator

    def inlineQuery(self, func):
        callback = self.__wrapCallback(func)
        self.dispatcher.add_handler(InlineQueryHandler(callback))

    def callbackQuery(self, func):
        callback = self.__wrapCallback(func)
        self.dispatcher.add_handler(CallbackQueryHandler(callback))

    def messageFilter(self, filters, **argv):
        def decorator(func):
            callback = self.__wrapCallback(func)
            self.dispatcher.add_handler(
                MessageHandler(filters, callback, **argv))
        return decorator
