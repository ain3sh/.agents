#!/usr/bin/env bash
# ~/.agents/scripts/statusline.sh

input=$(cat)

TIME_COLOR="\033[38;2;135;206;250m"
HOST_COLOR="\033[38;2;106;159;181m"
MODEL_COLOR="\033[38;2;186;133;232m"
TOKENS_COLOR="\033[38;2;255;159;67m"
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

trim_spaces() {
    local s="$1"
    s="${s#${s%%[![:space:]]*}}"
    s="${s%${s##*[![:space:]]}}"
    printf '%s' "$s"
}

first_valid_dir() {
    local d
    for d in "$@"; do
        if [[ -n "$d" && -d "$d" ]]; then
            printf '%s' "$d"
            return 0
        fi
    done
    return 1
}

resolve_parent_cwd() {
    local p
    p=$(readlink -f "/proc/$PPID/cwd" 2>/dev/null || true)
    [[ -n "$p" && -d "$p" ]] && printf '%s' "$p"
}

resolve_cwd_from_transcript() {
    local transcript_path="$1"
    local tail_text
    local candidate

    [[ -f "$transcript_path" ]] || return 0

    tail_text=$(tail -c 65536 "$transcript_path" 2>/dev/null || true)
    [[ -n "$tail_text" ]] || return 0

    candidate=$(printf '%s' "$tail_text" | grep -oE '"command":"cd [^"]+"' | tail -n 1 | sed -E 's/^"command":"cd //; s/"$//')
    if [[ -z "$candidate" ]]; then
        candidate=$(printf '%s' "$tail_text" | grep -oE '\\"command\\":\\"cd [^\\"]+' | tail -n 1 | sed -E 's/^\\"command\\":\\"cd //')
    fi
    if [[ -z "$candidate" ]]; then
        candidate=$(printf '%s' "$tail_text" | grep -oE 'Running: cd [^\n"]+' | tail -n 1 | sed -E 's/^Running: cd //')
    fi

    [[ -n "$candidate" ]] || return 0

    candidate=$(trim_spaces "$candidate")
    candidate="${candidate%%&&*}"
    candidate="${candidate%%;*}"
    candidate=$(trim_spaces "$candidate")

    if [[ "$candidate" == ~/* ]]; then
        candidate="$HOME/${candidate#~/}"
    fi

    [[ -d "$candidate" ]] || return 0
    printf '%s' "$candidate"
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

    val=$(cd "$CWD" 2>/dev/null && GH_PAGER=cat gh pr view --json number --jq '.number' 2>/dev/null || true)
    [[ -z "$val" ]] && val="-"
    printf '%s %s\n' "$now" "$val" > "$cache_file" 2>/dev/null || true

    [[ "$val" == "-" ]] && return 0
    printf '%s' "$val"
}

TIME=$(date '+%H:%M')
HOSTNAME=$(hostname -s)

MODEL="droid"
CLI_VERSION=""
SESSION_ID=""
INPUT_CWD=""
PROCESS_CWD=$(pwd -P 2>/dev/null || pwd)
PARENT_CWD=$(resolve_parent_cwd)
CWD=""
TRANSCRIPT_PATH=""

if command -v jq >/dev/null 2>&1 && [[ -n "$input" ]] && echo "$input" | jq -e . >/dev/null 2>&1; then
    p_model=$(echo "$input" | jq -r '.model.display_name // .model.id // "droid"' 2>/dev/null)
    p_version=$(echo "$input" | jq -r '.version // ""' 2>/dev/null)
    p_session=$(echo "$input" | jq -r '.session_id // ""' 2>/dev/null)
    p_cwd=$(echo "$input" | jq -r '.cwd // ""' 2>/dev/null)
    p_transcript=$(echo "$input" | jq -r '.transcript_path // ""' 2>/dev/null)

    [[ -n "$p_model" && "$p_model" != "null" ]] && MODEL="$p_model"
    [[ -n "$p_version" && "$p_version" != "null" ]] && CLI_VERSION="$p_version"
    [[ -n "$p_session" && "$p_session" != "null" ]] && SESSION_ID="$p_session"
    [[ -n "$p_cwd" && "$p_cwd" != "null" ]] && INPUT_CWD="$p_cwd"
    [[ -n "$p_transcript" && "$p_transcript" != "null" ]] && TRANSCRIPT_PATH="$p_transcript"
fi

CWD=$(first_valid_dir "$PROCESS_CWD" "$INPUT_CWD" "$PARENT_CWD" "${FACTORY_PROJECT_DIR:-}" || printf '%s' "$HOME")

if [[ -n "$TRANSCRIPT_PATH" ]]; then
    transcript_cwd=$(resolve_cwd_from_transcript "$TRANSCRIPT_PATH")
    if [[ -n "$transcript_cwd" ]]; then
        if [[ "$CWD" == "$INPUT_CWD" || "$CWD" == "${FACTORY_PROJECT_DIR:-}" || -z "$INPUT_CWD" ]]; then
            CWD="$transcript_cwd"
        fi
    fi
fi

TOKENS_USED=""
if [[ -n "$TRANSCRIPT_PATH" ]]; then
    SETTINGS_PATH="${TRANSCRIPT_PATH%.jsonl}.settings.json"
    if [[ -f "$SETTINGS_PATH" ]] && command -v jq >/dev/null 2>&1; then
        tok_tuple=$(jq -r '[
            (.tokenUsage.inputTokens // 0),
            (.tokenUsage.thinkingTokens // 0),
            (.tokenUsage.outputTokens // 0)
        ] | @tsv' "$SETTINGS_PATH" 2>/dev/null)
        IFS=$'\t' read -r input_tok thinking_tok output_tok <<< "$tok_tuple"
        total_tok=$((input_tok + thinking_tok + output_tok))
        [[ $total_tok -gt 0 ]] && TOKENS_USED=$(format_tokens "$total_tok")
    fi
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
printf "🤖 ${MODEL_COLOR}%s${RESET}" "$MODEL"
if [[ -n "$CLI_VERSION" ]]; then
    printf " ${ACCENT_COLOR}(v%s)${RESET}" "$CLI_VERSION"
fi
if [[ -n "$TOKENS_USED" ]]; then
    printf " ${ACCENT_COLOR}[${RESET}${TOKENS_COLOR}%s${RESET}${ACCENT_COLOR}]${RESET}" "$TOKENS_USED"
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
