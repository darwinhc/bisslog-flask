"""
Helper class for sending notifications through WebSocket using Flask-SocketIO.

This module provides a concrete implementation of the `WebSocketManager` interface,
allowing you to send events, manage rooms, and communicate with WebSocket clients
via Flask-SocketIO.
"""

from typing import Any

from bisslog.ports.ws_manager import WebSocketManager


class BisslogFlaskSocketHelper(WebSocketManager):
    """
    Flask-SocketIO implementation of the WebSocketManager interface.

    This class adapts Flask-SocketIO's functionality to the `bisslog` WebSocket contract,
    allowing event emission, room management, and direct message delivery using
    a consistent interface.
    """

    def __init__(self, conn) -> None:
        super().__init__(conn)

    def emit(self, event: str, connection_id: str, payload: Any,
             broadcast: bool = False, to: str = None):
        """
        Emit an event to a specific connection or to a room.

        Parameters
        ----------
        event : str
            Name of the event to emit.
        connection_id : str
            SocketIO session ID of the client.
        payload : Any
            Data to send.
        broadcast : bool, optional
            Whether to broadcast to all clients (default: False).
        to : str, optional
            Target room (if broadcasting).
        """
        self.conn.emit(
            event,
            payload,
            to=to or connection_id,
            broadcast=broadcast
        )

    def join_room(self, room: str, connection_id: str):
        """
        Add a connection to a room.

        Parameters
        ----------
        room : str
            Name of the room.
        connection_id : str
            Session ID of the connection to join the room.
        """
        self.conn.server.enter_room(connection_id, room)

    def leave_room(self, room: str, connection_id: str):
        """
        Remove a connection from a room.

        Parameters
        ----------
        room : str
            Name of the room.
        connection_id : str
            Session ID of the connection to leave the room.
        """
        self.conn.server.leave_room(connection_id, room)

    def rooms(self, connection_id: str):
        """
        Get a list of rooms the connection is part of.

        Parameters
        ----------
        connection_id : str
            Session ID of the client.

        Returns
        -------
        list[str]
            List of room names.
        """
        return list(self.conn.server.rooms(connection_id))

    def send(self, event: str, payload: Any = None, connection_id: str = None):
        """
        Send a message with or without an event name.

        Parameters
        ----------
        event : str
            Event name or message label.
        payload : Any, optional
            Payload to send.
        connection_id : str, optional
            Target client (if None, broadcast).
        """
        self.conn.send(payload or event, to=connection_id)
