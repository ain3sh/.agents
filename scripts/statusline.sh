#!/usr/bin/env bash
# ~/.agents/scripts/statusline.sh
# Factory Droid Status Line

# read JSON input from Factory Droid
input=$(cat)

# === ELEGANT DISPLAY CONFIG ===
TIME_COLOR="\033[38;2;135;206;250m"        # sky blue
HOST_COLOR="\033[38;2;106;159;181m"        # steel blue
MODEL_COLOR="\033[38;2;186;133;232m"       # soft purple
TOKENS_COLOR="\033[38;2;255;159;67m"       # orange amber
ACTIVE_TIME_COLOR="\033[38;2;152;251;152m" # pale green
DIR_COLOR="\033[38;2;255;179;71m"          # warm amber
PARENTS_COLOR="\033[38;2;255;205;128m"     # light amber
GIT_COLOR="\033[38;2;152;195;121m"         # soft green
PY_COLOR="\033[38;2;97;214;214m"           # aqua
SESSION_COLOR="\033[38;2;169;169;169m"     # dim gray
SEPARATOR_COLOR="\033[38;2;128;128;128m"   # medium gray
ACCENT_COLOR="\033[38;2;180;180;180m"      # light gray
RESET="\033[0m"
SEP_DOT="◦"


# === HELPER FUNCTIONS ===
format_tokens() {
    local tokens=$1
    if [[ $tokens -ge 1000000 ]]; then
        local whole=$((tokens / 1000000))
        local frac=$(( (tokens % 1000000) / 10000 ))
        printf "%d.%02dM" "$whole" "$frac"
    elif [[ $tokens -ge 1000 ]]; then
        local whole=$((tokens / 1000))
        local frac=$(( (tokens % 1000) / 10 ))
        printf "%d.%02dk" "$whole" "$frac"
    else
        printf "%d" "$tokens"
    fi
}

format_duration() {
    local ms=$1
    local secs=$((ms / 1000))
    local mins=$((secs / 60))
    local hours=$((mins / 60))
    secs=$((secs % 60))
    mins=$((mins % 60))
    if [[ $hours -gt 0 ]]; then
        printf "%02d:%02d:%02d" "$hours" "$mins" "$secs"
    else
        printf "%d:%02d" "$mins" "$secs"
    fi
}


# === SYSTEM DATA ===
TIME=$(date '+%H:%M')
HOSTNAME=$(hostname -s)


# === JSON DATA EXTRACTION ===
MODEL="droid"
SESSION_ID=""
CWD=$(pwd)
TRANSCRIPT_PATH=""

if command -v jq >/dev/null 2>&1 && [[ -n "$input" ]]; then
    if echo "$input" | jq -e . >/dev/null 2>&1; then
        # model display name (direct, no parsing needed)
        raw_model=$(echo "$input" | jq -r '.model.display_name // .model.id // empty' 2>/dev/null)
        [[ -n "$raw_model" && "$raw_model" != "null" ]] && MODEL="$raw_model"

        # session id
        raw_session=$(echo "$input" | jq -r '.session_id // empty' 2>/dev/null)
        [[ -n "$raw_session" && "$raw_session" != "null" ]] && SESSION_ID="$raw_session"

        # working directory
        raw_cwd=$(echo "$input" | jq -r '.cwd // empty' 2>/dev/null)
        [[ -n "$raw_cwd" && "$raw_cwd" != "null" ]] && CWD="$raw_cwd"

        # transcript path (for settings.json lookup)
        raw_transcript=$(echo "$input" | jq -r '.transcript_path // empty' 2>/dev/null)
        [[ -n "$raw_transcript" && "$raw_transcript" != "null" ]] && TRANSCRIPT_PATH="$raw_transcript"
    fi
fi


# === SESSION SETTINGS EXTRACTION ===
TOKENS_USED=""
ACTIVE_TIME=""

if [[ -n "$TRANSCRIPT_PATH" ]]; then
    # derive settings path: /path/to/<session-id>.jsonl -> /path/to/<session-id>.settings.json
    SETTINGS_PATH="${TRANSCRIPT_PATH%.jsonl}.settings.json"
    
    if [[ -f "$SETTINGS_PATH" ]] && command -v jq >/dev/null 2>&1; then
        settings=$(cat "$SETTINGS_PATH" 2>/dev/null)
        if echo "$settings" | jq -e . >/dev/null 2>&1; then
            # token usage: inputTokens + thinkingTokens + outputTokens
            input_tok=$(echo "$settings" | jq -r '.tokenUsage.inputTokens // 0' 2>/dev/null)
            thinking_tok=$(echo "$settings" | jq -r '.tokenUsage.thinkingTokens // 0' 2>/dev/null)
            output_tok=$(echo "$settings" | jq -r '.tokenUsage.outputTokens // 0' 2>/dev/null)
            total_tok=$((input_tok + thinking_tok + output_tok))
            [[ $total_tok -gt 0 ]] && TOKENS_USED=$(format_tokens $total_tok)

            # active time (extracted but not displayed - for future use)
            active_ms=$(echo "$settings" | jq -r '.assistantActiveTimeMs // 0' 2>/dev/null)
            [[ $active_ms -gt 0 ]] && ACTIVE_TIME=$(format_duration $active_ms)
        fi
    fi
fi


# === DIRECTORY CONTEXT (2 levels up) ===
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


# === GIT BRANCH (simplified) ===
GIT_INFO=""
if cd "$CWD" 2>/dev/null && git rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    if [[ -n "$BRANCH" ]]; then
        DIRTY=""
        if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
            DIRTY="● "
        fi
        GIT_INFO="${DIRTY}${BRANCH}"
    fi
fi


# === PYTHON ENVIRONMENT ===
PY_INFO=""
if [[ -n "$VIRTUAL_ENV" ]]; then
    VENV_NAME=$(basename "$VIRTUAL_ENV")
    [[ "$VENV_NAME" == ".venv" ]] && VENV_NAME="venv"
    PY_INFO="$VENV_NAME"
fi


# === OUTPUT ===
# time
printf "🕐 ${TIME_COLOR}%s${RESET}" "$TIME"

# model [tokens]
printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
printf "🤖 ${MODEL_COLOR}%s${RESET}" "$MODEL"
if [[ -n "$TOKENS_USED" ]]; then
    printf " ${ACCENT_COLOR}[${RESET}${TOKENS_COLOR}%s${RESET}${ACCENT_COLOR}]${RESET}" "$TOKENS_USED"
fi

# directory
printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
printf "📁 ${DIR_COLOR}%s${RESET}" "$DIR_NAME"
if [[ -n "$PARENT_CONTEXT" ]]; then
    printf " ${ACCENT_COLOR}(${RESET}${PARENTS_COLOR}%s${RESET}${ACCENT_COLOR})${RESET}" "$PARENT_CONTEXT"
fi

# python env (before git)
if [[ -n "$PY_INFO" ]]; then
    printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
    printf "🐍 ${PY_COLOR}%s${RESET}" "$PY_INFO"
fi

# git
if [[ -n "$GIT_INFO" ]]; then
    printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
    if [[ "$GIT_INFO" == "● "* ]]; then
        printf "🌿 ${ACCENT_COLOR}●${RESET} ${GIT_COLOR}%s${RESET}" "${GIT_INFO#● }"
    else
        printf "🌿 ${GIT_COLOR}%s${RESET}" "$GIT_INFO"
    fi
fi

# hostname/session_id (rightmost)
printf " ${SEPARATOR_COLOR}%s${RESET} " "$SEP_DOT"
printf "💻 ${HOST_COLOR}%s${RESET}" "$HOSTNAME"
if [[ -n "$SESSION_ID" ]]; then
    printf "${ACCENT_COLOR}/${RESET}${SESSION_COLOR}%s${RESET}" "$SESSION_ID"
fi

echo
