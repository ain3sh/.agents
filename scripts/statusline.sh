#!/usr/bin/env bash
# ~/.agents/scripts/statusline.sh

input=$(cat)

TIME_COLOR="\033[38;2;135;206;250m"
HOST_COLOR="\033[38;2;106;159;181m"
MODEL_COLOR="\033[38;2;186;133;232m"
CONTEXT_COLOR="\033[38;2;255;204;102m"
DIR_COLOR="\033[38;2;255;179;71m"
PARENTS_COLOR="\033[38;2;255;205;128m"
GIT_COLOR="\033[38;2;152;195;121m"
GIT_DIRTY_COLOR="\033[38;2;204;136;255m"
PR_COLOR="\033[38;2;132;211;255m"
PY_COLOR="\033[38;2;97;214;214m"
SESSION_COLOR="\033[38;2;169;169;169m"
SEPARATOR_COLOR="\033[38;2;128;128;128m"
ACCENT_COLOR="\033[38;2;180;180;180m"
RESET="\033[0m"
SEP_DOT="◦"

format_tokens() {
    local tokens=$1
    if [[ $tokens -ge 1000000 ]]; then
        printf "%d.%02dM" "$((tokens / 1000000))" "$(((tokens % 1000000) / 10000))"
    elif [[ $tokens -ge 1000 ]]; then
        printf "%d.%02dk" "$((tokens / 1000))" "$(((tokens % 1000) / 10))"
    else
        printf "%d" "$tokens"
    fi
}

git_in_cwd() {
    GIT_OPTIONAL_LOCKS=0 git -C "$CWD" "$@" 2>/dev/null
}

get_pr_number() {
    local repo_root=$1
    local branch=$2
    local cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/factory-statusline"
    local cache_key_source="${repo_root}|${branch}"
    local cache_key
    local cache_file
    local now
    local ts
    local val

    if ! command -v gh >/dev/null 2>&1; then
        return 0
    fi

    mkdir -p "$cache_dir" 2>/dev/null || return 0

    if command -v sha1sum >/dev/null 2>&1; then
        cache_key=$(printf '%s' "$cache_key_source" | sha1sum | awk '{print $1}')
    else
        cache_key=$(printf '%s' "$cache_key_source" | tr '/:| ' '_')
    fi

    cache_file="${cache_dir}/pr-${cache_key}"
    now=$(date +%s)

    if [[ -f "$cache_file" ]]; then
        read -r ts val < "$cache_file"
        if [[ "$ts" =~ ^[0-9]+$ ]] && (( now - ts < 180 )); then
            [[ "$val" == "-" ]] && return 0
            [[ -n "$val" ]] && printf '%s' "$val"
            return 0
        fi
    fi

    if ! val=$(cd "$CWD" 2>/dev/null && env GH_PAGER=cat gh pr view --json number --jq '.number' 2>/dev/null); then
        val=""
    fi
    [[ -z "$val" ]] && val="-"
    printf '%s %s\n' "$now" "$val" > "$cache_file" 2>/dev/null || true

    [[ "$val" == "-" ]] && return 0
    printf '%s' "$val"
}

TIME=$(TZ=America/Los_Angeles date '+%H:%M')
HOSTNAME=$(hostname -s)

MODEL="droid"
CLI_VERSION=""
SESSION_ID=""
CWD=""
REASONING_EFFORT=""
CONTEXT_DISPLAY=""
CONTEXT_TOKENS=""
CONTEXT_PERCENT=""

if command -v jq >/dev/null 2>&1 && [[ -n "$input" ]] && jq -e . >/dev/null 2>&1 <<< "$input"; then
    mapfile -t json_fields < <(
        jq -r '[
            .model.display_name // .model.id // "droid",
            .version // "",
            .session_id // "",
            .cwd // "",
            .model.reasoning_effort // "",
            .context.display // "",
            (.context.last_call_input_tokens // "" | tostring),
            (.context.percentage // "" | tostring)
        ][]' <<< "$input" 2>/dev/null
    )

    p_model=${json_fields[0]:-}
    p_version=${json_fields[1]:-}
    p_session=${json_fields[2]:-}
    p_cwd=${json_fields[3]:-}
    p_reasoning=${json_fields[4]:-}
    p_context_display=${json_fields[5]:-}
    p_context_tokens=${json_fields[6]:-}
    p_context_percent=${json_fields[7]:-}

    [[ -n "$p_model" && "$p_model" != "null" ]] && MODEL="$p_model"
    [[ -n "$p_version" && "$p_version" != "null" ]] && CLI_VERSION="$p_version"
    [[ -n "$p_session" && "$p_session" != "null" ]] && SESSION_ID="$p_session"
    [[ -n "$p_cwd" && "$p_cwd" != "null" ]] && CWD="$p_cwd"
    [[ -n "$p_reasoning" && "$p_reasoning" != "null" ]] && REASONING_EFFORT="$p_reasoning"
    [[ -n "$p_context_display" && "$p_context_display" != "null" ]] && CONTEXT_DISPLAY="$p_context_display"
    [[ -n "$p_context_tokens" && "$p_context_tokens" != "null" ]] && CONTEXT_TOKENS="$p_context_tokens"
    [[ -n "$p_context_percent" && "$p_context_percent" != "null" ]] && CONTEXT_PERCENT="$p_context_percent"
fi

DIR_NAME=$(basename "$CWD")
PARENT_CONTEXT=""
if [[ "$CWD" != "/" ]]; then
    PARENT_DIR=$(dirname "$CWD")
    if [[ "$PARENT_DIR" != "/" ]]; then
        GRANDPARENT_DIR=$(dirname "$PARENT_DIR")
        if [[ "$GRANDPARENT_DIR" != "/" ]]; then
            PARENT_CONTEXT="$(basename "$GRANDPARENT_DIR")/$(basename "$PARENT_DIR")"
        else
            PARENT_CONTEXT="$(basename "$PARENT_DIR")"
        fi
    fi
fi

GIT_INFO=""
PR_INFO=""
if [[ -d "$CWD" ]] && git_in_cwd rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    BRANCH=$(git_in_cwd symbolic-ref --quiet --short HEAD || true)
    if [[ -z "$BRANCH" ]]; then
        SHA=$(git_in_cwd rev-parse --short HEAD)
        [[ -n "$SHA" ]] && BRANCH="detached@${SHA}"
    fi

    if [[ -n "$BRANCH" ]]; then
        DIRTY=""
        if [[ -n "$(git_in_cwd status --porcelain --untracked-files=normal | head -n 1)" ]]; then
            DIRTY="● "
        fi
        GIT_INFO="${DIRTY}${BRANCH}"

        if [[ "$BRANCH" != detached@* ]]; then
            REPO_ROOT=$(git_in_cwd rev-parse --show-toplevel)
            PR_NUMBER=$(get_pr_number "$REPO_ROOT" "$BRANCH")
            [[ -n "$PR_NUMBER" ]] && PR_INFO="#${PR_NUMBER}"
        fi
    fi
fi

PY_INFO=""
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    VENV_NAME=$(basename "$VIRTUAL_ENV")
    [[ "$VENV_NAME" == ".venv" ]] && VENV_NAME="venv"
    PY_INFO="$VENV_NAME"
fi

printf "🕐 ${TIME_COLOR}%s${RESET}" "$TIME"

printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
printf "🤖 ${MODEL_COLOR}%s" "$MODEL"
if [[ -n "$REASONING_EFFORT" ]]; then
    printf -- "-%s" "$REASONING_EFFORT"
fi
printf "%b" "$RESET"
if [[ "$CONTEXT_TOKENS" =~ ^[0-9]+$ ]]; then
    context_display="$CONTEXT_DISPLAY"
    if [[ "$CONTEXT_PERCENT" =~ ^[0-9]+$ ]]; then
        context_display="${CONTEXT_PERCENT}%"
    fi
    if [[ -n "$context_display" ]]; then
        printf " ${ACCENT_COLOR}[${RESET}${CONTEXT_COLOR}%s:%s${RESET}${ACCENT_COLOR}]${RESET}" "$(format_tokens "$CONTEXT_TOKENS")" "$context_display"
    fi
fi
if [[ -n "$CLI_VERSION" ]]; then
    printf " ${ACCENT_COLOR}(v%s)${RESET}" "$CLI_VERSION"
fi

printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
printf "📁 ${DIR_COLOR}%s${RESET}" "$DIR_NAME"
if [[ -n "$PARENT_CONTEXT" ]]; then
    printf " ${ACCENT_COLOR}(${RESET}${PARENTS_COLOR}%s${RESET}${ACCENT_COLOR})${RESET}" "$PARENT_CONTEXT"
fi

if [[ -n "$PY_INFO" ]]; then
    printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
    printf "🐍 ${PY_COLOR}%s${RESET}" "$PY_INFO"
fi

if [[ -n "$GIT_INFO" ]]; then
    printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
    if [[ "$GIT_INFO" == "● "* ]]; then
        printf "🌿 ${GIT_DIRTY_COLOR}%s${RESET}" "${GIT_INFO#● }"
    else
        printf "🌿 ${GIT_COLOR}%s${RESET}" "$GIT_INFO"
    fi
    if [[ -n "$PR_INFO" ]]; then
        printf " ${ACCENT_COLOR}(${RESET}${PR_COLOR}%s${RESET}${ACCENT_COLOR})${RESET}" "$PR_INFO"
    fi
fi

printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
printf "💻 ${HOST_COLOR}%s${RESET}" "$HOSTNAME"
if [[ -n "$SESSION_ID" ]]; then
    printf "${ACCENT_COLOR}/${RESET}${SESSION_COLOR}%s${RESET}" "$SESSION_ID"
fi

echo
