# Novembro/2026 — pipeline AMD, QA unificado e JSON para evidências

> **Limite:** experiência validada em uma máquina Windows; não é instalador nem distribuição do código completo. O novo executor local `NELX-Whisper-GPU` não é idêntico ao aplicativo v1.0.0 anteriormente documentado.

## Configuração que funcionou

- **Reconhecimento:** Whisper **large-v3**, `whisper.cpp` com Vulkan na AMD Radeon RX 6600M; português (`-l pt`), GPU 0, seis threads, `-mc 0` e **Beam Size `-bs 5`**.
- **Áudio:** FFmpeg para PCM mono 16 kHz.
- **Alinhamento:** Wav2Vec2 XLSR-53 português exportado para ONNX, com inferência DirectML e alinhamento forçado CTC.
- **Diarização:** pyannote Community-1 ONNX/DirectML; intervalos regulares e exclusivos, com atribuição de palavras pelos exclusivos.
- **QA:** etapas `preflight`, `audio_16khz`, `ctc_directml`, `asr_vulkan`, `diarization_directml` e `integracao_final`.
- **Entrega:** um único `<nome-original>.framework.json` na subpasta `transcricao/`; caches, WAV temporário, logs e QA ficam em armazenamento privado separado.

`-bs 1` foi preservado como referência anterior. A mudança para `-bs 5` também alterou a assinatura do cache para não reutilizar indevidamente o ASR antigo. **Ainda não existe comparação humana controlada que prove ganho de precisão.** A verificação inicial CTC de logits de 2/3 segundos prova execução numérica, não timestamps por palavra.

## Uso em Git Bash — apenas instalação local

~~~bash
transcrever gravacao.mkv       # um arquivo
transcrever_pasta              # todos os compatíveis da pasta atual
transcrever_pasta "/pasta"     # pasta especificada
~~~

São funções do Git Bash **não incluídas no clone público**. A seleção de formatos aceita `.mkv`, `.mp4`, `.mp3` e `.ogg` via FFmpeg; **a validação real ponta a ponta desta etapa foi com MKV**. O lote é sequencial e não recursivo. Com Tab, o Bash completa nomes com espaços. O comando `transcrever_pasta` recebe uma pasta, não um arquivo. A documentação PowerShell/WhisperXGPU anterior permanece histórica.

## Evidência anônima de gravação real

| Métrica | Resultado |
| --- | ---: |
| Mídia | 21min03s (1.262,891 s) |
| Soma de tempos das etapas | aproximadamente 13min04s |
| Reconhecimento Vulkan | 562,92 s, 530 segmentos |
| Diarização DirectML | 61,86 s, 477 intervalos regulares / 487 exclusivos |
| Integração final | 133,19 s, 530 segmentos |
| Palavras reconhecidas | 3.202 |
| Palavras com timestamps | 3.149/3.202 = **98,34%** |
| Palavras alinhadas atribuídas a participante | 3.146/3.149 = **99,90%** |
| QA completo | **6 de 6 PASS** |

**98,34% representa cobertura de alinhamento, não precisão textual.** Numerais e janelas de áudio curtas podem permanecer sem tempo exato. Os rótulos `SPEAKER_00` etc. não são identidades e podem divergir dentro do mesmo segmento. Não inventar tempo, fala ou participante. O resultado não prova superioridade da GPU sobre CPU nem valida outro equipamento.

## Monitor integrado

O monitor, inicialmente testado em outra janela em modo somente leitura, foi integrado aos dois comandos Git Bash. Durante execução real apresentou **3/6 etapas concluídas, Whisper em execução e 11,4% do áudio processado**. A porcentagem do ASR vem de timestamps reais do motor. Para etapas sem marcadores intermediários, mostrar “Em execução” ou “Pendente”, nunca um percentual inventado.

## Contrato de entrega para o framework

O JSON deve preservar Evidence ID, fingerprint/relação com a mídia, status **`UNREVIEWED`**, idioma/modelo/perfil, texto original por segmento, tempo inicial/final, atribuição anônima e alertas. Trocas de participante por palavra exigem revisão; não basta escolher um rótulo para a frase inteira. O esquema exato ainda necessita fixture sanitizada e validação de compatibilidade antes de ser anunciado como contrato público estável.

O [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system/blob/main/docs/EVIDENCE_INGESTION.md) separa **gravação → transcrição → evidência revisada → requisito/decisão → implementação/QA**. Nenhuma fala vira decisão aprovada automaticamente. Conteúdo real de clientes e transcrições pertencem ao projeto privado, nunca a este repositório público.

## Aprendizados e pendências

Preservar ambientes Python isolados e recuperação CPU; validar Vulkan e DirectML separadamente; invalidar cache quando o perfil muda; evitar repetir QA já aprovado; não confundir cobertura com WER; mostrar progresso mensurado; manter somente um arquivo de entrega por gravação. Antes de lançar software público: auditar código/licenças/modelos, fixar versões, testar instalação limpa, formatos adicionais, retomada de lotes, esquema JSON e precisão humana.

[Detalhes técnicos (inglês)](../en/NOVEMBER_2026_PIPELINE.md) · [Contrato de evidência](../en/FRAMEWORK_EVIDENCE_ADAPTER.md)
