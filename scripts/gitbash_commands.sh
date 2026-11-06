# N3LX Transcription Toolkit — Git Bash developer preview.
# Use: source "/path/to/N3LX-Transcription-Toolkit/scripts/gitbash_commands.sh"
# Models, DirectML environments and local diarization worker are prerequisites.
_N3LX_SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

_n3lx_path() {
    local value="$1"
    if [[ "$value" == [A-Za-z]:* ]] && command -v cygpath >/dev/null 2>&1; then
        value="$(cygpath -u -- "$value")" || return 1
    fi
    realpath -e -- "$value"
}

_n3lx_windows() {
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -w -- "$1"
    else
        printf '%s\n' "$1"
    fi
}

transcrever() {
    if [ "$#" -ne 1 ]; then
        echo "Uso: transcrever ARQUIVO" >&2
        return 2
    fi
    local arquivo ext root qa monitor exportador destino log status relatorio origem path
    arquivo="$(_n3lx_path "$1")" || {
        echo "Arquivo nao encontrado: $1" >&2
        return 2
    }
    [ -f "$arquivo" ] || { echo "Nao e arquivo: $arquivo" >&2; return 2; }
    ext="${arquivo##*.}"
    case "${ext,,}" in
        mkv|mp4|mp3|ogg) ;;
        *) echo "Formato nao suportado: .$ext" >&2; return 2 ;;
    esac

    root="${N3LX_REPO_ROOT:-$_N3LX_SOURCE_ROOT}"
    root="$(_n3lx_path "$root")" || { echo "Raiz do Toolkit inexistente" >&2; return 2; }
    qa="${N3LX_QA_SCRIPT:-$root/src/n3lx_toolkit/qa_unificado.py}"
    qa="$(_n3lx_path "$qa")" || { echo "Executor QA inexistente" >&2; return 2; }
    monitor="$root/src/n3lx_toolkit/monitor.py"
    exportador="$root/src/n3lx_toolkit/export_framework.py"
    for path in "$qa" "$monitor" "$exportador"; do
        [ -f "$path" ] || { echo "Dependencia ausente: $path" >&2; return 2; }
    done
    destino="${arquivo%/*}/transcricao/${arquivo##*/}.framework.json"
    mkdir -p "${arquivo%/*}/transcricao" || return 1
    log="$(mktemp)" || return 1
    echo "NELX-Whisper-GPU | Whisper large-v3 / Vulkan / Beam 5 / DirectML"
    echo "Entrada: $arquivo"
    echo "Saida:   $destino"

    python "$monitor" --qa "$(_n3lx_windows "$qa")" \
        --input "$(_n3lx_windows "$arquivo")" --modo completo 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
    if [ "$status" -ne 0 ] || ! grep -Fq 'RESULTADO FINAL: QA_END_TO_END_PASS' "$log"; then
        echo "QA reprovado. Diagnostico: $log" >&2
        return 1
    fi

    relatorio="$(sed -n 's/^Relatorio: //p' "$log" | tail -n 1 | tr -d '\r')"
    if [ -z "$relatorio" ]; then
        echo "QA nao informou relatorio. Log: $log" >&2
        return 1
    fi
    origem="$(_n3lx_path "$relatorio")" || {
        echo "Relatorio QA nao encontrado. Log: $log" >&2
        return 1
    }
    origem="${origem%/*}"
    python "$exportador" \
        --media "$(_n3lx_windows "$arquivo")" \
        --integrado "$(_n3lx_windows "$origem/integrado.json")" \
        --qa-report "$(_n3lx_windows "$origem/qa_report.json")" \
        --qualidade "$(_n3lx_windows "$origem/integracao-qualidade.json")" \
        --saida "$(_n3lx_windows "$destino")"
    status=$?
    if [ "$status" -eq 0 ]; then
        rm -f "$log"
        echo "CONCLUIDO: $destino"
    else
        echo "Exportacao falhou; log: $log" >&2
    fi
    return "$status"
}

transcrever_pasta() {
    if [ "$#" -gt 1 ]; then
        echo "Uso: transcrever_pasta [PASTA]" >&2
        return 2
    fi
    local pasta arquivo total=0 ok=0 fail=0
    pasta="$(_n3lx_path "${1:-.}")" || { echo "Pasta nao encontrada" >&2; return 2; }
    [ -d "$pasta" ] || { echo "Nao e pasta: $pasta" >&2; return 2; }
    for arquivo in "$pasta"/*; do
        [ -f "$arquivo" ] || continue
        case "${arquivo,,}" in
            *.mkv|*.mp4|*.mp3|*.ogg)
                total=$((total + 1))
                echo "=== Arquivo $total: ${arquivo##*/} ==="
                if transcrever "$arquivo"; then
                    ok=$((ok + 1))
                else
                    fail=$((fail + 1))
                fi
                ;;
        esac
    done
    echo "TOTAL: $total | PASS: $ok | FALHAS: $fail"
    [ "$total" -gt 0 ] && [ "$fail" -eq 0 ]
}
