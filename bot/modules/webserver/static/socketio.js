$(document).ready(function() {
    // https://stackoverflow.com/a/38311629/8967590
    $.fn.setClass = function(classes) {
        this.attr('class', classes);
        return this;
    };

    // https://stackoverflow.com/a/46308265,
    // slightly modified for better readability
    $.fn.selectText = function(){
        let element = this[0], range, selection;
        if (document.body.createTextRange) {
            range = document.body.createTextRange();
            range.moveToElementText(element);
            range.select();
            document.execCommand('copy');
        } else if (window.getSelection) {
            selection = window.getSelection();
            range = document.createRange();
            range.selectNodeContents(element);
            selection.removeAllRanges();
            selection.addRange(range);
            document.execCommand('copy');
        }
    };

    $.fn.upsert = function(target_element_id, htmlString) {
        // upsert - find or create new element
        // find based on css selector     https://api.jquery.com/category/selectors/
        // create based on jQuery()       http://api.jquery.com/jquery/#jQuery2
        let $el = $(this).find(target_element_id);
        if ($el.length === 0) {
            // didn't exist, create and add to caller
            $el = $(htmlString);
            $(this).append($el);
        }

        return $el;
    };

    //connect to the socket server.
    window.socket = io.connect(
        'http://' + document.domain + ':' + location.port + '/chrani-bot-ng'
    );

    window.socket.on('connected', function() {
        console.log("connected...");
        window.socket.emit('ding');
        console.log("sent 'ding' to server");
    });

    window.socket.on('dong', function() {
        console.log("got 'dong' from server");
        window.setTimeout(
            function () {
                window.socket.emit('ding');
                console.log("sent 'ding' to server");
            },
            15000);
    });

    function request_player_table_widget_row(widget, widget_id, row_id) {
        window.socket.emit('widget_event', ['players', ['request_table_row', {'widget': widget, 'widget_id': widget_id, 'row_id': row_id}]]);
    }

    window.socket.on('data', function(data) {
        if (data["data_type"] === "player_table_widget_row") {
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }
            let selector = data["target_element"]["selector"];

            let parent_element = $(selector);
            parent_element.append(data["event_data"]);
        }
        if (data["data_type"] === "player_table_widget_row_content") {
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }
            let selector = data["target_element"]["selector"];

            let parent_element = $('#' + target_element_id + '_' + data["event_data"]["steamid"]);
            if (parent_element.length === 0) {
                /* seems like the container we want ain't here- let's request it */
                request_player_table_widget_row(data["target_element"]["parent_id"], target_element_id, data["event_data"]["steamid"]);
                return false;
            }

            parent_element.setClass(data["target_element"]["class"]);

            let elements_to_update = data["event_data"];
            $.each(elements_to_update, function (key, value) {
                if ($.type(value) === 'object') {
                    $.each(value, function (sub_key, sub_value) {
                        let element_to_update = $('#' + target_element_id + '_' + data["event_data"]["steamid"] + '_' + key + '_' + sub_key);
                        if (element_to_update.text() !== sub_value.toString()) {
                            element_to_update.html(sub_value);
                        }
                    });
                } else {
                    let element_to_update = $('#' + target_element_id + '_' + data["event_data"]["steamid"] + '_' + key);
                    if (element_to_update.text() !== value.toString()) {
                        element_to_update.html(value);
                    }
                }
            });
        }

        if (data["data_type"] === "element_content") {
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }
            let dummy_id = data["target_element"]["dummy_id"];
            if (dummy_id == null) {
                dummy_id = "player_table_row_"
            }
            let selector = data["target_element"]["selector"];

            let parent_element = $('#' + target_element_id);
            if (parent_element.length === 0) {
                /* seems like the container we want ain't here- let's request it */
                request_player_table_widget_row(target_element_id, data["event_data"]["steamid"])
            }

            parent_element.setClass(data["target_element"]["class"]);

            let elements_to_update = data["event_data"];
            $.each(elements_to_update, function (key, value) {
                if ($.type(value) === 'object') {
                    $.each(value, function (sub_key, sub_value) {
                        let element_to_update = $('#' + target_element_id + '_' + key + '_' + sub_key);
                        if (element_to_update.text() !== sub_value.toString()) {
                            element_to_update.html(sub_value);
                        }
                    });
                } else {
                    let element_to_update = $('#' + target_element_id + '_' + key);
                    if (element_to_update.text() !== value.toString()) {
                        element_to_update.html(value);
                    }
                }
            });
        } else if (data["data_type"] === "widget_content") {
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }
            let selector = data["target_element"]["selector"];
            let $el = $(selector).upsert('#' + target_element_id, '<div id="' + target_element_id + '" class="widget"></div>');

            if (data["method"] === "update") {
                $el.html(data["event_data"]);

            } else if (data["method"] === "append") {
                $el.append(data["event_data"]);

            } else if (data["method"] === "prepend") {
                $el = $('#' + data["target_element"]["id"] + ' ' + data["target_element"]["type"]);
                $el.prepend(data["event_data"]);
                let $entries = $el.find('li');
                if ($entries.length >= 50) {
                    $entries.last().remove();
                }
            }
        } else if (data["data_type"] === "status_message") {
            console.log("received status '" + data['status'] + "' for event '" + data['event_data'][0] + "' from server");
        } else if (data["data_type"] === "alert_message") {
            alert(data['status']);
        }
    });

});

