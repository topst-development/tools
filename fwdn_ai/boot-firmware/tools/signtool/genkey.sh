#!/bin/sh

KEY_BASE=keys

HKEY_NAME=hsmkey
RKEY_NAME=rootkey
MKEY_NAME=masterkey
IKEY_NAME=imagekey

SIGNKEY_NAME=signkey.pem
ENCKEY_NAME=enckey.bin

function genkey() {
    keydir=$1
    enckeylength=$2

    mkdir ${keydir}
    if [ $? -eq 0 ]; then
        openssl ecparam -genkey -name prime256v1 -out ${keydir}/${SIGNKEY_NAME}
        if [ $? -eq 0 ]; then
            echo -e "[\033[33mGenerating\033[0m] ${keydir}/${SIGNKEY_NAME}"
        else
            echo -e "[\033[31mERROR\033[0m] ${keydir}/${SIGNKEY_NAME}"
        fi
        openssl rand ${enckeylength} > ${keydir}/${ENCKEY_NAME}
        if [ $? -eq 0 ]; then
            echo -e "[\033[33mGenerating\033[0m] ${keydir}/${ENCKEY_NAME}"
        else
            echo -e "[\033[31mERROR\033[0m] ${keydir}/${ENCKEY_NAME}"
        fi
    fi
}

function main() {
    keybase=$1
    mkdir ${keybase}
    if [ $? -eq 0 ]; then
        genkey ${keybase}/${HKEY_NAME} 32
        genkey ${keybase}/${RKEY_NAME} 16
        genkey ${keybase}/${MKEY_NAME} 16
        genkey ${keybase}/${IKEY_NAME} 16
    fi
}

main $(cd $(dirname $0);pwd)/${KEY_BASE}
