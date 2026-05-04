from gdey0154f51.pi_server.config import PiServerConfig


def create_app(*args, **kwargs):  # type: ignore[no-untyped-def]
    from gdey0154f51.pi_server.app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app", "PiServerConfig"]
