from flask import request
from flask_login import current_user
from flask_socketio import emit
from time import time
from bot import loaded_modules_dict, started_modules_dict


class SocketIOHandlers(object):
    """
    Mixin for SocketIO event handlers.
    Requires: websocket (SocketIO), connected_clients dict, authenticated_only decorator
    """

    def __init__(self):
        pass

    def _register_socketio_handlers(self):
        """
        Register all SocketIO event handlers - called once during setup()
        Must be called after websocket is initialized.
        """

        @self.websocket.on('connect')
        @self.authenticated_only
        def connect_handler():
            if not hasattr(request, 'sid'):
                return False
            else:
                user = self.connected_clients[current_user.id]

                if len(user.socket_ids) > 0:
                    emit('session_conflict', {
                        'existing_sessions': len(user.socket_ids),
                        'message': 'another active session for this user detected. pick up existing session.'
                    }, room=request.sid)
                else:
                    user.add_socket(request.sid)
                    emit('session_accepted', room=request.sid)
                    for module in loaded_modules_dict.values():
                        module.on_socket_connect(current_user.id)
                    return None

        @self.websocket.on('disconnect')
        def disconnect_handler():
            if current_user.is_authenticated and current_user.id in self.connected_clients:
                user = self.connected_clients[current_user.id]
                user.remove_socket(request.sid)

        @self.websocket.on('ding')
        def ding_dong():
            current_user.last_seen = time()
            try:
                emit('dong', room=request.sid)
            except AttributeError as error:
                print("client_disappeared")

        @self.websocket.on('session_takeover_accept')
        @self.authenticated_only
        def session_takeover_accept():
            """User accepted to take over existing session - disconnect old sessions."""
            user = self.connected_clients[current_user.id]

            old_sockets = user.socket_ids.copy()
            for old_sid in old_sockets:
                emit('session_taken_over', {
                    'message': 'Ihre Session wurde von einem anderen Browser übernommen.'
                }, room=old_sid)
                self.websocket.server.disconnect(old_sid)
                user.remove_socket(old_sid)

            user.add_socket(request.sid)
            emit('session_accepted', room=request.sid)

            for module in loaded_modules_dict.values():
                module.on_socket_connect(current_user.id)

            print("session_takeover")

        @self.websocket.on('session_takeover_decline')
        @self.authenticated_only
        def session_takeover_decline():
            """User declined to take over - disconnect new session."""
            emit('session_declined', {
                'message': 'Session-Übernahme abgelehnt. Bitte schließen Sie die andere Session zuerst.'
            }, room=request.sid)

            self.websocket.server.disconnect(request.sid)

            print("session_takeover_declined")

        @self.websocket.on('browser_widget_action')
        @self.authenticated_only
        def browser_widget_action(action_data):
            """Widget events from the browser start here!"""
            action_module = started_modules_dict[action_data.get("action_module")]
            action = action_data.get("action")
            if action in action_module.available_actions_dict:
                action_module.on_browser_widget_action(
                    action_module, action_data, dispatchers_id=current_user.id
                )
