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
                Button("Edit", switch_inline_query_current_chat=\
                    self.commands.generate.edit(messageID)),
                Button("Delete", switch_inline_query_current_chat=\
                    self.commands.generate.delete(messageID)),
                Button(">>", callback_data=\
                    self.commands.generate.next(messageID))
            ]
        ])

    def sendMessage(self, chatID, internalMessageID=None):
        if not internalMessageID:
            internalMessageID = self.magi.database.navigateKey()
        record = self.db[internalMessageID] # TODO if message does not exist

        self.magi.core.send_message(
            chat_id=chatID,
            text=record["message"],
            reply_markup=self.__getKeyboard(internalMessageID)
        )

    def navigateUpdate(self, update, currentInternalMessageID, direction=1):
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
        self.magi.core.editMessageText(
            chat_id=chatID,
            message_id=messageID,
            text=self.db[internalMessageID]["message"],
            reply_markup=self.__getKeyboard(internalMessageID),
        )
        """
        self.magi.core.editMessageText(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            text=str(time.time()),
            reply_markup=self.__getKeyboard(update.effective_message.message_id),
        )
        print("button clicked", query)
        """
