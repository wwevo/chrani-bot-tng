document.addEventListener("DOMContentLoaded", function(event) {

    // based on https://stackoverflow.com/a/56279295/8967590
    Audio.prototype.play = (function(play) {
        return function () {
            let audio = this;
            let promise = play.apply(audio, arguments);
            if (promise !== undefined) {
                promise.catch(_ => {
                    // Autoplay was prevented. you can take steps here, like notifying the user.
                });
            }
        };
    }) (Audio.prototype.play);

    let audio_files = [];

    function load_audio_files() {
        audio_files["computer_work_beep"] = new Audio('/static/lcars/audio/computer_work_beep.mp3');
        audio_files["computer_error"] = new Audio('/static/lcars/audio/computer_error.mp3');
        audio_files["keyok1"] = new Audio('/static/lcars/audio/keyok1.mp3');
        audio_files["keyok1"].volume = 0.05;
        audio_files["input_ok_2_clean"] = new Audio('/static/lcars/audio/input_ok_2_clean.mp3');
        audio_files["processing"] = new Audio('/static/lcars/audio/processing.mp3');
        audio_files["processing"].volume = 0.25;
        audio_files["computerbeep_11"] = new Audio('/static/lcars/audio/computerbeep_11.mp3');
        audio_files["computerbeep_11"].volume = 0.5;
        audio_files["computerbeep_38"] = new Audio('/static/lcars/audio/computerbeep_38.mp3');
        audio_files["computerbeep_38"].volume = 0.1;
        audio_files["computerbeep_65"] = new Audio('/static/lcars/audio/computerbeep_65.mp3');
        audio_files["alarm01"] = new Audio('/static/lcars/audio/alarm01.mp3');
        audio_files["alarm03"] = new Audio('/static/lcars/audio/alarm03.mp3');
        audio_files["alert12"] = new Audio('/static/lcars/audio/alert12.mp3');
    }

    function play_audio_file(identifier) {
        try {
            if (audio_files[identifier].readyState === 4) { // 4 = HAVE_ENOUGH_DATA
                if (!audio_files[identifier].ended) {
                    audio_files[identifier].currentTime = 0;
                    audio_files[identifier].play();
                    // console.log("replay");
                } else {
                    audio_files[identifier].play();
                    // console.log("play");
                }
            }
        } catch(err) {
            console.log("bleh:" + err);
        }
    }

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
    });

    let start_time = (new Date).getTime();

    window.setInterval(function() {
        start_time = (new Date).getTime();
        socket.emit('ding');
        play_audio_file("processing");

        console.log("sent 'ding' to server");
    }, 10000);

    window.socket.on('dong', function() {
        let latency = (new Date).getTime() - start_time;
        play_audio_file("keyok1");

        console.log("ding/dong took " + latency + "ms");
    });

    function request_player_table_widget_row(module, widget, widget_id, row_id) {
        window.socket.emit('widget_event', [module, ['request_table_row', {'widget': widget, 'widget_id': widget_id, 'row_id': row_id}]]);
    }

    load_audio_files();

    window.socket.on('data', function(data) {
        if (data["data_type"] === "element_content") {
            let target_element_id = data["target_element"]["id"];
            let target_element = document.getElementById(target_element_id);
            if (target_element_id == null || target_element == null) {
                return false;
            }
            if (data["method"] === "update") {
                if (target_element.innerHTML !== data["event_data"]) {
                    target_element.innerHTML = data["event_data"];
                } else {
                    return false;
                }
            } else if (data["method"] === "replace") {
                target_element.outerHTML = data["event_data"];
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
                play_audio_file("computerbeep_38");
                $el = $('#' + data["target_element"]["id"] + ' ' + data["target_element"]["type"]);
                $el.prepend(data["event_data"]);
                let $entries = $el.find('tr');
                if ($entries.length >= 50) {
                    $entries.last().remove();
                }
            }
        }
        if (data["data_type"] === "table_row") {
            play_audio_file("processing");
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

            if (data['status']) {
                let json = data["status"];

                if (json["status"]) {
                    let status = json["status"];

                    if (status === "success") {
                        play_audio_file("computerbeep_11");
                    } else if (status === "fail") {
                        play_audio_file("computer_error");
                    }
                    console.log("received status from server\n\"" + status + ":" + json["uuid4"] + "\"");
                }
            }
        }
        if (data["data_type"] === "alert_message") {
            alert(data['status']);
        }
    });

});
