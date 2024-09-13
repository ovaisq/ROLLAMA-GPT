#!/usr/bin/env bash
# run inside docker container ©2024, Ovais Quraishi

# create directory if it doesn't exist
create_directory() {
    local DIR=$1
    if [ ! -d "$DIR" ]; then
        echo "Creating directory: ${DIR}"
        mkdir -p "${DIR}"
    else
        echo "Directory ${DIR} already exists."
    fi
}

# check and create group if it doesn't exist
check_and_create_group() {
    local GROUP=$1
    if ! grep -q "^${GROUP}:" /etc/group; then
        echo "Creating group: ${GROUP}"
        addgroup "${GROUP}"
    else
        echo "Group ${GROUP} already exists."
    fi
}

# check and create user if it doesn't exist
check_and_create_user() {
    local USER=$1
    local GROUP=$2
    if ! id -u "$USER" > /dev/null 2>&1; then
        echo "Creating user: ${USER}"
        adduser --system --no-create-home --ingroup "${GROUP}" "${USER}"
    else
        echo "User ${USER} already exists."
    fi
}

# load config file
load_config_file() {
    local CONFIG_FILE=$1
    if [[ -f ${CONFIG_FILE} ]]; then
        source ${CONFIG_FILE}
    else
        echo "Unable to find ${CONFIG_FILE}. Expecting ENV vars to be set externally" >&2
        exit -1
    fi
}

# load build info
APP_DIR="/app/"
BUILD_INFO=FE_BUILD_INFO.TXT
load_config_file "${BUILD_INFO}"

echo "Install Pkg"
# user and group name is same as service name
GROUP="rollama"
USER="rollama"

check_and_create_group "${GROUP}"
check_and_create_user "${USER}" "${GROUP}"

cd ${APP_DIR}
echo "tar xfz ./${PACKAGE} 2> /dev/null"
tar xfz ./${PACKAGE} 2> /dev/null

echo "Setting up Service"
pip3 install -r ${APP_DIR}/requirements.txt --quiet --root-user-action=ignore
