from api.db import *
from api.app import AccountRestService


ldap = AccountRestService.ldap

@ldap.login_required
def findAccounts():
    pass

@ldap.login_required
def addAccount(account):
    pass

@ldap.login_required
def updateAccount():
    pass


@ldap.login_required
def getProfile():
    pass

@ldap.login_required
def getAdminAccounts():
    pass

@ldap.login_required
def getAccounts():
    pass

