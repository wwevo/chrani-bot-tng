$(document).ready(function() {
    //connect to the socket server.
    let socket = io.connect(
        'http://' + document.domain + ':' + location.port + '/chrani-bot-ng'
    );

    socket.on('connected', function() {
        console.log("connected...");
        socket.emit('ding');
        console.log("sent 'ding'");
    });

    socket.on('dong', function() {
        console.log("got 'dong'");
        window.setTimeout(
            function () {
                socket.emit('ding');
                console.log("sent 'ding'");
            },
            5000);
    });

    socket.on('widget', function(data) {
        console.log(data);
    });


});

