#!/usr/bin/env python3

from logging import info

getValue = lambda f, k, d: f[k] if k in f else d

class SCMAGIAccessControl:

    def __init__(self, magi):
        self.magi = magi
        self.allowedUsers =  getValue(self.magi.database.acl, "users", [])
        self.allowedGroups = getValue(self.magi.database.acl, "groups", [])
        self.update()

    def update(self):
        aclRules = self.magi.config["acl"]
        allowedUsers =  getValue(aclRules, "users", []) 
        allowedGroups = getValue(aclRules, "admins-from-groups", [])
        for groupID in allowedGroups:
            admins = self.magi.core.getChatAdministrators(groupID)
            for admin in admins:
                allowedUsers.append(admin)
        self.allowedUsers = allowedUsers
        self.allowedGroups = allowedGroups

    def checkAccess(self, update):
        # First check user against our white list
        user = update.effective_user
        userAllowed = False
        for each in self.allowedUsers:
            if type(each) == str:
                if user.username == each:
                    userAllowed = True
                    break
            else:
                if user.id == each.user.id:
                    userAllowed = True
                    break
        if not userAllowed:
            info("Access denied for user @%s (id: %s)." %
                (user.username, user.id))
            return False
        # If chat is available, check that against our white list. But allow
        # access if chat cannot be found.
        chat = update.effective_chat
        if not chat: return True
        if chat.type == chat.PRIVATE: return True
        if chat.id in self.allowedGroups:
            return True
        else:
            info("Access denied for chat id: %s." % chat.id)
            return False
