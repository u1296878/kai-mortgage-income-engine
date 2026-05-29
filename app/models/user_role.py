from enum import Enum


class UserRole(str, Enum):
    broker = "broker"
    manager = "manager"
