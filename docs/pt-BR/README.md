# N3LX Transcription Toolkit — Português (Brasil)

O **N3LX Transcription Toolkit** é uma iniciativa para tornar a transcrição local de áudios e vídeos mais acessível, com caminhos separados para **CPU** e **GPU AMD** no Windows.

Nosso objetivo é permitir que outras pessoas compreendam a instalação, diagnostiquem problemas, validem o processamento e exportem transcrições com timestamps e, opcionalmente, identificação de participantes.

> **Situação atual:** documentação inicial. O fluxo CPU e um protótipo AMD GPU foram validados em uma máquina de referência, mas o repositório ainda não distribui um instalador completo e reproduzível nem o código da aplicação GPU. Não trate esta versão como pronta para instalar do zero.

## Por onde começar

- [Instalação em CPU (guia em inglês)](../en/CPU_SETUP.md)
- [Arquitetura e pré-requisitos da GPU AMD (guia em inglês)](../en/AMD_GPU_SETUP.md)
- [Testes, métricas e limitações](../en/VALIDATION.md)
- [Solução de problemas](../en/TROUBLESHOOTING.md)

A instalação CPU utiliza o WhisperX tradicional. A implementação GPU AMD utiliza um pipeline específico com **whisper.cpp + Vulkan** para reconhecimento e **ONNX Runtime + DirectML** para alinhamento e diarização. Não basta trocar o parâmetro de dispositivo do WhisperX original.

A validação local de uma gravação de 18 minutos resultou em 1.805 palavras alinhadas e processamento em aproximadamente 7 minutos e 29 segundos, com execução Vulkan e DirectML confirmada. Isso **não comprova**, por si só, superioridade de precisão em relação ao WhisperX CPU.

## Uma regra importante

**Gravação original, transcrição e interpretação são coisas diferentes.** A transcrição ajuda a localizar falas e navegar pelo material, mas decisões importantes devem ser conferidas na gravação.

Não publique mídias privadas, transcrições de clientes, tokens ou caminhos com informações pessoais. Exemplos públicos deverão utilizar materiais próprios ou autorizados e capturas revisadas.

## Idiomas e contribuições

O [README principal](../../README.md) e a documentação técnica começam em inglês; manteremos acesso em português brasileiro. Commits usam [Conventional Commits](https://www.conventionalcommits.org/), com mensagens em inglês.

A licença do código ainda está em análise. Até que uma licença seja publicada, não presuma permissão de reutilização somente porque o repositório é público.
