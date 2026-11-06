# Auditoria do worker local — Git Bash (somente leitura)

Este é o próximo passo de equalização do **N3LX-Transcription-Toolkit**. O worker final que já está funcionando em Windows **não está entre os arquivos recuperados nesta conversa**. Por isso, não vamos substituí-lo nem fingir que a reconstrução publicada é idêntica.

A auditoria compara **dois arquivos Python**: o worker atualmente instalado e o candidato publicado no PR #8. Mostra SHA-256, funções alteradas e a presença de marcadores do contrato regular/exclusivo. **Não importa ou executa o código**, não lê áudio/modelos, não altera nenhuma instalação e não envia o conteúdo do worker a serviços externos. A única rede utilizada no procedimento abaixo é para **baixar dois arquivos públicos do GitHub**.

## Um comando no Git Bash

Execute exatamente este bloco no Windows onde a transcrição já funciona:

~~~bash
(
  set -e

  INSTALADO="$HOME/Git/NELX-Whisper-GPU/src/diarizacao_directml_worker.py"
  if [ ! -f "$INSTALADO" ]; then
    echo "ERRO: worker final local nao encontrado. Nenhum arquivo foi alterado."
    exit 2
  fi

  TMPDIR_AUDIT="$(mktemp -d)" || exit 2
  trap 'rm -rf "$TMPDIR_AUDIT"' EXIT

  BASE="https://raw.githubusercontent.com/nelsonseccofilho/N3LX-Transcription-Toolkit/docs/nov-2026-gpu-qa-framework-evidence"

  curl -fLsS "$BASE/scripts/auditar_worker_local.py" -o "$TMPDIR_AUDIT/auditar_worker_local.py"
  curl -fLsS "$BASE/src/n3lx_toolkit/diarizacao_directml_worker.py" -o "$TMPDIR_AUDIT/worker_publicado.py"

  python "$TMPDIR_AUDIT/auditar_worker_local.py" \
    --instalado "$INSTALADO" \
    --publicado "$TMPDIR_AUDIT/worker_publicado.py"
)
~~~

Não é necessário começar outra transcrição, mexer nos modelos ou abrir a GPU. O relatório aparece no terminal e a pasta temporária é eliminada automaticamente.

## Como interpretar o resultado

| Status | Interpretação |
| --- | --- |
| \`MATCH_EXATO\` | Hash SHA-256 idêntico: os arquivos são iguais byte a byte |
| \`DIVERGENCIA_ESTRUTURAL\` | A estrutura das funções ou os sinais do contrato diferem; comparar antes de migrar |
| \`DIFERENCA_NAO_FUNCIONAL_OU_EXTERNA\` | Hashes divergem, mas as funções principais analisadas não diferem; **não** significa equivalência funcional |

O relatório mostra apenas hashes, tamanho dos arquivos, nomes de funções e sinais do contrato. Não inclui transcrição, áudio, caminhos absolutos nem linhas do código privado. O campo \`worker_local_tem_intervalos_exclusivos\` é uma **pista estática**, não uma verificação de execução.

## Critério de conclusão deste ciclo

- [x] Worker candidato e contrato regular/exclusivo registrados no PR.
- [x] Auditor de comparação somente leitura com testes sintéticos.
- [ ] Verificar o relatório do worker final instalado no Windows.
- [ ] Rever as diferenças efetivas com o código aprovado, sem alterar a instalação.
- [ ] Rodar validação de GPU apenas se for necessário para comprovar a nova versão.

**Não execute nenhuma substituição automática do worker local com base neste relatório.**
