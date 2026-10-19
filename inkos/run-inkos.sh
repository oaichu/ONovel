#!/usr/bin/env bash
# run-inkos.sh <inkos args...>: run inkos 1.8.0 on MiMo v2.6 Flash (api.b.ai). Key comes from env BAI_API_KEY (~/.profile).
# REWRITTEN 2026-10-15 after /CODE loss. Keep the export lines at column 0: other scripts `eval "$(grep '^export ' run-inkos.sh)"`.
# Audit A02 (2026-10-19): the export lines must never abort the caller when BAI_API_KEY is unset (stub/free/offline modes eval them);
# the key is required only here, right before inkos (the MiMo provider) is actually executed. Honors the runs/mimo-off kill switch.
source ~/.profile >/dev/null 2>&1
export INKOS_LLM_PROVIDER=openai
export INKOS_LLM_BASE_URL=https://api.b.ai/v1
export INKOS_LLM_MODEL=mimo-v2.6-flash
export INKOS_LLM_API_FORMAT=chat
export INKOS_LLM_API_KEY="${BAI_API_KEY:-}"
export NODE_NO_WARNINGS=1
[ $# -eq 0 ] && exit 0
F=${MIMO_OFF_FLAG:-/CODE/inkos/runs/mimo-off}; [ -f "$F" ] && { echo "run-inkos.sh: MiMo is OFF (flag $F); inkos not started" >&2; exit 4; }
[ -n "$INKOS_LLM_API_KEY" ] || { echo "run-inkos.sh: BAI_API_KEY not set (needed for the MiMo provider)" >&2; exit 2; }
exec inkos "$@"
