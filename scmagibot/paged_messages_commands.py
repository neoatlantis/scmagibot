#!/usr/bin/env python3

from logging import info
from .usertext.paged_messages_commands import *


class _CommandsGenerator:

    def edit(self, msgid, tags=[]):
        tagsStr = "\n".join(["#" + each for each in tags])
        return TEXT_COMMAND_EDIT.format(id=msgid, tags=tagsStr)

    def delete(self, msgid):
        return "/delete id=%s XXXX //Replace XXXX on the left with word `confirmed` and send, to delete that message." % msgid

    def new(self):
        return "/new \n//Now select a message, and set current message as a reply to it."

    #def quote(self, msgid):
    #    return TEXT_COMMAND_QUOTE.format(id=msgid)

    def next(self, msgid):
        return "/next id=%s" % msgid

    def prev(self, msgid):
        return "/prev id=%s" % msgid


class PagedMessagesCommands:

    CHAT_COMMANDS = ["edit", "delete", "new", "quote"]
    QUERY_COMMANDS = ["prev", "next"]

    def __init__(self, parent):
        self.parent = parent
        self.magi = parent.magi
        self.generate = _CommandsGenerator()

    def __argsToDict(self, args):
        result = {}
        for each in args:
            b = each.split("=")
            result[b[0]] = "=".join(b[1:])
        return result

    def __call__(self, bot, update, source="query"):
        mentioned, command, hashtags = False, None, []

        if source == "chat":
            message = update.message
            # find out message entities: mentions, commands, and hashtags
            for entity in message.entities:
                entityText = message.text[entity.offset:][:entity.length]
                if entity.type == "mention" and not mentioned:
                    mentioned = (entityText == '@' + self.magi.username)
                if entity.type == "bot_command" and not command:
                    command = entityText[1:]
                if entity.type == "hashtag":
                    hashtags.append(entityText[1:])
            
            if not mentioned: return
            if command not in self.CHAT_COMMANDS: return
            
            payload = message.text.split("//")[0] # remove comments
            payload = payload.replace("\n", " ").split(" ") # remove comments
            payload = [e for e in payload if e and e[0] not in "/@#"]

        elif source == "query":
            message = update.callback_query.data
            slices = [each for each in message.split(" ") if each]
            for each in slices:
                if each.startswith("/"):
                    command = each[1:]
                    break
            if command not in self.QUERY_COMMANDS: return
            payload = [e for e in slices if e[0] not in "/@#"]

        else:
            raise Exception("Invalid source.")

        # Confirmed this is a user commanding us. Analyze what to do.
        payload = self.__argsToDict(payload)
        print(command, payload, hashtags)
        getattr(self, command)(
            bot=bot,
            update=update,
            args=payload,
            hashtags=hashtags
        )

    def new(self, bot, update, hashtags, args):
        newMessage = update.message.reply_to_message
        if not newMessage:
            info("/new command received without new message.")
            update.message.reply_text(
                "New memo failed: you have't choosen anything for creation."
            )
            return
        msgid = self.magi.database.addMessage(
            message=newMessage.text,
            tags=hashtags
        )
        update.message.reply_text("Success!")

    """def quote(self, bot, update, hashtags, args):
        targetMessage = update.message.reply_to_message
        withMessageID = args["id"]
        self.parent.sendMessage(
            chatID=update.message.chat_id,
            internalMessageID=withMessageID,
            reply_to_message_id=targetMessage.message_id
        )"""
    
    def edit(self, bot, update, hashtags, args):
        replaceMessage = update.message.reply_to_message
        internalMessageID = args["id"]
        if replaceMessage:
            r1 = self.magi.database.editMessage(
                internalMessageID, message=replaceMessage.text)
        else:
            r1 = True
        r2 = self.magi.database.editMessage(
            internalMessageID, tags=hashtags)
        if not r1 and not r2:
            update.message.reply_text("Edit message failed.")
            return
        update.message.reply_text("Message edited successfully.")

    def delete(self, bot, update, hashtags, args):
        if "confirmed" not in [i.lower().strip() for i in args.keys()]:
            update.message.reply_text("Deletion intent not confirmed.")
            return
        if self.magi.database.deleteMessage(args["id"]):
            update.message.reply_text("Delete success!")
        else:
            update.message.reply_text("Delete failed.")

    def prev(self, bot, update, hashtags, args):
        self.parent.navigateUpdate(update, args["id"], -1)
        self.magi.core.answerCallbackQuery(update.callback_query.id)

    def next(self, bot, update, hashtags, args):
        self.parent.navigateUpdate(update, args["id"], 1)
        self.magi.core.answerCallbackQuery(update.callback_query.id)
