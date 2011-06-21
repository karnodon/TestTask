/**
 * Created by PyCharm.
 * User: Frostbite
 * Date: 19.06.11
 * Time: 15:40
 */

var c = 0;
var timer;
var timer_is_on = 0;

function timedCount() {
    try {
        c =  parseInt(document.getElementById('tictac').value);
    }
    catch (err) {
        c = 0;
    }
    c = c + 1;
    try {
        document.getElementById('tictac').value = c;
        document.getElementById('tictacdisplay').innerHTML = formatTicTac();
    }
    catch (err) {}
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
    return h + ":" + m + ":" + s;
}

function validateAnswer() {
    var opts = document.getElementsByName('option');
    for (var i = 0; i < opts.length; i++) {
        var opt = opts[i];
        if ((opt.type == 'text' && opt.value != '') || opt.checked)
            return true;
    }
    return false;
}