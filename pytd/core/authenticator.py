
from getpass import getpass

from pytd.util.sysutils import isQtApp, toStr
from pytd.gui.dialogs import loginDialog


class Authenticator(object):

    def __init__(self):
        self.authenticated = False

    def loggedUser(self):
        return {}

    def logIn(self, *args, **kwargs):
        return {}

    def logOut(self):
        return True

    def authenticate(self, **kwargs):

        if kwargs.get('relog', False):
            self.logOut()

        userData = self.loggedUser()
        if not userData:

            if isQtApp():
                userData = loginDialog(loginFunc=self.logIn)
            else:
                for _ in xrange(5):
                    sUser = raw_input("login:")
                    sPwd = getpass()
                    try:
                        userData = self.logIn(sUser, sPwd)
                    except Exception, e:
                        print toStr(e)
                    else:
                        if userData:
                            break

        if userData:
            self.authenticated = True

        return userData
