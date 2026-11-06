#!/bin/sh
# Builds "Print from iPhone & iPad.app" at $1. Extra arguments go to swiftc.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; APP=$1; shift
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
swiftc -O -parse-as-library -target arm64-apple-macos12 "$@" "$HERE/airprint-app/main.swift" -o "$APP/Contents/MacOS/SharePrinters"
cp "$HERE/airprint-app/Info.plist" "$APP/Contents/"
cp "$HERE/airprint-app/AppIcon.icns" "$APP/Contents/Resources/"
