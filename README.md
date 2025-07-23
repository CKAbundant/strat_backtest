# Back Testing
Python library for backtesting trading strategies including deep learning model.

# Setup

## Step 1: Install UV

Use url to download the script and execute it with sh for linux system:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Please refer to the [official UV website](https://docs.astral.sh/uv/getting-started/installation/) for details to install for Windows system.

## Step 2: Install dependencies

Backtesting uses ta-lib python library to generate the technical analysis (ta) indicators. Before we can install ta-lib c library, we need to install the required dependencies package.

```bash
sudo apt update && sudo apt install build-essentials python3-dev
```

## Step 3: Install ta-lib library

Download correct Linux debian packages from [ta-lib official website](https://ta-lib.org/install/#linux) e.g. [ta-lib_0.6.4_amd64.deb](https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib_0.6.4_amd64.deb)

Install or update

```bash
sudo dpkg -i ta-lib_0.6.4_amd64.deb
```

Please refer to the [official UV website](https://ta-lib.org/install/) for details to install for Windows system.

## Step 4: Upgrade ta-lib package to the latest version

ta-lib python version present in `uv.lock` file may not be the latest. This will create issues when you perform `uv sync`. As such, we need to upgrade ta-lib package to the latest version i.e. similar to the version you have installed in Step 3.

```bash
uv lock --upgrade-package ta-lib
uv sync
```





