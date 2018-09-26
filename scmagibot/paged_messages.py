#!/usr/bin/env python3

import time

from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Button
from telegram.ext.filters import Filters

from .paged_messages_commands import PagedMessagesCommands


class PagedMessages:

    def __init__(self, magi):
        self.magi = magi
        self.db = self.magi.database.messages
        self.commands = PagedMessagesCommands(self)
        self.__bindEvents()

    def __bindEvents(self):
        self.magi.callbackQuery(
            lambda bot, update: self.commands(bot, update, source="query"))
        self.magi.messageFilter(
            Filters.entity("mention")
        )(lambda bot, update: self.commands(bot, update, source="chat"))

    def __getKeyboard(self, messageID):
        return InlineKeyboardMarkup([
            [ # Row 1
                Button("<<", callback_data=\
                    self.commands.generate.prev(messageID)),
                Button("New", switch_inline_query_current_chat=\
                    self.commands.generate.new()),
#                Button("Quote", switch_inline_query_current_chat=\
#                    self.commands.generate.quote(messageID)),
                Button("Edit", switch_inline_query_current_chat=\
                    self.commands.generate.edit(messageID)),
                Button("Delete", switch_inline_query_current_chat=\
                    self.commands.generate.delete(messageID)),
                Button(">>", callback_data=\
                    self.commands.generate.next(messageID))
            ]
        ])

    def __formatDatabaseRecord(self, record):
        tags = record["tags"]
        tagsJoined = "\n".join(["#%s" % e for e in tags])
        ret = record["message"]
        if tags:
            ret += "\n----\n%s" % tagsJoined
        return ret

    def sendMessage(self, chatID, internalMessageID=None, **kvargs):
        if not internalMessageID:
            internalMessageID = self.magi.database.navigateKey()
        if not internalMessageID in self.db: return False
        record = self.db[internalMessageID]
        self.magi.core.send_message(
            chat_id=chatID,
            text=self.__formatDatabaseRecord(record),
            reply_markup=self.__getKeyboard(internalMessageID),
            **kvargs
        )
        return True

    def navigateUpdate(
        self,
        update,
        currentInternalMessageID=None, direction=1,
        newInternalMessageID=None
    ):
        if not newInternalMessageID:
            if not currentInternalMessageID:
                newInternalMessageID = self.magi.database.navigateKey()
            else:
                newInternalMessageID = self.magi.database.navigateKey(
                    currentInternalMessageID,
                    direction
                )
        # TODO if not newKey

        self.updateMessage(
            chatID=update.effective_chat.id, 
            messageID=update.effective_message.message_id,
            internalMessageID=newInternalMessageID
        )

    def updateMessage(self, chatID, messageID, internalMessageID):
        record = self.db[internalMessageID]
        self.magi.core.editMessageText(
            chat_id=chatID,
            message_id=messageID,
            text=self.__formatDatabaseRecord(record),
            reply_markup=self.__getKeyboard(internalMessageID),
        )
