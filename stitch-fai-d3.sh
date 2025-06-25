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

if ! [ -d "build/d3-g-topst-main/tmp/deploy/images/d3-g-topst-main" ]; then
	>&2 echo [-] No build output
	exit
fi

function show_help {
	cat << EOL
[!] Usage: ${0} [-S] [-s] [-f] [output_name]

Options:
  -S            enable subcore
  -s            save partition images
  -f            with FWDN package
  output_name   output name prefix (default: output)
EOL
}

WITH_SUBCORE=0
WITH_IMAGES=0
WITH_FWDN=0

OPTIND=1

while getopts "h?Ssf" opt; do
	case "$opt" in
		h|\?)
			show_help
			exit 0
			;;
		S)
			WITH_SUBCORE=1
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

OUTPUT="${1:-output_d3g}"

if [ -d "build-sub/tmp/deploy/images/tcc8050-sub" ] && \
	[ $WITH_SUBCORE -eq 0 ]; then
	while true; do
		read -p "[!] Will you use subcore? (yes/no) " yn
		case $yn in
			[Yy]* )
				WITH_SUBCORE=1
				break;;
			[Nn]* )
				WITH_SUBCORE=0
				break;;
			* )
				echo [-] Unknown command
				exit;;
		esac
	done
fi

TMPDIR=$(realpath $(mktemp -d ./.stitch_XXXXXXX))

function cleanup {
	rm -rf $TMPDIR
}

trap cleanup EXIT INT TERM

dd if=/dev/zero of=$TMPDIR/user-data.ext4 bs=1 count=0 seek=1M status=none
mkfs.ext4 -q -b 4096 $TMPDIR/user-data.ext4

if [ $WITH_SUBCORE -eq 1 ]; then
	PARTITION_LIST=partition.dual.list.d3
	dd if=/dev/zero of=$TMPDIR/home-directory.ext4 bs=1024 count=0 seek=512000 status=none
else
	PARTITION_LIST=partition.single.list.d3
	dd if=/dev/zero of=$TMPDIR/home-directory.ext4 bs=1024 count=0 seek=1758208 status=none
fi

mkfs.ext4 -q -b 4096 $TMPDIR/home-directory.ext4

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

./tools/fwdn_d3/mktcimg \
	--parttype gpt \
	--storage_size 17818182656 \
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

	cp -rf \
		tools/fwdn_d3/* \
		$TMPDIR

	if [ $WITH_SUBCORE -eq 0 ]; then
		MODE="single"
	else
		MODE="dual"
	fi

	sed -i "s,##MODE##,$MODE,g" $TMPDIR/fwdn.bat
	sed -i "s,##OUTPUT##,$OUTPUT,g" $TMPDIR/fwdn.bat

	sed -i "s,##MODE##,$MODE,g" $TMPDIR/fwdn.sh
	sed -i "s,##OUTPUT##,$OUTPUT,g" $TMPDIR/fwdn.sh

	rm -f "${OUTPUT}.fwdn.zip"
	cd $TMPDIR
	rm -f *.ext4
	zip -r ../"${OUTPUT}.fwdn.zip" *
fi
