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
        let $el = $(this).find(target_element_id);
        if ($el.length === 0) {
            // didn't exist, create and add to caller
            $el = $(htmlString);
            $(this).prepend($el);
        }

        return $el;
    };

    //connect to the socket server.
    window.socket = io.connect(
        'http://' + document.domain + ':' + location.port, {
            'sync disconnect on unload': true
        }
    );

    window.socket.on('connected', function() {
        console.log("connected...");
        window.socket.emit('ding');
        console.log("sent 'ding' to server");
    });

    let ding_dong_times = [];
        let start_time;
        start_time = (new Date).getTime();
        window.setInterval(function() {
            start_time = (new Date).getTime();
            socket.emit('ding');
        }, 10000);

    window.socket.on('dong', function() {
        let latency = (new Date).getTime() - start_time;
        console.log("ding/dong took " + latency + "ms");
    });

    function request_player_table_widget_row(module, widget, widget_id, row_id) {
        window.socket.emit('widget_event', [module, ['request_table_row', {'widget': widget, 'widget_id': widget_id, 'row_id': row_id}]]);
    }

    window.socket.on('data', function(data) {
        if (data["data_type"] === "element_content") {
            let target_element_id = data["target_element"]["id"];
            let target_element = document.getElementById(target_element_id);
            if (target_element_id == null || target_element == null) {
                return false;
            }
            if (target_element.innerHTML !== data["event_data"]) {
                target_element.innerHTML = data["event_data"];
            } else {
                return false;
            }
        }
        if (data["data_type"] === "widget_content") {
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
        }
        if (data["data_type"] === "table_row") {
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }
            let selector = data["target_element"]["selector"];

            let parent_element = $(selector);
            let target_element = parent_element.find("#" + target_element_id);

            if (target_element.length === 0) {
                parent_element.append(data["event_data"]);
            } else {
                target_element.replaceWith(data["event_data"]);
            }
        }
        if (data["data_type"] === "table_row_content") {
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }
            let target_player_steamid = data["event_data"]["steamid"];
            if (target_player_steamid == null) {
                return false;
            }
            let selector = data["target_element"]["selector"];

            let parent_element = $('#' + target_element_id + '_' + target_player_steamid);
            if (parent_element.length === 0) {
                /* seems like the container we want ain't here- let's request it */
                request_player_table_widget_row(
                    data["target_element"]["module"],
                    data["target_element"]["parent_id"],
                    target_element_id,
                    data["event_data"]["steamid"]
                );
                return false;
            }

            parent_element.setClass(data["target_element"]["class"]);

            let elements_to_update = data["event_data"];
            $.each(elements_to_update, function (key, value) {
                if ($.type(value) === 'object') {
                    $.each(value, function (sub_key, sub_value) {
                        let element_to_update = $('#' + target_element_id + '_' + data["event_data"]["steamid"] + '_' + key + '_' + sub_key);
                        if (element_to_update.length !== 0 && element_to_update.text() !== sub_value.toString()) {
                            element_to_update.html(sub_value);
                        }
                    });
                } else {
                    let element_to_update = $('#' + target_element_id + '_' + data["event_data"]["steamid"] + '_' + key);
                    if (element_to_update.length !== 0 && element_to_update.text() !== value.toString()) {
                        element_to_update.html(value);
                    }
                }
            });
        }
        if (data["data_type"] === "status_message") {
            console.log("received status '" + data['status'] + "' for event '" + data['event_data'][0] + "' from server");
        }
        if (data["data_type"] === "alert_message") {
            alert(data['status']);
        }
    });

});

