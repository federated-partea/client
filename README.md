# Partea - Privacy-AwaRe Time-to-Event Analysis

All repositories are available on GitHub under [https://github.com/federated-partea](https://github.com/federated-partea)

## 1. System requirements

- MacOS Monterey 12.2.1 and Ubuntu 20.04
- The software was tested on both OS

## 2. Installation Guide

1. [Download](https://exbio.wzw.tum.de/partea/how-to#participants) the client software.
   1. [macOS](https://exbio.wzw.tum.de/partea/assets/executables/partea_macos.zip)
   2. [ubuntu](https://exbio.wzw.tum.de/partea/assets/executables/partea_ubuntu.tar.gz)
2. **Unzip** the archive.
3. If you do not have Google Chrome installed already, please [Download](https://www.google.com/chrome/) and install it.
4. Run the executable file
    1. macOS: Double-click on partea.app to start the client. The first time, you might need to run it
       with `control + click`.
    2. Ubuntu: Run the executable in your terminal with `./partea`
5. The Partea Server and Partea Webapp are deployed at the servers of the Technical University Munich and do not need to
   be installed locally.

## 3. Demo

A [getting started tutorial](https://exbio.wzw.tum.de/partea/how-to) is available on the Partea website.

### A. Study coordinator initializes the project

1. [Sign up](https://exbio.wzw.tum.de/partea/account) for an account.
2. [Sign in] with the account, if not done automatically after sign up.
3. [Create](https://exbio.wzw.tum.de/partea/projects) a new project by clicking on the **Projects** tab, enter a project
   name and click **Create**.
4. Keep the default parameters to execute a non-parametric time-to-event analysis for survival function and cumulative
   hazard rate estimation. **Initialize** the project by clikcing the corresponding button.
5. Scroll down to the **Collaborators** section and press **Create token**. This is how you can invite participants to
   your study. This token can now be shared with a participant.

### B. Collaborator(s) join the project

1. Now, we assume that we were a collaborator of the study. After receiving the token, we start our **Partea client**
   executable and sign in using our account credentials and the corresponding token.
2. Now we describe our dataset, which is in this case:
    1. Duration Column: week
    2. Event Column: arrest
    3. Seperator: comma
3. After that, we choose the dataset from our directory. You can download the sample data
   archive [here](https://exbio.wzw.tum.de/partea/assets/sample_data.zip). For simplicity, we will run the analysis here
   with only one collaborator, so we choose the dataset `rossi_complete.csv`, after unzipping the sample data archive.
4. Click "Run" to start the analysis. Now you wait, until the study coordinator starts the study. The client application
   should indicate this with the Message: "Waiting for other participants and project start."

### C. Project coordinator runs the analysis

1. As in this example we are the study coordinator, we go the Partea Webapp again, click on **Projects** and select our
   project.
2. After scrolling to the **Collaborators** section, we see that our client is running, and we can start the analysis by
   clicking **Run Project**.
3. After around 5-10 seconds, the analysis with only one client should be finished. The client application can be closed
   now, and the results are visible on the Webapp.
4. You can see all results in the webapp and compare the Survival Curve and Table with the expected results we attached
   here.

## 4. Instructions for use

The Demo section basically explains already how to use Partea. 
1. In the case of multiple participants, the coordinator
simply creates more tokens and shares them with the corresponding participant. 
2. Each participant then executes the client software locally, and press run.
3. After each participant has run the local computation, the study coordinator can run the project.
