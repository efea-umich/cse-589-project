To set up this project, first install `uv` by either installing it from [the official repo](https://github.com/astral-sh/uv) or through pip by running
```bash
$ pip install uv
```

Then, in the `network-sim` directory, run
```bash
$ uv sync
$ uv pip install -e .
```

Our tests were conducted with the tools under `network-sim/src/network_sim/test_runner`. Specifically, to replicate the experiments shown in the paper, edit the `run_client.py` and `run_server.py` client code to output the appropriate logs for the experiment being run by modifying the inputs to the function (which are automatically taken as command line arguments by the `fire` package).

Then, edit `full_tester.py` to conduct the relevant experiment by passing the needed parameters through the subprocess calls.

Then, in the `network-sim` directory, run
```bash
uv run src/network_sim/test_runner/full_tester.py <args>
```