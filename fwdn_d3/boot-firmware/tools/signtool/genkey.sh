#!/bin/sh

KEY_BASE=keys

HKEY_NAME=hsmkey
RKEY_NAME=rootkey
MKEY_NAME=masterkey
IKEY_NAME=imagekey

#Root Public Key revocation parameters
RPUKEYS_NAME=rpubkey
NUM_OF_RPUKEYS=8
DEFAULT_RPUBKEY=0
SIGNKEY_NAME=signkey.pem
ENCKEY_NAME=enckey.bin

function genkey() {
    keydir=$1
    enckeylength=$2

    mkdir ${keydir}
    if [ $? -eq 0 ]; then
        if [ "${keydir##*/}" != "rootkey" ]; then
        openssl ecparam -genkey -name prime256v1 -out ${keydir}/${SIGNKEY_NAME}
        if [ $? -eq 0 ]; then
            echo -e "[\033[33mGenerating\033[0m] ${keydir}/${SIGNKEY_NAME}"
        else
            echo -e "[\033[31mERROR\033[0m] ${keydir}/${SIGNKEY_NAME}"
            fi
        fi
        if [ "$3" != "rpubkeys" ]; then
        openssl rand ${enckeylength} > ${keydir}/${ENCKEY_NAME}
        if [ $? -eq 0 ]; then
            echo -e "[\033[33mGenerating\033[0m] ${keydir}/${ENCKEY_NAME}"
        else
            echo -e "[\033[31mERROR\033[0m] ${keydir}/${ENCKEY_NAME}"
            fi
        fi
    fi
}

function main() {
    keybase=$1
    mkdir ${keybase}
    num_rpubkeys=$(expr $NUM_OF_RPUKEYS - 1)
    if [ $? -eq 0 ]; then
        genkey ${keybase}/${HKEY_NAME} 32
        genkey ${keybase}/${RKEY_NAME} 16
        while [ ${num_rpubkeys} -ge 0 ]
        do
            genkey ${keybase}/${RKEY_NAME}/${num_rpubkeys}_${RPUKEYS_NAME} 16 rpubkeys
            num_rpubkeys=$(expr $num_rpubkeys - 1)
        done
        genkey ${keybase}/${MKEY_NAME} 16
        genkey ${keybase}/${IKEY_NAME} 16
    fi
    if [ -e ${keybase}/${RKEY_NAME}/${DEFAULT_RPUBKEY}_${RPUKEYS_NAME}/${SIGNKEY_NAME} ]; then
        cp ${keybase}/${RKEY_NAME}/${DEFAULT_RPUBKEY}_${RPUKEYS_NAME}/${SIGNKEY_NAME} ${keybase}/${RKEY_NAME}
    else
        echo -e -e "[\033[31mERROR\033[0m] File doesn't exist (${keybase}/${RKEY_NAME}/${DEFAULT_RPUBKEY}_${RPUKEYS_NAME}/${SIGNKEY_NAME})"
    fi
}

main $(cd $(dirname $0);pwd)/${KEY_BASE}
