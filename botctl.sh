#!/usr/bin/env bash
# Unified controller for managing the KRS Reminder bot lifecycle.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$PROJECT_ROOT/var/run"
LOG_DIR="$PROJECT_ROOT/var/log"
PIDFILE="$RUN_DIR/bot.pid"
LOGFILE="$LOG_DIR/bot.log"
SRC_DIR="$PROJECT_ROOT/src"
PYTHONPATH="$SRC_DIR${PYTHONPATH:+:$PYTHONPATH}"

ensure_dirs() {
    mkdir -p "$RUN_DIR" "$LOG_DIR"
}

is_running() {
    local pid
    if [[ -f "$PIDFILE" ]]; then
        pid=$(cat "$PIDFILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

start_bot() {
    ensure_dirs

    if is_running; then
        local pid
        pid=$(cat "$PIDFILE")
        echo "❌ Bot already running (PID: $pid)"
        echo "   Use '$0 restart' to restart or '$0 stop' to stop it first."
        return 1
    fi

    if [[ -f "$PIDFILE" ]]; then
        echo "⚠️  Removing stale PID file"
        rm -f "$PIDFILE"
    fi

    # Validate Python environment
    if ! command -v python3 &> /dev/null; then
        echo "❌ python3 not found in PATH"
        return 1
    fi

    # Validate source directory
    if [[ ! -d "$SRC_DIR/krs_reminder" ]]; then
        echo "❌ Source directory not found: $SRC_DIR/krs_reminder"
        return 1
    fi

    echo "🚀 Starting KRS Reminder Bot..."
    cd "$PROJECT_ROOT"
    PYTHONPATH="$PYTHONPATH" nohup python3 -m krs_reminder.cli >> "$LOGFILE" 2>&1 &
    local pid=$!
    echo $pid > "$PIDFILE"

    sleep 2

    if ps -p "$pid" > /dev/null 2>&1; then
        echo "✅ Bot started successfully!"
        echo "   PID : $pid"
        echo "   Logs: $LOGFILE"
        echo ""
        echo "💡 Use '$0 logs' to monitor the bot"
    else
        echo "❌ Failed to start bot"
        echo "   Check $LOGFILE for errors"
        rm -f "$PIDFILE"
        return 1
    fi

    return 0
}

stop_bot() {
    if [[ ! -f "$PIDFILE" ]]; then
        echo "❌ Bot is not running (no PID file found)"
        return 1
    fi

    local pid
    pid=$(cat "$PIDFILE")

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "❌ Bot is not running (stale PID file)"
        rm -f "$PIDFILE"
        return 1
    fi

    echo "🛑 Stopping bot (PID: $pid)..."
    kill "$pid"

    for _ in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ Bot stopped successfully"
            rm -f "$PIDFILE"
            return 0
        fi
        sleep 0.5
    done

    if ps -p "$pid" > /dev/null 2>&1; then
        echo "⚠️  Force stopping..."
        kill -9 "$pid" || true
        sleep 1
    fi

    if ps -p "$pid" > /dev/null 2>&1; then
        echo "❌ Failed to stop bot"
        return 1
    fi

    echo "✅ Bot stopped (forced)"
    rm -f "$PIDFILE"
    return 0
}

status_bot() {
    echo "📊 KRS Reminder Bot Status"
    echo "=========================================="

    if [[ ! -f "$PIDFILE" ]]; then
        echo "Status: ❌ Not running"
        echo "=========================================="
        return 1
    fi

    local pid
    pid=$(cat "$PIDFILE")

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo "Status: ❌ Not running (stale PID file)"
        echo "=========================================="
        rm -f "$PIDFILE"
        return 1
    fi

    local uptime mem cpu
    uptime=$(ps -p "$pid" -o etime= | tr -d ' ')
    mem=$(ps -p "$pid" -o rss= | awk '{printf "%.1f MB", $1/1024}')
    cpu=$(ps -p "$pid" -o %cpu= | tr -d ' ')

    echo "Status: ✅ Running"
    echo "PID   : $pid"
    echo "Uptime: $uptime"
    echo "Memory: $mem"
    echo "CPU   : $cpu%"
    echo "=========================================="
    return 0
}

logs_bot() {
    ensure_dirs

    local lines="${2:-50}"
    local follow="${3:-yes}"

    if [[ ! -f "$LOGFILE" ]]; then
        echo "❌ Log file not found: $LOGFILE"
        return 1
    fi

    echo "📝 KRS Reminder Bot Logs"
    echo "=========================================="

    if [[ "$follow" == "yes" ]]; then
        echo "Following logs (Press Ctrl+C to exit)"
        echo "=========================================="
        echo
        tail -n "$lines" -f "$LOGFILE"
    else
        echo "Last $lines lines"
        echo "=========================================="
        echo
        tail -n "$lines" "$LOGFILE"
    fi
}

run_foreground() {
    ensure_dirs
    cd "$PROJECT_ROOT"
    echo "🚀 Running bot in foreground mode..."
    echo "   Press Ctrl+C to stop"
    echo ""
    PYTHONPATH="$PYTHONPATH" python3 -m krs_reminder.cli
}

restart_bot() {
    echo "🔄 Restarting KRS Reminder Bot..."
    echo ""

    if is_running; then
        stop_bot || echo "⚠️  Stop step returned non-zero, continuing"
        sleep 2
    else
        echo "ℹ️  Bot not running, starting fresh..."
    fi

    start_bot

    if [[ $? -eq 0 ]]; then
        echo ""
        echo "✅ Restart completed successfully"
    else
        echo ""
        echo "❌ Restart failed"
        return 1
    fi
}

show_help() {
    cat <<USAGE
Usage: $0 <command>

Commands:
  start     Start the bot in background mode
  stop      Stop the running bot
  restart   Restart the bot (stop -> start)
  status    Show current bot status
  logs      Tail the bot log file
  run       Run the bot in the foreground (blocking)
  help      Show this help message

Examples:
  $0 start
  $0 logs
  $0 run
USAGE
}

main() {
    local cmd=${1:-help}
    case "$cmd" in
        start) start_bot ;;
        stop) stop_bot ;;
        restart) restart_bot ;;
        status) status_bot ;;
        logs) logs_bot ;;
        run) run_foreground ;;
        help|--help|-h) show_help ;;
        *)
            echo "❌ Unknown command: $cmd" >&2
            echo
            show_help
            return 1
            ;;
    esac
}

main "$@"
exit $?
