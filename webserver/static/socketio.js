$(document).ready(function() {
    //connect to the socket server.
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/dummy');
    socket.emit('dummy', '/dummy');
});

