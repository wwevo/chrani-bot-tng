$(document).ready(function() {
    //connect to the socket server.
    window.socket = io.connect('http://' + document.domain + ':' + location.port + '/chrani-bot-ng');

    window.socket.emit('dummy', '/chrani-bot-ng');

    window.socket.on('dummy', function() {
    });
});

