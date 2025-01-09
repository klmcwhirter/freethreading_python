#!/usr/bin/env bash

function echo_cmd
{
    local no_v=$1
    [ "${no_v}" == "--no-v" ] && shift

    echo "==> $@"

    if [ "${no_v}" == "--no-v" ]
    then
        $@ >/dev/null  # let stderr display
    else
        $@
    fi
}

PYTHON_VER=3.14

echo $0: $(pwd)
echo $0 PYTHON_VER=${PYTHON_VER}

###
### UV
###

echo $0: starting uv install $(date)

# echo_cmd export UV_HOME=~/.local/share/uv
echo_cmd export UV_LINK_MODE=symlink
echo_cmd export UV_PYTHON=/usr/bin/python${PYTHON_VER}

echo 'curl -LsSf https://astral.sh/uv/install.sh | sh'
curl -LsSf https://astral.sh/uv/install.sh | sh

echo $0: done uv install $(date)


###
### UV CREATE
###

echo $0: starting uv create $(date)

echo_cmd uv venv

echo_cmd ln -s /usr/bin/python3.14 .venv/bin/python3.14.0a3
echo_cmd ln -s /usr/bin/python3.14t .venv/bin/python3.14.0a3t

echo $0: done uv create $(date)
