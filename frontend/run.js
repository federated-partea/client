window.onload = function () {
    runProject()
};

function info(message, color = 'black') {
    document.getElementById('info-label').innerHTML = message.fontcolor(color);
}

function setProgress(percentage, color = "blue") {
    document.getElementById('progress-bar').value = percentage;
}

function reset() {
    window.location = "project.html";
}

function finish() {
    window.location = "finish.html";
}

eel.expose(info);
eel.expose(setProgress);
eel.expose(finish)

async function runProject() {
    let serverUrl = window.localStorage.getItem('serverUrl');
    let filePath = window.localStorage.getItem('filePath')
    let durationCol = window.localStorage.getItem('durationCol')
    let eventCol = window.localStorage.getItem('eventCol')
    let separator = window.localStorage.getItem('separator')
    let condCol = window.localStorage.getItem('condCol')
    let method = window.localStorage.getItem('method')
    let token = window.localStorage.getItem('token')
    let clientId = window.localStorage.getItem('clientId')
    let minTime = window.localStorage.getItem('timelineMin')
    let maxTime = window.localStorage.getItem('timelineMax')
    let stepSize = window.localStorage.getItem('timelineSteps')
    let smpc = window.localStorage.getItem('smpc')
    smpc = smpc === 'true';
    let r = await eel.run_project(method, serverUrl, token, condCol, filePath, durationCol, eventCol, separator, clientId, minTime, maxTime, stepSize, smpc)

    const infoTextString = r[1]
    if (!r[0]) {
        document.getElementById('info-label').innerHTML = infoTextString.fontcolor("#FF6584");
        let loadButton = document.getElementById("load-button");
        loadButton.classList.add("is-hidden");
        if (!r[2]) {
            let resetButton = document.getElementById("reset-button");
            resetButton.classList.remove("is-hidden");
        } else {
            let endButton = document.getElementById("end-button");
            endButton.classList.remove("is-hidden");
            endButton.style.backgroundColor = "#FF6584"
        }

    } else {
        window.location = "finish.html";
    }
}

