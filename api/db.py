from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, create_engine, event, String, Boolean, Table, Integer, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship


class AccountingBase(object):
    id = Column(UUID, default=str(uuid4()), primary_key=True)
    created_at = Column(DateTime(), default=datetime.now())
    updated_at = Column(DateTime(), onupdate=datetime.now())

    def __init__(self):
        self.id = str(uuid4())

    def dump(self):
        return dict([(k, v) for k, v in vars(self).items() if not k.startswith("_")])

    @staticmethod
    def insert(mapper, connection, target):
        target.created_at = datetime.now()

    @staticmethod
    def update(mapper, connection, target):
        target.updated_at = datetime.now()


event.listen(AccountingBase, "before_insert", AccountingBase.insert)
event.listen(AccountingBase, "before_update", AccountingBase.update)

Base = declarative_base(cls=AccountingBase)
db_session = None


def init_db(uri, persist=True):
    global db_session
    engine = create_engine(uri, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    Base.query = db_session.query_property()
    if not persist:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(bind=engine)
    return db_session


class Account(Base):
    __tablename__ = "accounts"
    name = Column(String(100), unique=True)
    active = Column(Boolean)
    principle_investigator = Column(String(255))
    faculty = Column(String(100))
    department = Column(String(100))

    users = association_proxy("account_users", "user")


class User(Base):
    __tablename__ = "users"
    ldap_name = Column(String(100), unique=True)

    accounts = association_proxy("account_users", "account")


class AccountUser(Base):
    __tablename__ = 'account_users'

    account_id = Column(Integer, ForeignKey('account.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    admin = Column(Boolean, nullable=False)

    account = relationship(Account, backref="account_users")
    user = relationship(User, backref="account_users")
