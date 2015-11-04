
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

    def authenticate(self, **kwargs):

        if kwargs.get('relog', False):
            self.logOut()

        userData = self.loggedUser()
        if not userData:

            if qtGuiApp():
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
            print (u"<{}> User '{}' authenticated successfully !"
                   .format(self.__class__.__name__, userData["login"]))

        return userData
