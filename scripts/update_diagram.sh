#!/bin/bash

# This script just prevents flickering
# when viewing a .png with my image viewer

for INFILE; do
    echo "${INFILE} -> ${INFILE}.svg";
    cat $INFILE | svgbob \
        --font-family="Courier New" \
        --output $INFILE.tmp.svg \
        --scale 4;

    OLD_MD5=$(cat ${INFILE}.svg | md5sum);
    NEW_MD5=$(cat ${INFILE}.tmp.svg | md5sum);

    if [[ "${OLD_MD5}" == "${NEW_MD5}" ]]; then
        rm "${INFILE}.tmp.svg";
        echo "noop";
    else
        mv "${INFILE}.tmp.svg" "${INFILE}.svg";
        echo "updated";
    fi
done

