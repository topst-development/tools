#!/bin/bash

set -e

if [ "$EUID" -eq 0 ]; then
	>&2 echo [-] Running this script with root privileges is not recommended
	exit
fi

if [ "$0" != "$BASH_SOURCE" ]; then
	>&2 echo [-] Do not sourcing the script
	return
fi

while [[ $PWD != '/' && ! -d $PWD/.repo ]]; do cd ..; done
if [[ $PWD == '/' ]]; then
	>&2 echo [-] Please ensure you are running this script within the Yocto SDK directory
	exit
fi

if ! [ -d "build/ai-g-topst/tmp/deploy/images/ai-g-topst" ]; then
	>&2 echo [-] No build output
	exit
fi

function show_help {
	cat << EOL
[!] Usage: ${0} [-s] [-f] [output_name]

Options:
  -s            save partition images
  -f            with FWDN package
  output_name   output name prefix (default: output)
EOL
}

WITH_IMAGES=0
WITH_FWDN=0

OPTIND=1

while getopts "h?sf" opt; do
	case "$opt" in
		h|\?)
			show_help
			exit 0
			;;
		s)
			WITH_IMAGES=1
			;;
		f)
			WITH_FWDN=1
			;;
	esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

OUTPUT="${1:-output_aig}"

TMPDIR=$(realpath $(mktemp -d ./.stitch_XXXXXXX))

function cleanup {
	rm -rf $TMPDIR
}

trap cleanup EXIT INT TERM

PARTITION_LIST=partition.list.ai

BINS=$(awk -F@ '{print $2}' tools/${PARTITION_LIST} | grep '^build')
for BIN in ${BINS[@]}
do
	if ! [ -f $BIN ]; then
		>&2 echo [-] Missing file: $BIN
		exit
	fi
done

cp tools/$PARTITION_LIST $TMPDIR/$PARTITION_LIST
sed -i "s,##TEMPDIR##,$TMPDIR,g" $TMPDIR/$PARTITION_LIST

./tools/fwdn_ai/mktcimg \
	--parttype gpt \
	--storage_size 6368709120 \
	--fplist $TMPDIR/$PARTITION_LIST \
	--outfile "$TMPDIR/${OUTPUT}.fai" \
	--gptfile "$TMPDIR/${OUTPUT}.gpt"
mv "$TMPDIR/${OUTPUT}.fai" .

if [ $WITH_IMAGES -eq 1 ]; then
	echo [+] Store output bins
	zip -j1 "${OUTPUT}.bins.zip" "$TMPDIR/${OUTPUT}.gpt"* $BINS
fi

if [ $WITH_FWDN -eq 1 ]; then
	echo [+] Packaging FWDN binaries
	mv "${OUTPUT}.fai" $TMPDIR
	rm $TMPDIR/$PARTITION_LIST

	cp -r \
		tools/fwdn_ai/* \
		$TMPDIR

	sed -i "s,##MODE##,$MODE,g" $TMPDIR/fwdn_ai.bat
	sed -i "s,##OUTPUT##,$OUTPUT,g" $TMPDIR/fwdn_ai.bat

	sed -i "s,##MODE##,$MODE,g" $TMPDIR/fwdn_ai.sh
	sed -i "s,##OUTPUT##,$OUTPUT,g" $TMPDIR/fwdn_ai.sh

	rm -f "${OUTPUT}.fwdn.zip"
	cd $TMPDIR
	rm -f *.ext4
	zip -r ../"${OUTPUT}.fwdn.zip" \
		"${OUTPUT}.fai" \
		* \
		boot-firmware/*
fi
