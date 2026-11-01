# Validação realizada

Verificado em 1 de novembro de 2026 no ambiente Linux da nuvem, com Python 3.12.14.

| Verificação | Resultado |
| --- | --- |
| Instalação por `uv sync --locked` | Concluída; repetição sem mudanças de dependências. |
| `pytest -q` | 13 testes aprovados, nenhum pulado nessa execução. |
| Ruff: análise e formatação | Aprovadas. |
| Interface Streamlit | Navegação das três etapas testada; servidor respondeu HTTP 200 na raiz e no health check. |
| Detector Haar e LBPH reais | Cinco amostras derivadas de uma imagem de exemplo cadastradas; uma variação adicional foi reconhecida com distância 29,08 no limite 65. |
| PySerial | OFF → ON → OFF confirmado por um emulador em pseudoterminal Linux. |
| Sketch Arduino | Código real compilado e executado em um simulador C++ de GPIO, serial e relógio: boot desligado, comandos, rejeição de mensagens inválidas e watchdog aprovados. |
| Windows e câmera física | Não executados neste ambiente Linux; instruções fornecidas e job Windows configurado no CI. |
| Compilação AVR e gravação no Uno | Pendentes no Arduino IDE; o teste C++ simula a lógica, não a placa. |
| Relé e lâmpada de 127/220 V | Não conectados à nuvem; exigem comissionamento físico. |

O teste do detector usou a [imagem de exemplo astronaut do scikit-image](https://github.com/scikit-image/scikit-image/blob/v0.19.3/skimage/data/astronaut.png) somente em diretório temporário. Nenhum rosto de exemplo foi incluído no cadastro ou no projeto. Variações sintéticas da mesma imagem validam a execução do pipeline, **não medem acurácia**, resistência a fotos ou desempenho com pessoas diferentes. Faça a calibração no ambiente real com a pessoa autorizada e com pessoas não cadastradas antes de conectar a carga.
