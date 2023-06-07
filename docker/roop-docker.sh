#!/usr/bin/env bash

# wrapper shell script for roop in a docker image
# eg.,
# roop-docker.sh -r nvidia -f ~/tmp/face.jpg -t ~/tmp/target.mp4 -o ~/tmp/outdocker.mp4 -- --gpu-vendor=nvidia --gpu-threads=2 --keep-frames

set -o pipefail
set -u

ENCODING="utf-8"

[[ "$(uname -s)" = 'Darwin' ]] && REALPATH=grealpath || REALPATH=realpath
[[ "$(uname -s)" = 'Darwin' ]] && DIRNAME=gdirname || DIRNAME=dirname
if ! (type "$REALPATH" && type "$DIRNAME" && type $CONTAINER_ENGINE) > /dev/null; then
  echo "$(basename "${BASH_SOURCE[0]}") requires $CONTAINER_ENGINE, $REALPATH and $DIRNAME" >&2
  exit 1
fi
SCRIPT_PATH="$($DIRNAME $($REALPATH -e "${BASH_SOURCE[0]}"))"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

VERBOSE_FLAG=
FACE=
TARGET=
OUTPUT=
ROOP_IMAGE="${ROOP_IMAGE:-roop:latest}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-docker}"
RUNTIME_ARGS=()
while getopts 'vf:t:o:i:e:r:' OPTION; do
  case "$OPTION" in
    v)
      set -x
      VERBOSE_FLAG="-v"
      ;;

    f)
      FACE="$OPTARG"
      ;;

    t)
      TARGET="$OPTARG"
      ;;

    o)
      OUTPUT="$OPTARG"
      ;;

    i)
      ROOP_IMAGE="$OPTARG"
      ;;

    e)
      CONTAINER_ENGINE="$OPTARG"
      ;;

    r)
      RUNTIME_ARGS+=( --runtime )
      RUNTIME_ARGS+=( "$OPTARG" )
      ;;

    ?)
      echo "script usage: $(basename $0) [-f face] [-t target] [-o output] (-i <roop image>) (-e <container engine>) (-r <container runtime>)" >&2
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"
ROOP_RUN_ARGS=("$@")

PUID=$([[ "${CONTAINER_ENGINE}" == "podman" ]] && echo 0 || id -u)
PGID=$([[ "${CONTAINER_ENGINE}" == "podman" ]] && echo 0 || id -g)

TEMP_DIR=$(mktemp -d -p "$($DIRNAME "${OUTPUT}")" -t roop.XXXXXXXXXX)
FACE_BASENAME="$(basename "${FACE}")"
TARGET_BASENAME="$(basename "${TARGET}")"
OUT_BASENAME="$(basename "${OUTPUT}")"

containsElement () {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

function finish {
  if containsElement "--keep-frames" "${ROOP_RUN_ARGS[@]}"; then
    rm $VERBOSE_FLAG -f "${TEMP_DIR}/${FACE_BASENAME}" "${TEMP_DIR}/${TARGET_BASENAME}" "${TEMP_DIR}/${OUT_BASENAME}"
    mv $VERBOSE_FLAG "${TEMP_DIR}"/* "${TEMP_DIR}"/../
    rmdir "${TEMP_DIR}"
  else
    rm $VERBOSE_FLAG -rf "${TEMP_DIR}"
  fi
}
trap finish EXIT

cp $VERBOSE_FLAG "${FACE}" "${TEMP_DIR}/"
cp $VERBOSE_FLAG "${TARGET}" "${TEMP_DIR}/"

"${CONTAINER_ENGINE}" run --rm -t \
  "${RUNTIME_ARGS[@]}" \
  -e PUID=$PUID \
  -e PGID=$PGID \
  -v "${TEMP_DIR}:/data:rw" \
  -w "/data" \
  "${ROOP_IMAGE}" \
  python3 /roop/run.py \
  -f "/data/${FACE_BASENAME}" \
  -t "/data/${TARGET_BASENAME}" \
  -o "/data/${OUT_BASENAME}" \
  "${ROOP_RUN_ARGS[@]}"

cp $VERBOSE_FLAG "${TEMP_DIR}/${OUT_BASENAME}" "${OUTPUT}"

echo "${OUTPUT}"
