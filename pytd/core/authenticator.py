
from functools import partial
from getpass import getpass

from pytd.util.sysutils import qtGuiApp, toStr
from pytd.gui.dialogs import loginDialog


class Authenticator(object):

    def __init__(self):
        self.authenticated = False
        self.userLogin = ""

    def loggedUser(self):
        return {}

    def logIn(self, *args, **kwargs):
        return {}

    def logOut(self):
        return True

    def authenticate(self, user=None, password=None, relog=False):

        if user and password:
            logInFunc = partial(self.logIn, writeCookie=False)
            userData = {}
        else:
            logInFunc = self.logIn
            userData = self.loggedUser()

        if (not relog) and userData and user and userData["login"] != user:
            relog = True

        if relog:
            self.logOut()
            userData = {}

        if not userData:
            if user and password:
                userData = logInFunc(user, password)
            elif qtGuiApp():
                userData = loginDialog(loginFunc=logInFunc)
            else:
                for _ in xrange(5):
                    sUser = raw_input("login:")
                    sPwd = getpass()
                    try:
                        userData = logInFunc(sUser, sPwd)
                    except Exception, e:
                        print toStr(e)
                    else:
                        if userData:
                            break
        if userData:
            self.authenticated = True
            print (u"<{}> User '{}' authenticated successfully !"
                   .format(self.__class__.__name__, userData["login"]))

        return userData
