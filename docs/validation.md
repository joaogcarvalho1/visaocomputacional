# Validação da detecção automática

Verificado em 1 de novembro de 2026 no ambiente Linux da nuvem, com Python 3.12.14.

| Verificação | Resultado |
| --- | --- |
| `pytest -q` | 22 testes aprovados, nenhum pulado nesta execução. |
| Ruff: análise e formatação | Aprovadas. |
| Detector Haar real | Detectou um rosto, dois rostos e nenhum rosto nos respectivos quadros de teste. Não exige cadastro ou arquivos de amostras. |
| Atrasos | Luz apagada antes de cinco segundos de presença, ligada no limite de cinco; desligamento após cinco segundos de ausência. |
| Mudança de condição | Interrupções reiniciam a contagem de ligar; retorno do rosto cancela a contagem de desligar. |
| Monitor com câmera simulada | Um ou dois rostos acionam a mesma lógica. Falha da câmera libera o dispositivo e envia desligamento, inclusive se a luz estiver ligada. |
| Protocolo serial | Testes verificam OFF inicial, ON/OFF confirmado, erro de confirmação e fechamento da porta. |
| Guia Streamlit | Monta o comando com a COM e atrasos selecionados; rejeita porta inválida. |
| Firmware | Sketch real executado com GPIO, relógio e serial simulados em C++: boot desligado, comandos, mensagens inválidas e watchdog aprovados. |
| Windows e câmera física | Não executados na nuvem Linux; dependem do computador do usuário. |
| Compilação AVR, gravação no Uno e rede 127/220 V | Exigem Arduino IDE e comissionamento físico. O teste C++ simula a lógica, não a placa. |

O teste do detector real usou a [imagem pública astronaut do scikit-image](https://github.com/scikit-image/scikit-image/blob/v0.19.3/skimage/data/astronaut.png), uma composição com duas cópias e um quadro vazio, somente em diretório temporário. Nenhuma imagem foi incluída no projeto. Essa checagem demonstra a execução do detector; não mede taxa de acertos em diferentes câmeras e condições de iluminação.

A versão atual não reconhece identidades, não usa LBPH e não lê nem grava fotos de cadastro. O watchdog do Arduino continua desligando após três segundos sem comando válido; esse mecanismo de falha é independente dos atrasos normais de cinco segundos.
