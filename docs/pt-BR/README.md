# N3LX Transcription Toolkit — Português (Brasil)

**Não ter CUDA não deveria impedir a aceleração.**

O **N3LX Transcription Toolkit** documenta como transcrever áudio e vídeo **localmente no Windows**, por CPU ou GPU AMD.

## Por que este projeto existe?

O projeto surgiu para atender às demandas de transcrição e ingestão de evidências do [AI-Assisted Design Engineering Operating System](https://github.com/nelsonseccofilho/ai-assisted-design-engineering-operating-system). Eu já utilizava o **WhisperX em CPU**, mas precisava processar reuniões e outras mídias com mais velocidade. Meu computador não possuía uma placa NVIDIA compatível com CUDA; possuía uma **AMD Radeon RX 6600M**.

Por isso, desenvolvi e validei progressivamente um pipeline que combina **whisper.cpp/Vulkan** (reconhecimento) com **ONNX Runtime/DirectML** (alinhamento de palavras e diarização). A alternativa tradicional de WhisperX CPU permanece independente.

O Operating System motivou essa solução, mas **não é obrigatório para usar o Toolkit**. A ferramenta poderá apoiar entrevistas, aulas, reuniões e gravações autorizadas.

## Equipamento em que realizamos os testes

| Componente | Configuração |
| --- | --- |
| Sistema | Windows 11 Pro |
| Processador | AMD Ryzen 5 5500, 3,60 GHz |
| Memória RAM | 24 GB |
| GPU | AMD Radeon RX 6600M, 8 GB de VRAM |
| NVIDIA/CUDA | **Não utilizados** |

Uma mídia de **18 minutos** foi processada em **7 minutos e 29 segundos**, com 1.805 palavras alinhadas, reconhecimento Vulkan confirmado e alinhamento/diarização DirectML confirmados. Isso representa cerca de **2,4 vezes a velocidade do tempo real**, mas **não** equivale a um benchmark CPU contra GPU com configurações idênticas.

## Escolha seu caminho

- [Instalação CPU — WhisperX (em inglês)](../en/CPU_SETUP.md)
- [Arquitetura e instalação AMD GPU (em inglês)](../en/AMD_GPU_SETUP.md)
- [Dependências identificadas e pendências de versão](../en/DEPENDENCIES.md)
- [Histórico das decisões de engenharia](../en/DEVELOPMENT_HISTORY.md)
- [Comandos e arquivos de saída](../en/OUTPUTS_AND_CLI.md)
- [Reprodução em ambiente limpo](../en/REPRODUCIBILITY.md)
- [Testes e limitações](../en/VALIDATION.md)
- [Critérios para a publicação do software](../en/RELEASE_CRITERIA.md)

> **Situação da publicação:** a aplicação GPU v1.0.0 foi validada **localmente**, mas o repositório público ainda é uma base de documentação. **Ele não fornece, neste momento, um instalador completo e reproduzível em outro computador.** O objetivo é publicar a implementação, dependências e testes depois das auditorias de segurança, licenças e reprodução.

A gravação é a evidência primária; a transcrição é uma representação auxiliar e pode conter erros. Não publique gravações privadas, transcrições reais, tokens, caminhos pessoais ou capturas sem revisão.

O [README principal](../../README.md) está em inglês. O histórico segue [Conventional Commits](https://www.conventionalcommits.org/) em inglês. A licença do software público ainda precisa ser definida e publicada.
