import logging

from connexion import NoContent
from flask import session
from sqlalchemy.dialects.oracle.zxjdbc import SQLException

from api.db import db_session, Account, User, AccountUser
from api.app import AccountRestService

logger = logging.getLogger('api')
ldap = AccountRestService.ldap


@ldap.login_required
def find_accounts(admin=False, limit=20):
    u = db_session.query(User)
    user = u.filter(User.ldap_name == session['username']).one_or_none()
    if not user:
        logger.warning("User {0} not found".format(session['username']))
        return "User doesn't exist", 404
    ua = db_session.query(AccountUser)
    accounts = ua.filter(AccountUser.user == user)
    if admin:
        return [a.accounts for a in accounts if a.admin][:limit], 200
    else:
        return [a.account.dump() for a in accounts][:limit], 200


@ldap.login_required
def add_account(account):
    if not session['admin']:
        return NoContent, 401
    a = Account(**account)
    try:
        db_session.add(a)
        db_session.commit()
        db_session.refresh(a)
        return a.dump(), 201
    except SQLException:
        logger.exception("error while creating account")
        return NoContent, 500


@ldap.login_required
def update_account(account):
    u = db_session.query(User)
    user = u.filter(User.ldap_name == session['username']).one_or_none()
    if not user:
        logger.warning("User {0} not found".format(session['username']))
        return "User doesn't exist", 404
    a = db_session.query(Account)
    dba = a.filter(Account.name == account.name).one_or_none()
    if not dba:
        logger.error("Account {0} does not exist".format(account.name))
        return "Lookup failed for {0}".format(account.name), 404
    if not session['admin']:
        ua = db_session.query(AccountUser)
        admin = ua.filter(AccountUser.user == user and AccountUser.account == dba and AccountUser.admin).one_or_none()
        if not admin:
            logger.error("user {0} not authorized for changes of {1}".format(user.ldap_name, dba.name))
            return "User {0} is not an admin".format(user.ldap_name), 403
    try:
        for k in account:
            setattr(dba, k, account[k])
        db_session.commit()
        db_session.refresh(dba)
        return dba.dump(), 201
    except SQLException:
        logger.exception("error while updating account")
        return NoContent, 500


@ldap.login_required
def get_profile():
    u = db_session.query(User)
    user = u.filter(User.ldap_name == session['username']).one_or_none()
    return (user.dump(), 200) if user else ("User doesn't exist", 404)
