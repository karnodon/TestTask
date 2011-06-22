/**
 * Created by PyCharm.
 * User: Frostbite
 * Date: 19.06.11
 * Time: 15:40
 */

var c = 0;
var timer;
var timer_is_on = 0;
var timeIsUp = false;

function timedCount() {
    try {
        c = parseInt(document.getElementById('tictac').value);
        var limit = parseInt(document.getElementById('limit').value);
        if (limit > 0 && limit <= c) {
            timeIsUp = true;
        }
    }
    catch (err) {
        c = 0;
    }
    c = c + 1;
    try {
        document.getElementById('tictac').value = c;
        if (timeIsUp) {
            document.getElementById('tictacdisplay').innerHTML = 'Время истекло!';
        } else {
            document.getElementById('tictacdisplay').innerHTML = formatTicTac();
        }
    }
    catch (err) {}
    if (!timeIsUp)
        timer = setTimeout("timedCount()", 1000);
}

function formatTicTac() {
    var h = Math.floor(c/3600);
    if (h < 10) {
        h = "0" + h.toString();
    }
    var m = Math.floor(c % 3600 /60);
    if (m < 10) {
        m = "0" + m.toString();
    }
    var s = (c % 3600 % 60);
    if (s < 10) {
        s = "0" + s.toString();
    }
    return "Прошло " + h + ":" + m + ":" + s;
}

function validateAnswer() {
    var opts = document.getElementsByName('option');
    for (var i = 0; i < opts.length; i++) {
        var opt = opts[i];
        if ((opt.type == 'text' && opt.value != '') || opt.checked)
            return !timeIsUp;
    }
    return false;
}