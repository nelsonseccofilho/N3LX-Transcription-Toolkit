# Estrutura de desenvolvimento — novembro/2026

**O Toolkit agora inclui código-fonte de desenvolvimento**, não apenas documentação. Foram incorporados o QA unificado, o monitor, o exportador de evidências e os comandos Git Bash. **Ainda não é um instalador público ou uma reprodução completa do ambiente Windows validado**: o worker exato do Community-1, os ambientes Python isolados, os modelos e as permissões de redistribuição dependem de recuperação e revisão.

## Estrutura

~~~text
src/n3lx_toolkit/qa_unificado.py       seis etapas, cache, Vulkan/DirectML
src/n3lx_toolkit/monitor.py            painel com progresso medido do ASR
src/n3lx_toolkit/export_framework.py   um JSON de evidência por gravação
scripts/gitbash_commands.sh            transcrever / transcrever_pasta
tests/test_toolkit.py                  testes fictícios e offline
docs/en/LOCAL_DEVELOPER_SETUP.md       guia técnico detalhado
~~~

O reconhecimento local é Whisper large-v3/Vulkan em português, Beam Size 5; o alinhamento utiliza CTC Wav2Vec2 português/ONNX DirectML e a diarização utiliza Community-1/DirectML, **quando as dependências externas já estão instaladas**.

## Dependências que não vêm no clone

FFmpeg, whisper.cpp compilado com Vulkan, modelo GGML large-v3, ONNX CTC português, fonte PyTorch do modelo Wav2Vec2, modelos ONNX do Community-1, dois ambientes Python compatíveis e o **worker real de diarização**. Não é correto alegar que esses elementos foram instalados pelo repositório.

Variáveis suportadas:

- **N3LX_WORKSPACE:** local de ferramentas, modelos, ambientes e cache.
- **N3LX_DIARIZATION_WORKER:** caminho do worker de diarização compatível.
- **N3LX_QA_SCRIPT:** caminho opcional para o QA local já aprovado.
- **N3LX_REPO_ROOT:** raiz opcional dos scripts Bash.

## Uso no Git Bash (ambiente configurado)

~~~bash
cd "/c/exemplo/N3LX-Transcription-Toolkit"
source scripts/gitbash_commands.sh

transcrever "/c/exemplo/gravacao.mkv"
transcrever_pasta "/c/exemplo/midias"
~~~

O segundo comando processa a pasta sequencialmente e não visita subpastas. Ambos aceitam seleção por extensão .mkv/.mp4/.mp3/.ogg, mas apenas **MKV** foi validado ponta a ponta em uma gravação real neste ciclo. A entrega fica em **transcricao/<nome-original>.framework.json**, preservando logs técnicos em um workspace privado. A fonte audiovisual é a evidência primária; a transcrição permanece UNREVIEWED até revisão.

## Testar sem GPU

~~~bash
python -m unittest discover -s tests -p "test_*.py" -v
bash -n scripts/gitbash_commands.sh
~~~

Esses testes não comprovam uma nova instalação Vulkan/DirectML ou qualidade do texto. Leia o guia em inglês, os resultados de novembro e os critérios de release antes de publicar um instalador.
