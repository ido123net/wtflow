from uuid import uuid4


def create_uuid() -> str:
    return str(uuid4().hex)
