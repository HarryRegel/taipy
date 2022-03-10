from __future__ import annotations

import typing as t
import warnings
from types import SimpleNamespace

from flask import request


class _DataScopes:
    def __init__(self) -> None:
        self.__scopes: t.Dict[str, SimpleNamespace] = {}
        self.__scopes["global"] = SimpleNamespace()
        self.__single_client = False

    def set_single_client(self, value: bool) -> None:
        self.__single_client = value

    def get_single_client(self) -> bool:
        return self.__single_client

    def get_scope(self) -> SimpleNamespace:
        if self.__single_client or not request:
            return self.__scopes["global"]
        # global context in case request is not registered or client_id is not available (such as in the context of running tests)
        client_id = getattr(request, "taipy_client_id", "")
        if not client_id:
            client_id = request.args.get("client_id", "")
        if not client_id:
            warnings.warn("Empty session id, using global scope instead")
            return self.__scopes["global"]
        if client_id not in self.__scopes:
            warnings.warn(
                f"session id {client_id} not found in data scope. Taipy will automatically create a scope for this session id but you might have to reload your webpage"
            )
            self.create_scope(client_id)
        return self.__scopes[client_id]

    def _set_client_id(self, client_id: t.Optional[str]):
        if client_id:
            setattr(request, "taipy_client_id", client_id)

    def get_all_scopes(self) -> t.Dict[str, SimpleNamespace]:
        return self.__scopes

    def broadcast_data(self, name, value):
        if self.__single_client:
            return
        if not hasattr(request, "taipy_client_id"):
            for _, v in self.__scopes.items():
                if hasattr(v, name):
                    setattr(v, name, value)

    def create_scope(self, id: str) -> None:
        if self.__single_client:
            return
        if id is None:
            warnings.warn("Empty session id, might be due to unestablished WebSocket connection")
            return
        if id not in self.__scopes:
            self.__scopes[id] = SimpleNamespace()

    def delete_scope(self, id: str) -> None:  # pragma: no cover
        if self.__single_client:
            return
        if id is None:
            warnings.warn("Empty session id, might be due to unestablished WebSocket connection")
            return
        if id in self.__scopes:
            del self.__scopes[id]
