window.onload = function () {
    document.getElementById('project').value = window.localStorage.getItem('name');
    document.getElementById('method').value = window.localStorage.getItem('method');
    document.getElementById('timeline').value = window.localStorage.getItem('timeline');
    document.getElementById('timelineMin').value = window.localStorage.getItem('timelineMin');
    document.getElementById('timelineMax').value = window.localStorage.getItem('timelineMax');
    document.getElementById('diffpriv').value = window.localStorage.getItem('diffpriv');

    if (window.localStorage.getItem('groups')) {
        document.getElementById('groupColLabel').innerText = window.localStorage.getItem('groups') + " Column";
    } else {
        document.getElementById('groupColField').style.display = "none";
    }

    if (window.localStorage.getItem('method') === "cox") {
        document.getElementById('groupColField').style.display = "none";
    }
    if (window.localStorage.getItem('smpc') === "false") {
        document.getElementById('from').style.display = "none";
        document.getElementById('to').style.display = "none";
    }
};

function getPathToFile() {
    eel.get_path_to_file()(r => setPath(r))
}

function setPath(r) {
    window.localStorage.setItem('filePath', r);
    document.getElementById('file-upload-text').innerText = window.localStorage.getItem('filePath');
    document.getElementById('run-button').disabled = false;
}

function prepare() {
    window.localStorage.setItem('durationCol', document.getElementById('durationCol').value);
    window.localStorage.setItem('eventCol', document.getElementById('eventCol').value);
    window.localStorage.setItem('condCol', document.getElementById('condCol').value);
    window.localStorage.setItem('separator', document.getElementById('separator').value);
    window.location = "run.html";
}