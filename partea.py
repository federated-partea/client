import json
import logging
import os
import sys
import traceback
from time import sleep
from tkinter import Tk, TclError
from tkinter.filedialog import askopenfilename

import eel
import requests
import urllib3.exceptions
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from pet.encryption import encrypt_outgoing, Encryption
from pet.smpc_agg import aggregate_smpc
from pet.smpc_local import make_secure
from serialize import deserialize, serialize
from survival_analysis import univariate, coxph
import pandas as pd

import numpy as np

from survival_analysis.coxph import CoxPHModel

NAME = "Partea Client"

retry_strategy = Retry(
    total=10,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'}

logger = logging.getLogger(__name__)


@eel.expose
def print_js(message):
    print(f'Print: {message}')


@eel.expose
def finish_program():
    sys.exit(0)


@eel.expose
def get_path_to_file():
    root = Tk()
    root.withdraw()

    try:
        root.tk.call('tk_getOpenFile', '-foobarbaz')
        # now set the magic variables accordingly
    except TclError:
        pass

    filename = askopenfilename(initialdir='~', title='Select file',
                               filetypes=(('CSV files', '*.csv'), ('TSV files', '*.tsv'), ('SASS files', '*.sass'),
                                          ('all files', '*.*')))
    return filename


@eel.expose
def join_project(username: str, password: str, token: str, server_url: str):
    request_body = {'username': username, 'password': password, 'token': token}
    try:
        response = http.post(f'{server_url}/project/', json=request_body)
        if response.status_code != 200:
            error_message = response.content.decode('utf-8')

            return ["Join Error:", error_message]

        response_data = json.loads(response.content)
        method = response_data['project']['method']
        min_time = response_data['project']['from_time']
        max_time = response_data['project']['to_time']
        step_size = response_data['project']['step_size']
        smpc = response_data['project']['smpc']
        privacy_level = response_data['project']['privacy_level']
        conditions = response_data['project']['conditions']
        timeline = response_data['project']['timeline']
        max_iters = response_data['project']['max_iters']
        name = response_data['project']['name']

        client_id = response_data['client_id']
        token = response_data['token']

        print(f'Perform {method} computation')
        return [response.status_code,
                [method, token, client_id, min_time, max_time, step_size, max_iters, smpc, privacy_level, conditions,
                 timeline, name]]

    except ConnectionError as e:
        print("Connection Error", "Connection to server could not be established.", e)
        traceback.print_exc()
        exit()


def get_global_data(token: str, client_step: int, server_url: str, client_id: int = 0):
    while True:
        response = http.get(url=f'{server_url}/task/?token={token}&mode=state', headers=headers)
        data_from_server = json.loads(response.content)
        server_state = data_from_server['state']
        server_step = int(data_from_server['step'])
        project_state = data_from_server['internal_state']

        if project_state == 'finished':
            return {}, server_step, project_state

        if (server_state == 'waiting') and server_step > client_step:
            if project_state == "init":
                return {}, server_step, "init"
            response = http.get(url=f'{server_url}/task/?token={token}&mode=data&client={str(client_id)}',
                                headers=headers)
            if response.status_code == 200:
                data = deserialize(response.content)
                client_step = server_step
                sleep(1)
                if data is not None:
                    if isinstance(data, dict):
                        if "error" in data.keys():
                            raise RuntimeError(f'Error during computation: {data["error"]}')
                    return data, client_step, project_state
            elif response.status_code == 500:
                print(response.content)
                print(response.status_code)

        else:
            sleep(1)
            continue


def send_local_data(data, token: str, server_url: str):
    serialized_local_data = serialize(data)
    response = http.post(url=f'{server_url}/task/?token={token}', data=serialized_local_data, headers=headers)
    if response.status_code == 200:
        sleep(1)
        return
    else:
        print("Could not send data to server. Try again.", response.status_code, response.content)


def wait_until_project_started(token: str, server_url: str):
    while True:
        response = http.get(f'{server_url}/task/?token={token}&mode=state', headers=headers)
        decoded_resp = json.loads(response.content)
        if decoded_resp['state'] == 'waiting':
            sleep(1)
            return decoded_resp['number_of_participants']
        sleep(3)


@eel.expose
def univariate_analysis(data: pd.DataFrame, category_col: str, token: str, server_url: str):
    eel.setProgress(50)
    eel.info("Calculating local statistics...")
    state = None
    client_step = 0
    while state != "finished":
        global_data, client_step, state = get_global_data(token, client_step, server_url)
        print("State:", state)
        if state != "finished":
            local_results = univariate.compute(category_col, data)
            send_local_data({"local_results": local_results, "sample_number": data.shape[0]}, token, server_url)
            eel.setProgress(75)
            eel.info("Aggregating statistics globally ...")
        else:
            eel.setProgress(100)
            eel.finish()
            return


@eel.expose
def smpc_univariate_analysis(local_data: pd.DataFrame, category_col: str, token: str, server_url: str, min_time: float,
                             max_time: float, step_size: float, client_id: int):
    eel.setProgress(10)
    eel.info("Initializing ...")
    state = None
    client_step = 0
    enc = Encryption()
    while state != "finished":
        data, client_step, state = get_global_data(token, client_step, server_url, client_id)
        print("State:", state)
        if state == "init":
            eel.setProgress(20)
            eel.info("Sharing encryption keys ...")
            send_local_data(enc.public_key, token, server_url)
        elif state == "smpc_agg":
            eel.setProgress(50)
            eel.info("Locally aggregate secrets ...")
            decrypted_data = enc.decrypt_incoming(data)
            local_smpc_aggregate = aggregate_smpc(decrypted_data)
            eel.setProgress(75)
            eel.info("Globally aggregate secrets ...")
            send_local_data(local_smpc_aggregate, token, server_url)
        elif state == "local_calc":
            eel.setProgress(30)
            eel.info("Calculate local statistics")
            enc.public_keys = data
            participants = list(enc.public_keys.keys())

            local_results = univariate.compute(category_col, local_data, float(min_time), float(max_time),
                                               float(step_size))
            smpc_data = make_secure(params={"local_results": local_results, "sample_number": local_data.shape[0]},
                                    n=len(participants), exp=0)
            encrypted_data = encrypt_outgoing(data=smpc_data, public_keys=enc.public_keys)
            eel.setProgress(40)
            eel.info("Server distributes secrets ...")
            send_local_data(encrypted_data, token, server_url)
        elif state == 'finished':
            eel.setProgress(100)
            eel.finish()


@eel.expose
def regression_analysis(data: pd.DataFrame, token: str, server_url: str, cph: CoxPHModel):
    state = None
    client_step = 0
    progress = 0
    eel.setProgress(10)
    eel.info("Initializing ...")
    while state != "finished":
        global_data, client_step, state = get_global_data(token, client_step, server_url)
        print("State:", state)
        if state == "init":
            mean = cph.get_mean()
            send_local_data({"mean": mean, "n_samples": cph.n_samples}, token, server_url)
        elif state == "norm_std":
            eel.setProgress(20)
            eel.info("Normalization ...")
            cph.set_mean(global_data["norm_mean"])
            std = cph.get_std(cph.get_mean())
            send_local_data({"std": std, "n_samples": cph.n_samples}, token, server_url)
        elif state == "local_init":
            cph.set_std(global_data["norm_std"])
            cph.normalize_local_data()
            distinct_times, zlr, numb_d_set, n_samples = cph._local_initialization()
            send_local_data(
                {"distinct_times": distinct_times, "zlr": zlr, "numb_d_set": numb_d_set, "n_samples": n_samples}, token,
                server_url)
            eel.setProgress(30)
            progress = 30
        elif state == "iteration_update":
            eel.info("Update beta parameters ...")
            if "params" not in global_data.keys():
                print(f'UPDATE BETA - iteration {global_data["iteration"]}')
                eel.info(f'Iteration update {global_data["iteration"]}')
                if progress <= 90:
                    progress = progress + 5
                eel.setProgress(progress)
                i1, i2, i3 = cph._update_aggregated_statistics_(global_data["beta"])

                if np.nan in list(i1.values()) or np.nan in list(i1.values()) or np.nan in list(i1.values()):
                    raise RuntimeError("Convergence error. Could not compute the beta updates.")
                if np.inf in list(i1.values()) or np.inf in list(i1.values()) or np.inf in list(i1.values()):
                    raise RuntimeError("Convergence error. Could not compute the beta updates.")

                send_local_data({"is": [i1, i2, i3]}, token, server_url)
        elif state == "c-index":
            eel.info('Calculate c-index')
            eel.setProgress(80)
            cph.params_ = global_data["params"]
            c_index = cph.local_concordance_calculation()
            send_local_data({"c-index": c_index, "sample_number": data.shape[0]}, token, server_url)
        elif state == "finished":
            eel.setProgress(100)
            eel.finish()


@eel.expose
def smpc_regression_analysis(cph: CoxPHModel, token: str, server_url: str, min_time: float or None,
                             max_time: float or None, step_size: float or None, client_id: int):
    exp = 10
    state: str = None
    client_step = 0
    enc = Encryption()
    participants = None
    progress = 0
    eel.setProgress(10)
    eel.info("Initializing ...")
    while state != "finished":
        data, client_step, state = get_global_data(token, client_step, server_url, client_id)
        print("State:", state)
        if state == "init":
            cph.smpc = True
            send_local_data(enc.public_key, token, server_url)
        elif state.startswith("smpc_agg"):
            decrypted_data = enc.decrypt_incoming(data)
            local_smpc_aggregate = aggregate_smpc(decrypted_data)
            send_local_data(local_smpc_aggregate, token, server_url)
        elif state == "norm_mean":
            eel.setProgress(20)
            eel.info("Normalization ...")
            enc.public_keys = data
            participants = list(enc.public_keys.keys())
            n_samples = cph.X.shape[0]
            mean = cph.get_mean() * n_samples
            smpc_data = make_secure(params={"mean": mean.to_dict(), "n_samples": n_samples / 10 ** exp},
                                    n=len(participants),
                                    exp=exp)
            encrypted_data = encrypt_outgoing(data=smpc_data, public_keys=enc.public_keys)
            send_local_data(encrypted_data, token, server_url)
        elif state == "norm_std":
            cph.set_mean(data)
            std = cph.get_std(cph.get_mean())
            smpc_data = make_secure(params={"std": std.to_dict()}, n=len(participants), exp=exp)
            encrypted_data = encrypt_outgoing(data=smpc_data, public_keys=enc.public_keys)
            send_local_data(encrypted_data, token, server_url)
        elif state == "local_init":
            cph.set_std(data)
            cph.normalize_local_data()
            timeline = np.arange(min_time, max_time, step_size).tolist()
            timeline.reverse()
            cph.timeline = timeline
            _, zlr, numb_d_set, n_samples = cph._local_initialization()
            smpc_data = make_secure(params={"zlr": zlr.to_dict(), "numb_d_set": numb_d_set, "n_samples": n_samples},
                                    n=len(participants), exp=exp)
            encrypted_data = encrypt_outgoing(data=smpc_data, public_keys=enc.public_keys)
            send_local_data(encrypted_data, token, server_url)
            eel.setProgress(30)
            progress = 30
        elif state == "iteration_update":
            print(f'update beta - iteration {data[1]}')
            eel.info(f'Iteration update {data[1]}')
            if progress <= 90:
                progress = progress + 5
            eel.setProgress(progress)
            i1, i2, i3 = cph._update_aggregated_statistics_(beta=data[0])

            smpc_data = make_secure(params={"i1": i1, "i2": i2, "i3": i3}, n=len(participants), exp=exp)
            encrypted_data = encrypt_outgoing(data=smpc_data, public_keys=enc.public_keys)
            send_local_data(encrypted_data, token, server_url)
        elif state == "c_index":
            eel.info('Calculate c-index')
            eel.setProgress(80)
            cph.params_ = data
            n_samples = cph.X.shape[0]
            c_idx = cph.local_concordance_calculation() * 10 * n_samples
            smpc_data = make_secure(params={"c-index": c_idx}, n=len(participants), exp=0)
            encrypted_data = encrypt_outgoing(data=smpc_data, public_keys=enc.public_keys)
            send_local_data(encrypted_data, token, server_url)
        elif state == "finished":
            eel.setProgress(100)
            eel.finish()


@eel.expose
def preprocess_data(input_path: str, method: str, duration_col: str, event_col: str, cond_col: str, sep: str, check=True):
    data = None
    cph = None
    if not os.path.exists(input_path):
        print("Path does not exist")
        exit()
    try:
        print(input_path, method, duration_col, event_col, cond_col, sep, check)
        if method == "univariate":
            data = univariate.preprocess(duration_col, event_col, cond_col, input_path, sep)
        elif method == "cox":
            data = coxph.preprocess(input_path, sep, duration_col, event_col)
            cph = coxph.CoxPHModel(data, duration_col, event_col)
        if data.shape[0] < 5:
            print("You need at least 5 samples to participate in the computation.")
            exit()
        if data is None:
            print("No data was found")
            raise Exception("No data found.")
        if check:
            eel.run()
        else:
            return data, cph
    except Exception as e:
        print(f'File could not be processed: {e}')
        traceback.print_exc()
        eel.error(f'File could not be processed: {e}')


@eel.expose
def run_project(method: str, server_url: str, token: str, category_col: str, file_path: str, duration_col: str,
                event_col: str, sep: str, client_id: int, min_time: float or None, max_time: float or None,
                step_size: float or None,
                smpc: bool):
    data, cph = preprocess_data(file_path, method, duration_col, event_col, category_col, sep, False)
    if min_time is not None:
        min_time = float(min_time)
    if max_time is not None:
        max_time = float(max_time)
    if step_size is not None:
        step_size = float(step_size)
    try:
        n_participants = wait_until_project_started(token, server_url)
        if n_participants == 1:
            smpc = False
        if method == "univariate":
            if not smpc:
                univariate_analysis(data, category_col, token, server_url)
            else:
                smpc_univariate_analysis(data, category_col, token, server_url, min_time, max_time, step_size,
                                         client_id)
        elif method == "cox":
            if not smpc:
                regression_analysis(data, token, server_url, cph)
            else:
                smpc_regression_analysis(cph, token, server_url, min_time, max_time, step_size, client_id)
    except Exception as e:
        traceback.print_exc()
        eel.info("Computation failed. Please try again.")
        eel.setProgress(0)
        try:
            send_local_data(data={"state": "error", "error": e}, token=token, server_url=server_url)
        except urllib3.exceptions.MaxRetryError:
            return [False,
                    'The computation failed. The partea server was not reachable or a server computation '
                    'was not successful. '
                    'Check the webapp for more informations.',
                    True]

        return [False, 'The computation failed. The coordinator needs to create a new project.', True]


if __name__ == "__main__":
    eel.init('frontend')
    eel.start('main.html', port=0, chromeFlags=['--disable-http-cache'])
    eel._eel()
