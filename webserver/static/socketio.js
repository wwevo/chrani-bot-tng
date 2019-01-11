$(document).ready(function() {
    //connect to the socket server.
    let socket = io.connect('http://' + document.domain + ':' + location.port + '/chrani-bot-ng');

    socket.on('connected', function(msg) {
        console.log(msg['message']);
        socket.emit('my event', { data: 'I\'m connected!' });
    });

    socket.on('my response', function(msg) {
        console.log(msg['message']);
        window.setTimeout(
            function () {
                socket.emit('my event', { data: 'Still connected!' });
            },
            5000);
    });
});

