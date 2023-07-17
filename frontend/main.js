async function joinProject() {
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;
    let projectToken = document.getElementById("projectToken").value;
    let infoText = document.getElementById("login_info")
    window.localStorage.setItem('serverUrl', "https://apps.cosy.bio/api-partea/client")

    let response = await eel.join_project(username, password, projectToken, window.localStorage.getItem('serverUrl'))();

    if (response[0] !== 200) {
        let infoTextString = "Login failed. " + response[1];
        infoText.innerHTML = infoTextString.fontcolor("#FF6584");
    } else {
        window.localStorage.setItem('method', response[1][0]);
        window.localStorage.setItem('token', response[1][1]);
        window.localStorage.setItem('clientId', response[1][2]);
        window.localStorage.setItem('timelineMin', response[1][3]);
        window.localStorage.setItem('timelineMax', response[1][4]);
        window.localStorage.setItem('timelineSteps', response[1][5]);
        window.localStorage.setItem('maxIters', response[1][6]);
        window.localStorage.setItem('smpc', response[1][7]);
        let diffpriv;
        if (response[1][8] === 1) {
            diffpriv = "High";
        } else if (response[1][8] === 2) {
            diffpriv = "Medium";
        } else if (response[1][8] === 3) {
            diffpriv = "Low";
        } else if (response[1][8] === 0) {
            diffpriv = "None";
        } else {
            diffpriv = "eps=" + response[1][8].toString();
        }
        window.localStorage.setItem('diffpriv', diffpriv);
        window.localStorage.setItem('groups', response[1][9]);
        window.localStorage.setItem('timeline', response[1][10]);
        window.localStorage.setItem('name', response[1][11]);

        window.location = "project.html"
    }
}

