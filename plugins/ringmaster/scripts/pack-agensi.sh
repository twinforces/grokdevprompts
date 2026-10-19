#!/bin/sh
# Build a zip Agensi can list. SKILL.md is at the archive root.
# Hooks stay out: they are Grok plugin enforcement, and the marketplace
# scan is for a portable SKILL.md plus its references.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
out=${1:-"$root/../../dist/ringmaster-agensi.zip"}
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
cp "$root/skills/ringmaster/SKILL.md" "$stage/SKILL.md"
mkdir -p "$stage/references"
cp "$root/references/"*.md "$stage/references/"
mkdir -p "$(dirname "$out")"
rm -f "$out"
(
  cd "$stage"
  zip -qr "$out" SKILL.md references
)
echo "$out"
