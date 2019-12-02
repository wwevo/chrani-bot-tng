document.addEventListener("DOMContentLoaded", function(event) {

    // based on https://stackoverflow.com/a/56279295/8967590
    Audio.prototype.play = (function(play) {
        return function () {
            let audio = this;
            let promise = play.apply(audio, arguments);
            if (promise !== undefined) {
                promise.catch(_ => {
                    console.log("autoplay of audiofile failed :(");
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

    /* found on https://stackoverflow.com/a/21648508/8967590
     * slightly modified to only return the rgb value and getting rid of type-warnings
     */
    function hexToRgb(hex){
        let char;
        if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
            char = hex.substring(1).split('');
            if (char.length === 3) {
                char = [char[0], char[0], char[1], char[1], char[2], char[2]];
            }
            char = '0x' + char.join('');
            return [(char >> 16) & 255, (char >> 8) & 255, char & 255].join(', ');
        } else {
            alert(hex);
            throw new Error('Bad Hex');
        }
    }

    let lcars_colors = []
    function load_lcars_colors() {
        /* https://davidwalsh.name/css-variables-javascript */
        lcars_colors["lcars-brown"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-brown').trim()
        );
        lcars_colors["lcars-orange"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-orange').trim()
        );
        lcars_colors["lcars-yellow"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-yellow').trim()
        );
        lcars_colors["lcars-red"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-red').trim()
        );
        lcars_colors["lcars-purple"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-purple').trim()
        );
        lcars_colors["lcars-lilac"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-lilac').trim()
        );
        lcars_colors["lcars-dark-blue"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-dark-blue').trim()
        );
        lcars_colors["lcars-light-blue"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--lcars-light-blue').trim()
        );
        lcars_colors["background"] = hexToRgb(
            getComputedStyle(document.documentElement).getPropertyValue('--background').trim()
        );
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

    let flash = function(elements, color=false) {
        let opacity = 40;
        if (color === false) {
            color = lcars_colors["lcars-yellow"]; // has to be in this format since we use rgba
        }
        let interval = setInterval(function() {
            opacity -= 2.5;
            if (opacity <= 0) {
                clearInterval(interval);
                $(elements).removeAttr('style');
            } else {
                $(elements).css({
                    "background-color": "rgba(" + color + ", " + (opacity / 50) + ")"
                });
            }
        }, 20)
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

    load_audio_files();
    load_lcars_colors();

    window.socket.on('data', function(data) {
        if ([
            "element_content",
            "widget_content",
            "remove_table_row",
            "table_row",
            "table_row_content"
        ].includes(data["data_type"])) {
            /* target element needs to be present for these operations */
            let target_element_id = data["target_element"]["id"];
            if (target_element_id == null) {
                return false;
            }

            if (data["data_type"] === "widget_content") {
                /* widget content requires a selector, in case the widget is not yet rendered in the browser
                 * with the help of the selector, we can create it in the right place
                 */
                let html_string = '<div id="' + target_element_id + '" class="widget"></div>';
                let selector = data["target_element"]["selector"];
                let target_element = $(selector).upsert(
                    '#' + target_element_id,
                    html_string
                );

                if (data["method"] === "update") {
                    target_element.html(data["payload"]);
                    // console.log("widget content updated");
                    // flash(target_element);
                } else if (data["method"] === "append") {
                    target_element.append(data["payload"]);
                    // console.log("widget content appended");
                    // flash(target_element);
                } else if (data["method"] === "prepend") {
                    play_audio_file("computerbeep_38");
                    let target_table = $('#' + target_element_id + ' ' + data["target_element"]["type"]);
                    /* prepend adds a row on top */
                    target_table.prepend(data["payload"]);
                    let $entries = target_table.find('tr');
                    if ($entries.length >= 50) {
                        $entries.last().remove();
                    }
                    // console.log("widget content prepended");
                    // flash($entries[1]);
                }
            }
            if (data["data_type"] === "element_content") {
                let target_element = document.getElementById(target_element_id);
                if (target_element == null) {
                    return false;
                }
                if (data["method"] === "update") {
                    if (target_element.innerHTML !== data["payload"]) {
                        target_element.innerHTML = data["payload"];
                        // flash(target_element);
                        // console.log("element content appended");
                    } else {
                        return false;
                    }
                } else if (data["method"] === "replace") {
                    target_element.outerHTML = data["payload"];
                    flash(target_element);
                    // console.log("element content replaced");
                }
            }
            if (data["data_type"] === "table_row") {
                /* the whole row will be swapped out, not very economic ^^
                 * can be suitable for smaller widgets, not needing the hassle of sub-element id's and stuff
                 * table_row content requires a selector, in case the row is not yet rendered in the browser
                 * with the help of the selector, we can create it in the right place
                 */
                play_audio_file("processing");
                let parent_element = $(data["target_element"]["selector"]);

                let target_element = parent_element.find("#" + target_element_id);

                if (target_element.length === 0) {
                    /* If the row doesn't exist, append it */
                    parent_element.append(data["payload"]);
                    // console.log("table row added");
                } else {
                    target_element.replaceWith(data["payload"]);
                    // console.log("table row replaced");
                }
                // flash(target_element);
            }
            if (data["data_type"] === "table_row_content") {
                play_audio_file("keyok1");
                let parent_element = $('#' + target_element_id);
                if (parent_element.length === 0) {
                    return false;
                }
                if (data["target_element"]["class"].length >= 1) {
                    parent_element.setClass(data["target_element"]["class"]);
                } else {
                    parent_element[0].removeAttribute("class");
                }

                let elements_to_update = data["payload"];
                $.each(elements_to_update, function (key, value) {
                    if ($.type(value) === 'object') {
                        $.each(value, function (sub_key, sub_value) {
                            let element_to_update = $('#' + target_element_id + '_' + key + '_' + sub_key);
                            if (element_to_update.length !== 0 && element_to_update.text() !== sub_value.toString()) {
                                element_to_update.html(sub_value);
                                // console.log("table row content updated");
                                // flash(element_to_update);
                            }
                        });
                    } else {
                        let element_to_update = $('#' + target_element_id + '_' + key);
                        if (element_to_update.length !== 0 && element_to_update.text() !== value.toString()) {
                            element_to_update.html(value);
                            // console.log("table row content updated");
                            // flash(element_to_update);
                        }
                    }
                });
            }
            if (data["data_type"] === "remove_table_row") {
                let target_element = document.getElementById(target_element_id);
                target_element.parentElement.removeChild(target_element);
            }
        } else if (data["data_type"] === "status_message") {
            /* this does not require any website containers. we simply play sounds and echo logs */
            if (data['status']) {
                let json = data["status"];
                if (json["status"]) {
                    let status = json["status"];
                    if (status === "success") {
                        play_audio_file("computerbeep_11");
                    } else if (status === "fail") {
                        play_audio_file("computer_error");
                        flash(document.body, lcars_colors["lcars-red"])
                    }
                    console.log("received status from server\n\"" + status + ":" + json["uuid4"] + "\"");
                }
            }
        }
    });
});
