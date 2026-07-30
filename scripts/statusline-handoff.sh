#!/usr/bin/env bash
# Demo statusline: machine identity first, never truncated away.

input=$(cat)

HOST_COLOR="\033[1;38;2;132;211;255m"
REMOTE_COLOR="\033[1;38;2;255;179;71m"
MODEL_COLOR="\033[38;2;186;133;232m"
DIR_COLOR="\033[38;2;255;204;102m"
SESSION_COLOR="\033[38;2;169;169;169m"
SEP_COLOR="\033[38;2;128;128;128m"
RESET="\033[0m"
SEP=" \033[38;2;128;128;128m◦\033[0m "

HOSTNAME="${FACTORY_STATUSLINE_HOST:-$(hostname -s)}"
MODEL="droid"
CWD=""
SESSION_ID=""
REMOTE=""

if command -v jq >/dev/null 2>&1 && [[ -n "$input" ]] && jq -e . >/dev/null 2>&1 <<< "$input"; then
    mapfile -t f < <(
        jq -r '[
            .computer.name // "",
            (.computer.is_remote // "" | tostring),
            .model.display_name // .model.id // "droid",
            .cwd // "",
            .session_id // ""
        ][]' <<< "$input" 2>/dev/null
    )
    [[ -n "${f[0]:-}" && "${f[0]}" != "null" ]] && HOSTNAME="${f[0]}"
    [[ "${f[1]:-}" == "true" ]] && REMOTE=1
    [[ -n "${f[2]:-}" && "${f[2]}" != "null" ]] && MODEL="${f[2],,}"
    MODEL="${MODEL// /-}"
    [[ -n "${f[3]:-}" && "${f[3]}" != "null" ]] && CWD="${f[3]}"
    [[ -n "${f[4]:-}" && "${f[4]}" != "null" ]] && SESSION_ID="${f[4]:0:8}"
fi

if [[ -n "$REMOTE" ]]; then
    printf "📡 ${REMOTE_COLOR}%s${RESET}" "$HOSTNAME"
else
    printf "💻 ${HOST_COLOR}%s${RESET}" "$HOSTNAME"
fi

printf "%b🤖 ${MODEL_COLOR}%s${RESET}" "$SEP" "$MODEL"

if [[ -n "$CWD" ]]; then
    printf "%b📁 ${DIR_COLOR}%s${RESET}" "$SEP" "$(basename "$CWD")"
fi

if [[ -n "$SESSION_ID" ]]; then
    printf "%b${SESSION_COLOR}%s${RESET}" "$SEP" "$SESSION_ID"
fi

echo
