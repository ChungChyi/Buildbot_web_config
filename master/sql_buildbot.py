# coding:utf-8

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DATE, ForeignKey, Table  # 导入外键
from sqlalchemy.orm import relationship  # 创建关系

engine = create_engine("mysql+pymysql://root:jkljkl147@localhost:3306/sql_buildbot_config",
                       encoding="utf-8")

Base = declarative_base()  # 生成orm基类

scheduler_builder = Table(
    "scheduler_builder",
    Base.metadata,
    Column("scheduler_id", Integer, ForeignKey("schedulers.id"), nullable=False, primary_key=True),
    Column("builder_id", Integer, ForeignKey("builders.id"), nullable=False, primary_key=True)
)

worker_builder = Table(
    "worker_builder",
    Base.metadata,
    Column("worker_id", Integer, ForeignKey("workers.id"), nullable=False, primary_key=True),
    Column("builder_id", Integer, ForeignKey("builders.id"), nullable=False, primary_key=True)
)

class Workers(Base):
    __tablename__ = "workers"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    worker_name = Column(String(32), unique=True)
    password = Column(String(32))
    builders = relationship("Builders", secondary=worker_builder, backref="workers")

    def __init__(self, worker_name, password):
        self.worker_name = worker_name
        self.password = password
    def __repr__(self):
        return "<Workers(name='%s', pw='%s')>" % (self.workername, self.password)


class ChangeSource(Base):
    __tablename__ = "change_source"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    repourl = Column(String(128))
    branches = Column(String(32))
    poll_interval = Column(Integer())

    def __init__(self, repourl, branches,poll_interval=60*60*24):
        self.repourl = repourl
        self.branches = branches
        self.poll_interval=poll_interval
    def __repr__(self):
        return "<ChangeSource(repourl='%s', branches='%s', pollInterval='%s')>" % (
            self.repourl, self.branches,self.poll_interval)

class Schedulers(Base):
    __tablename__ = "schedulers"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    scheduler_name = Column(String(32), unique=True)
    scheduler_type = Column(String(32))

    single = relationship("SingleBranch", cascade='all', backref='parent')
    periodic = relationship("Periodic", cascade='all', backref='parent')
    force = relationship("Force", cascade='all', backref='parent')
    builders = relationship("Builders", secondary=scheduler_builder, backref="schedulers")


    def __init__(self, scheduler_name, scheduler_type):
        self.scheduler_name = scheduler_name
        self.scheduler_type = scheduler_type


class Builders(Base):
    __tablename__ = "builders"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    builder_name = Column(String(32), unique=True)
    priority = relationship("PrioritizeBuilders", cascade='all', backref='parent')
    factory = relationship("Factory", cascade='all', backref='parent')

    def __init__(self, builder_name):
        self.builder_name = builder_name

class SingleBranch(Base):
    __tablename__ = "single_branch_schedulers"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    scheduler_name = Column(String(32), ForeignKey("schedulers.scheduler_name"))
    branch = Column(String(32))
    tree_stable_timer = Column(Integer())

    def __init__(self, scheduler_name, branch, tree_stable_timer):
        self.scheduler_name = scheduler_name
        self.branch = branch
        self.tree_stable_timer = tree_stable_timer

class Periodic(Base):
    __tablename__ = "periodic_schedulers"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    scheduler_name = Column(String(32), ForeignKey("schedulers.scheduler_name"))
    periodic_build_timer = Column(Integer())


    def __init__(self, scheduler_name, periodic_build_timer):
        self.scheduler_name = scheduler_name
        self.periodic_build_timer = periodic_build_timer

class Force(Base):
    __tablename__ = "force_schedulers"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    scheduler_name = Column(String(32), ForeignKey("schedulers.scheduler_name"))


    def __init__(self, scheduler_name):
        self.scheduler_name = scheduler_name


class Factory(Base):
    __tablename__ = "factory"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    builder_name = Column(String(32), ForeignKey("builders.builder_name"))
    repourl = Column(String(128))
    commands = relationship("Command", cascade='all', backref='factory')

    def __init__(self, builder_name, repourl):
        self.builder_name = builder_name
        self.repourl = repourl

class Command(Base):
    __tablename__ = "shell_command"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    factory_id = Column(Integer(), ForeignKey("factory.id"))
    command = Column(String(64))

    def __init__(self, factory_id, command):
        self.factory_id = factory_id
        self.command = command


class PrioritizeBuilders(Base):
    __tablename__ = "prioritize_builders"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    builder_name = Column(String(32), ForeignKey("builders.builder_name"))
    priority_num = Column(Integer())

    def __init__(self, builder_name, priority_num = 100):
        self.builder_name = builder_name
        self.priority_num = priority_num

class GlobalConfig(Base):
    __tablename__ = "global_config"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(32))
    value = Column(String(64))

    def __init__(self, name, value):
        self.name = name
        self.value = value

Base.metadata.create_all(engine)  # 创建表