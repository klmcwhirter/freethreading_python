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

echo $0: $(pwd)

###
### PYTHON
###

echo $0: starting python install $(date)

# install python dependencies
echo Installing cpython prereqs
echo_cmd --no-v sudo apt-get update -y
echo_cmd --no-v sudo apt-get install -y bzip2 libffi-dev liblzma-dev libncurses-dev libreadline-dev libsqlite3-dev tk-dev

PYTHON_MajMin=3.14
PYTHON_VER=${PYTHON_MajMin}.0a3

echo Installing cpython ${PYTHON_MajMin} and ${PYTHON_MajMin}t
echo_cmd asdf plugin add python
echo_cmd asdf install python ${PYTHON_VER}t
echo_cmd asdf install python ${PYTHON_VER}
echo_cmd asdf local python ${PYTHON_VER}

echo Symlink-ing cpython ${PYTHON_MajMin} and ${PYTHON_MajMin}t to ~/.local/bin
echo_cmd mkdir -p ~/.local/bin
echo_cmd ln -s ~/.asdf/installs/python/${PYTHON_VER}/bin/python${PYTHON_MajMin} ~/.local/bin/python${PYTHON_VER}
echo_cmd ln -s ~/.asdf/installs/python/${PYTHON_VER}t/bin/python${PYTHON_MajMin}t ~/.local/bin/python${PYTHON_VER}t

echo $0: done python install $(date)

###
### PDM
###

echo $0: starting pdm install $(date)

echo_cmd export PDM_HOME=~/.local/share/pdm

echo_cmd asdf plugin add pdm
echo_cmd --no-v asdf install pdm latest
echo_cmd asdf local pdm latest

echo_cmd rm -f pdm.toml
echo_cmd pdm config -l python.use_venv true
echo_cmd pdm config -l venv.in_project true

# work around assumption that auth with pypi should be setup
echo_cmd pdm config -g check_update false

echo $0: done pdm install $(date)


###
### PDM CREATE
###

echo $0: starting pdm create $(date)

echo_cmd pdm create

echo $0: done pdm create $(date)
