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
### UV
###

echo $0: starting uv install $(date)

# echo_cmd export UV_HOME=~/.local/share/uv
echo_cmd export UV_LINK_MODE=symlink
echo_cmd export UV_PYTHON=/home/vscode/.local/bin/python${PYTHON_VER}

echo_cmd asdf plugin add uv
echo_cmd --no-v asdf install uv latest
echo_cmd asdf local uv latest

echo $0: done uv install $(date)


###
### UV CREATE
###

echo $0: starting uv create $(date)

echo_cmd uv venv
echo_cmd rm -fr .etc
echo_cmd mkdir .etc
echo '#!/usr/bin/env bash' >.etc/ln_python.sh
echo -e "for p in python${PYTHON_VER} python${PYTHON_VER}t;do ln -s ${HOME_BIN}/"'$p'" .venv/bin;done" >>.etc/ln_python.sh
echo_cmd chmod +x .etc/ln_python.sh
echo_cmd ./.etc/ln_python.sh

echo $0: done uv create $(date)
