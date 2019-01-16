$(document).ready(function() {
    // https://stackoverflow.com/a/46308265
    $.fn.upsert = function(selector, htmlString) {
        // upsert - find or create new element
        // find based on css selector     https://api.jquery.com/category/selectors/
        // create based on jQuery()       http://api.jquery.com/jquery/#jQuery2
        let $el = $(this).find(selector);
        if ($el.length === 0) {
            // didn't exist, create and add to caller
            $el = $(htmlString);
            $(this).append($el);
        }

        return $el;
    };

    //connect to the socket server.
    let socket = io.connect(
        'http://' + document.domain + ':' + location.port + '/chrani-bot-ng'
    );

    socket.on('connected', function() {
        console.log("connected...");
        socket.emit('ding');
        console.log("sent 'ding' to server");
    });

    socket.on('dong', function() {
        console.log("got 'dong' from server");
        window.setTimeout(
            function () {
                socket.emit('ding');
                console.log("sent 'ding' to server");
            },
            15000);
    });

    socket.on('widget', function(data) {
        let $el = $("body > main").upsert('#' + data["target_element"], '<div class="widget" id="' + data["target_element"] + '"></div>');
        if (data["method"] === "update") {
            $el.html(data["data"]);
        } else if (data["method"] === "append") {
            $el.append('<p>' + data["data"] + '</p>');
        } else if  (data["method"] === "prepend") {
            $el.prepend('<p>' + data["data"] + '</p>');
        }
    });


});

