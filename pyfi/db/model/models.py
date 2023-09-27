# type: ignore

"""
Class database model definitions
"""

import json
from datetime import datetime
from typing import Any, Optional

from oso import Oso
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    and_,
    literal_column,
)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import DeclarativeMeta, declared_attr
from sqlalchemy.orm import declarative_base, foreign, relationship
from sqlalchemy.schema import CreateColumn

Base: Any = declarative_base(name="Base")

oso = Oso()


@compiles(CreateColumn, "postgresql")
def use_identity(element, compiler, **kw):
    text = compiler.visit_create_column(element, **kw)
    text = text.replace("SERIAL", "INT GENERATED BY DEFAULT AS IDENTITY")
    return text


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        from datetime import datetime

        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [
                x for x in dir(obj) if not x.startswith("_") and x != "metadata"
            ]:
                data = obj.__getattribute__(field)
                try:
                    # this will fail on non-encodable values, like other classes
                    if type(data) is datetime:
                        data = str(data)
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


class HasLogins(object):
    @declared_attr
    def logins(cls):
        return relationship(
            "LoginModel",
            order_by="desc(LoginModel.created)",
            primaryjoin=lambda: and_(foreign(LoginModel.user_id) == cls.id),
            lazy="select",
        )


class HasLogs(object):
    @declared_attr
    def logs(cls):
        return relationship(
            "LogModel",
            order_by="desc(LogModel.created)",
            primaryjoin=lambda: and_(
                foreign(LogModel.oid) == cls.id,
                LogModel.discriminator == cls.__name__,
            ),
            lazy="select",
        )


class BaseModel(Base):
    """
    Docstring
    """

    __abstract__ = True

    id = Column(
        String(40),
        autoincrement=False,
        default=literal_column("uuid_generate_v4()"),
        unique=True,
        primary_key=True,
    )
    name = Column(String(80), unique=True, nullable=False, primary_key=True)
    owner = Column(String(40), default=literal_column("current_user"))

    status = Column(String(20), nullable=False, default="ready")
    requested_status = Column(String(40), default="ready")

    enabled = Column(Boolean)
    created = Column(DateTime, default=datetime.now, nullable=False)
    lastupdated = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    def __repr__(self):
        return json.dumps(self, cls=AlchemyEncoder)


class LogModel(Base):
    """
    Docstring
    """

    __tablename__ = "log"

    id = Column(
        String(40),
        autoincrement=False,
        default=literal_column("uuid_generate_v4()"),
        unique=True,
        primary_key=True,
    )

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True)

    public = Column(Boolean, default=False)
    created = Column(DateTime, default=datetime.now, nullable=False)
    oid = Column(String(40), primary_key=True)
    discriminator = Column(String(40))
    text = Column(String(80), nullable=False)
    source = Column(String(40), nullable=False)

    def __repr__(self):
        return json.dumps(self, cls=AlchemyEncoder)


rights = [
    "ALL",
    "CREATE",
    "READ",
    "UPDATE",
    "DELETE",
    "DB_DROP",
    "DB_INIT",
    "START_AGENT",
    "RUN_TASK",
    "CANCEL_TASK",
    "START_PROCESSOR",
    "STOP_PROCESSOR",
    "PAUSE_PROCESSOR",
    "RESUME_PROCESSOR",
    "LOCK_PROCESSOR",
    "UNLOCK_PROCESSOR",
    "VIEW_PROCESSOR",
    "VIEW_PROCESSOR_CONFIG",
    "VIEW_PROCESSOR_CODE",
    "EDIT_PROCESSOR_CONFIG",
    "EDIT_PROCESSOR_CODE" "LS_PROCESSORS",
    "LS_USERS",
    "LS_USER",
    "LS_PLUGS",
    "LS_SOCKETS",
    "LS_QUEUES",
    "LS_AGENTS",
    "LS_NODES",
    "LS_SCHEDULERS",
    "LS_WORKERS",
    "ADD_PROCESSOR",
    "ADD_AGENT",
    "ADD_NODE",
    "ADD_PLUG",
    "ADD_PRIVILEGE",
    "ADD_QUEUE",
    "ADD_ROLE",
    "ADD_SCHEDULER",
    "ADD_SOCKET",
    "ADD_USER",
    "UPDATE_PROCESSOR",
    "UPDATE_AGENT",
    "UPDATE_NODE",
    "UPDATE_PLUG",
    "UPDATE_ROLE",
    "UPDATE_SCHEDULER",
    "UPDATE_SOCKET",
    "UPDATE_USER",
    "DELETE_PROCESSOR",
    "DELETE_AGENT",
    "DELETE_NODE",
    "DELETE_PLUG",
    "DELETE_PRIVILEGE",
    "DELETE_QUEUE",
    "DELETE_ROLE",
    "DELETE_SCHEDULER",
    "DELETE_SOCKET",
    "DELETE_USER",
    "READ_PROCESSOR",
    "READ_AGENT",
    "READ_NODE",
    "READ_LOG",
    "READ_PLUG",
    "READ_PRIVILEGE",
    "READ_QUEUE",
    "READ_ROLE",
    "READ_SCHEDULER",
    "READ_SOCKET",
    "READ_USER",
]


class PrivilegeModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "privilege"

    right = Column("right", Enum(*rights, name="right"))


role_privileges = Table(
    "role_privileges",
    Base.metadata,
    Column("role_id", ForeignKey("role.id")),
    Column("privilege_id", ForeignKey("privilege.id")),
)


class RoleModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "role"

    privileges = relationship(
        "PrivilegeModel", secondary=role_privileges, lazy="subquery"
    )


user_privileges_revoked = Table(
    "user_privileges_revoked",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("privilege_id", ForeignKey("privilege.id")),
)

user_privileges = Table(
    "user_privileges",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("privilege_id", ForeignKey("privilege.id")),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("role_id", ForeignKey("role.id")),
)


class UserModel(HasLogins, BaseModel):
    """
    Docstring
    """

    __tablename__ = "users"
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), unique=False, nullable=False)
    clear = Column(String(60), unique=False, nullable=False)

    privileges = relationship(
        "PrivilegeModel", secondary=user_privileges, lazy="subquery"
    )

    revoked = relationship(
        "PrivilegeModel", secondary=user_privileges_revoked, lazy="subquery"
    )

    roles = relationship("RoleModel", secondary=user_roles, lazy="subquery")


socket_types = ["RESULT", "ERROR"]

plug_types = ["RESULT", "ERROR"]

schedule_types = ["CRON", "INTERVAL"]

strategies = ["BALANCED", "EFFICIENT"]


class FileModel(BaseModel):

    __tablename__ = "file"

    path = Column(String(120))
    filename = Column(String(80))
    collection = Column(String(80))
    code = Column(Text)
    type = Column(String(40))
    icon = Column(String(40))
    versions = relationship(
        "VersionModel", back_populates="file", cascade="all, delete-orphan"
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True)


flows_versions = Table(
    "flows_versions",
    Base.metadata,
    Column("flow_id", ForeignKey("flow.id"), primary_key=True),
    Column("version_id", ForeignKey("versions.id"), primary_key=True),
)


class FlowModel(BaseModel):
    """
    A flow model
    """

    __tablename__ = "flow"

    # Collection of processors within this flow. A processor can reside
    # in multiple flows at once
    processors = relationship("ProcessorModel", lazy=True)

    # File reference for this flow. i.e. it's saved state
    file_id = Column(String, ForeignKey("file.id"), nullable=False)
    file = relationship(
        "FileModel", lazy=True, cascade="all, delete-orphan", single_parent=True
    )

    # List of versions associated with this flow
    versions = relationship("VersionModel", secondary=flows_versions, lazy=True)


class AgentModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "agent"
    hostname = Column(String(60))
    cpus = Column(Integer)
    port = Column(Integer)
    pid = Column(Integer)

    workers = relationship(
        "WorkerModel", backref="agent", lazy=True, cascade="all, delete-orphan"
    )

    node_id = Column(String(40), ForeignKey("node.id"), nullable=False)


class ActionModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "action"
    params = Column(String(80))

    # host, worker, processor, queue, or all
    target = Column(String(20), nullable=False)


class WorkerModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "worker"
    backend = Column(String(40), nullable=False)
    broker = Column(String(40), nullable=False)
    concurrency = Column(Integer)
    process = Column(Integer)
    port = Column(Integer)
    hostname = Column(String(60))

    workerdir = Column(String(256))

    processor = relationship("ProcessorModel")
    processor_id = Column(
        String(40), ForeignKey("processor.id", ondelete="CASCADE"), nullable=False
    )

    deployment_id = Column(String(40), ForeignKey("deployment.id"), nullable=True)

    deployment = relationship("DeploymentModel", back_populates="worker")

    agent_id = Column(String(40), ForeignKey("agent.id"), nullable=False)

    # agent = relationship("AgentModel", back_populates="worker")


class ContainerModel(BaseModel):
    __tablename__ = "container"

    container_id = Column(String(80), unique=True, nullable=False)


class VersionModel(Base):
    __tablename__ = "versions"

    id = Column(
        String(40),
        autoincrement=False,
        default=literal_column("uuid_generate_v4()"),
        unique=True,
        primary_key=True,
    )
    name = Column(String(80), unique=False, nullable=False)
    file_id = Column(String, ForeignKey("file.id"), nullable=False)
    file = relationship(
        "FileModel", lazy=True, cascade="all, delete-orphan", single_parent=True
    )
    owner = Column(String(40), default=literal_column("current_user"))
    flow = Column(Text, unique=False, nullable=False)

    version = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )


class DeploymentModel(BaseModel):
    __tablename__ = "deployment"

    name = Column(String(80), unique=False, nullable=False)
    hostname = Column(String(80), nullable=False)
    cpus = Column(Integer, default=1, nullable=False)
    processor_id = Column(String(40), ForeignKey("processor.id"), nullable=False)

    worker = relationship(
        "WorkerModel", lazy=True, uselist=False, back_populates="deployment"
    )


class ProcessorModel(HasLogs, BaseModel):
    """
    Docstring
    """

    __tablename__ = "processor"

    module = Column(String(80), nullable=False)
    beat = Column(Boolean)
    gitrepo = Column(String(180))
    branch = Column(String(30), default="main")
    commit = Column(String(50), nullable=True)
    gittag = Column(String(50), nullable=True)
    retries = Column(Integer)
    concurrency = Column(Integer)
    receipt = Column(String(80), nullable=True)
    ratelimit = Column(String(10), default=60)
    perworker = Column(Boolean, default=True)
    timelimit = Column(Integer)
    ignoreresult = Column(Boolean)
    serializer = Column(String(10))
    backend = Column(String(80))
    ackslate = Column(Boolean)
    trackstarted = Column(Boolean)
    disabled = Column(Boolean)
    retrydelay = Column(Integer)
    password = Column(Boolean)
    requirements = Column(Text)
    endpoint = Column(Text)
    modulepath = Column(Text)
    icon = Column(Text)
    cron = Column(Text)
    hasapi = Column(Boolean)
    uistate = Column(Text)

    description = Column(Text(), nullable=True, default="Some description")
    container_image = Column(String(60))
    container_command = Column(String(180))
    container_version = Column(String(20), default="latest")
    use_container = Column(Boolean, default=False)
    detached = Column(Boolean, default=False)

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", backref="processor", lazy=True)

    flow_id = Column(String(40), ForeignKey("flow.id"), nullable=True)

    password = relationship("PasswordModel", lazy=True, viewonly=True)
    password_id = Column(String, ForeignKey("passwords.id"), nullable=True)

    plugs = relationship(
        "PlugModel", backref="processor", lazy=True, cascade="all, delete-orphan"
    )

    deployments = relationship(
        "DeploymentModel", backref="processor", lazy=True, cascade="all, delete-orphan"
    )

    sockets = relationship(
        "SocketModel", backref="processor", lazy=True, cascade="all, delete-orphan"
    )


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String(200), primary_key=True)
    next_run_time = Column(DOUBLE_PRECISION)
    job_state = Column(LargeBinary)


class PasswordModel(BaseModel):
    __tablename__ = "passwords"

    id = Column(
        String(40),
        autoincrement=False,
        default=literal_column("uuid_generate_v4()"),
        unique=True,
        primary_key=True,
    )
    password = Column(String(60), nullable=False)

    processor = relationship("ProcessorModel", lazy=True, uselist=False)


class NetworkModel(BaseModel):
    __tablename__ = "network"

    schedulers = relationship(
        "SchedulerModel", backref="network", lazy=True, cascade="all, delete"
    )

    queues = relationship(
        "QueueModel", backref="network", lazy=True, cascade="all, delete"
    )
    nodes = relationship(
        "NodeModel", backref="network", lazy=True, cascade="all, delete"
    )

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True)


class WorkModel(BaseModel):
    __tablename__ = "work"

    next_run_time = Column(DOUBLE_PRECISION)
    job_state = Column(LargeBinary)

    task_id = Column(String(40), ForeignKey("task.id"))
    task = relationship("TaskModel", single_parent=True)


calls_events = Table(
    "calls_events",
    Base.metadata,
    Column("call_id", ForeignKey("call.id"), primary_key=True),
    Column("event_id", ForeignKey("event.id"), primary_key=True),
)


class CallModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "call"

    name = Column(String(80), unique=False, nullable=False)
    state = Column(String(10))
    parent = Column(String(80), nullable=True)
    taskparent = Column(String(80), nullable=True)
    resultid = Column(String(80))
    celeryid = Column(String(80))
    tracking = Column(String(80))
    argument = Column(String(40))

    task_id = Column(String(40), ForeignKey("task.id"), nullable=False)
    started = Column(DateTime, default=datetime.now, nullable=False)
    finished = Column(DateTime)

    socket_id = Column(String(40), ForeignKey("socket.id"), nullable=False)
    socket = relationship(
        "SocketModel", back_populates="call", lazy=True, uselist=False
    )

    events = relationship(
        "EventModel", secondary=calls_events, lazy=True, cascade="all, delete"
    )


class SchedulerModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "scheduler"

    nodes = relationship("NodeModel", backref="scheduler", lazy=True)
    strategy = Column("strategy", Enum(*strategies, name="strategies"))

    network_id = Column(String(40), ForeignKey("network.id"))


class SettingsModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "settings"
    value = Column(String(80), nullable=False)


class NodeModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "node"
    hostname = Column(String(60))
    scheduler_id = Column(String(40), ForeignKey("scheduler.id"), nullable=True)

    memsize = Column(String(60), default="NaN")
    freemem = Column(String(60), default="NaN")
    memused = Column(Float, default=0)

    disksize = Column(String(60), default="NaN")
    diskusage = Column(String(60), default="NaN")
    cpus = Column(Integer, default=0)
    cpuload = Column(Float, default=0)

    network_id = Column(String(40), ForeignKey("network.id"))

    agent = relationship(
        "AgentModel", backref="node", uselist=False, cascade="all, delete-orphan"
    )


plugs_arguments = Table(
    "plugs_arguments",
    Base.metadata,
    Column("plug_id", ForeignKey("plug.id"), primary_key=True),
    Column("argument_id", ForeignKey("argument.id"), primary_key=True),
)


class ArgumentModel(BaseModel):
    __tablename__ = "argument"

    name = Column(String(60), nullable=False)
    position = Column(Integer, default=0)
    kind = Column(Integer)

    task_id = Column(String(40), ForeignKey("task.id"))

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True)
    plugs = relationship("PlugModel", backref="argument")


class TaskModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "task"

    module = Column(String(120), nullable=False, primary_key=True)
    gitrepo = Column(String(180), nullable=False, primary_key=True)
    """
    Tasks can also be mixed-in to the module loaded by the processor as new functions
    using the code field, which must contain a function
    """
    mixin = Column(Boolean, default=False)

    source = Column(Text)  # Repo module function code
    code = Column(Text)  # Source code override for task

    sockets = relationship("SocketModel", back_populates="task")

    arguments = relationship("ArgumentModel", backref="task")


class EventModel(BaseModel):
    """
    Events are linked to call objects: received, prerun, postrun
    """

    __tablename__ = "event"
    note = Column(String(80), nullable=False)
    name = Column(String(80), nullable=False)

    call_id = Column(String(40), ForeignKey("call.id"))
    call = relationship(
        "CallModel",
        back_populates="events",
        single_parent=True,
        cascade="all, delete-orphan",
    )


sockets_queues = Table(
    "sockets_queues",
    Base.metadata,
    Column("socket_id", ForeignKey("socket.id")),
    Column("queue_id", ForeignKey("queue.id")),
)

plugs_source_sockets = Table(
    "plugs_source_sockets",
    Base.metadata,
    Column("plug_id", ForeignKey("plug.id"), primary_key=True),
    Column("socket_id", ForeignKey("socket.id"), primary_key=True),
)
plugs_target_sockets = Table(
    "plugs_target_sockets",
    Base.metadata,
    Column("plug_id", ForeignKey("plug.id"), primary_key=True),
    Column("socket_id", ForeignKey("socket.id"), primary_key=True),
)


class GateModel(BaseModel):
    __tablename__ = "gate"

    open = Column(Boolean)
    task_id = Column(String(40), ForeignKey("task.id"))


class SocketModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "socket"
    processor_id = Column(String(40), ForeignKey("processor.id"), nullable=False)

    schedule_type = Column("schedule_type", Enum(*schedule_types, name="schedule_type"))

    scheduled = Column(Boolean)
    cron = Column(String(20))

    description = Column(Text(), nullable=True, default="Some description")
    interval = Column(Integer)
    task_id = Column(String(40), ForeignKey("task.id"))
    task = relationship(
        "TaskModel",
        back_populates="sockets",
        single_parent=True,
        cascade="delete, delete-orphan",
    )

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True)

    # Wait for all sourceplugs to deliver their data before invoking the task
    wait = Column(Boolean, default=False)

    sourceplugs = relationship("PlugModel", secondary=plugs_source_sockets)

    targetplugs = relationship("PlugModel", secondary=plugs_target_sockets)

    queue = relationship("QueueModel", secondary=sockets_queues, uselist=False)

    call = relationship(
        "CallModel", back_populates="socket", cascade="all, delete-orphan"
    )


plugs_queues = Table(
    "plugs_queues",
    Base.metadata,
    Column("plug_id", ForeignKey("plug.id")),
    Column("queue_id", ForeignKey("queue.id")),
)


class PlugModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "plug"

    type = Column("type", Enum(*plug_types, name="plug_type"), default="RESULT")

    processor_id = Column(String(40), ForeignKey("processor.id"), nullable=False)

    source = relationship(
        "SocketModel",
        back_populates="sourceplugs",
        secondary=plugs_source_sockets,
        uselist=False,
    )

    target = relationship(
        "SocketModel",
        back_populates="targetplugs",
        secondary=plugs_target_sockets,
        uselist=False,
    )
    argument_id = Column(String, ForeignKey("argument.id"))

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True)

    description = Column(Text(), nullable=True, default="Some description")
    queue = relationship("QueueModel", secondary=plugs_queues, uselist=False)


class QueueModel(BaseModel):
    """
    Docstring
    """

    __tablename__ = "queue"
    qtype = Column(String(20), nullable=False, default="direct")
    durable = Column(Boolean, default=True)
    reliable = Column(Boolean, default=True)
    auto_delete = Column(Boolean, default=True)
    max_length = Column(Integer, default=-1)
    max_length_bytes = Column(Integer, default=-1)
    message_ttl = Column(Integer, default=3000)
    expires = Column(Integer, default=3000)

    network_id = Column(String(40), ForeignKey("network.id"))


class LoginModel(Base):
    __tablename__ = "login"

    id = Column(
        String(40),
        autoincrement=False,
        default=literal_column("uuid_generate_v4()"),
        unique=True,
        primary_key=True,
    )
    owner = Column(String(40), default=literal_column("current_user"))

    created = Column(DateTime, default=datetime.now, nullable=False)
    lastupdated = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    login = Column(DateTime, default=datetime.now, nullable=False)
    token = Column(
        String(40),
        autoincrement=False,
        default=literal_column("uuid_generate_v4()"),
        unique=True,
        primary_key=True,
    )

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("UserModel", lazy=True, overlaps="logins")


oso.register_class(BaseModel)
oso.register_class(PasswordModel)
oso.register_class(UserModel)
oso.register_class(LogModel)
oso.register_class(ProcessorModel)
oso.register_class(QueueModel)
oso.register_class(SocketModel)
oso.register_class(PlugModel)
oso.register_class(AgentModel)
oso.register_class(WorkerModel)
oso.register_class(NodeModel)
oso.register_class(FlowModel)
oso.register_class(RoleModel)
oso.register_class(PrivilegeModel)
oso.register_class(ActionModel)
oso.register_class(EventModel)
oso.register_class(SchedulerModel)
oso.register_class(CallModel)
oso.register_class(TaskModel)
oso.register_class(ArgumentModel)
oso.register_class(NetworkModel)
oso.register_class(GateModel)
oso.register_class(LoginModel)
oso.register_class(JobModel)
oso.register_class(DeploymentModel)
oso.register_class(FileModel)
