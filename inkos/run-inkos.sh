#!/usr/bin/env bash
# run-inkos.sh <inkos args...>: run inkos 1.8.0 on MiMo v2.6 Flash (api.b.ai). Key comes from env BAI_API_KEY (~/.profile).
# REWRITTEN 2026-10-15 after /CODE loss. Keep the export lines at column 0: other scripts `eval "$(grep '^export ' run-inkos.sh)"`.
source ~/.profile >/dev/null 2>&1
export INKOS_LLM_PROVIDER=openai
export INKOS_LLM_BASE_URL=https://api.b.ai/v1
export INKOS_LLM_MODEL=mimo-v2.6-flash
export INKOS_LLM_API_FORMAT=chat
export INKOS_LLM_API_KEY="${BAI_API_KEY:?BAI_API_KEY not set}"
export NODE_NO_WARNINGS=1
[ $# -eq 0 ] && exit 0
exec inkos "$@"
