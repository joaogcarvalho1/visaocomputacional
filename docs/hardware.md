# Hardware: Arduino Uno, módulo relé 5 V e lâmpada 127/220 V

O computador reconhece o rosto e envia comandos pela porta USB. O Uno apenas controla a entrada de um **módulo relé com driver**, alimentado conforme a especificação do fabricante. Um relé avulso não deve ser ligado diretamente ao pino do Arduino: a bobina precisa de circuito de acionamento e proteção.

## Lado de controle — baixa tensão

Para um módulo comum de três pinos, compatível com lógica de 5 V:

| Arduino Uno | Módulo relé | Função |
| --- | --- | --- |
| D8 | IN / S | Comando digital |
| GND | GND | Referência do circuito de controle |
| 5 V ou fonte regulada dimensionada | VCC | Alimentação, conforme a corrente exigida pelo módulo |

Use USB para conectar o Uno ao computador. Confira o consumo do módulo e o orçamento de corrente do Uno/USB antes de usar o pino 5 V. Módulos com `JD-VCC`, optoacoplador ou fonte independente têm ligações específicas: siga seu manual, sem presumir a posição dos jumpers nem unir fontes indiscriminadamente.

O sketch usa **D8** e considera acionamento em **LOW** por padrão. `RELAY_ACTIVE_LOW = false` seleciona módulo ativo em HIGH. O LED embutido indica o estado lógico solicitado, não a presença de tensão na lâmpada.

## Lado da lâmpada — 127/220 V

Essa parte exige profissional qualificado. Não use protoboard, fios Dupont ou terminais expostos para a rede elétrica. Não conecte tensão da rede aos pinos do Arduino.

O instalador deve dimensionar relé, contatos, proteção, cabos, terminais e caixa isolante para a tensão e a corrente da lâmpada, incluindo a corrente de partida do driver LED. A inscrição de corrente para carga resistiva no relé não garante capacidade equivalente para qualquer lâmpada. O estado desenergizado deve manter a lâmpada desligada, usando o contato normalmente aberto adequado. Aterramento e isolamento entre rede e controle devem seguir as normas locais.

Não há ligação direta entre o circuito USB de controle e a rede elétrica. A seleção do módulo e a montagem devem manter a separação elétrica prevista pelo fabricante. O firmware não substitui isolamento, fusível/disjuntor e proteção mecânica.

## Comissionamento

1. Mantenha a rede elétrica desconectada. Grave o sketch e confira a porta COM.
2. Teste a lógica do módulo e o LED embutido, ainda sem carga de rede.
3. Cadastre o rosto, teste uma imagem nova e teste pessoas não cadastradas.
4. Execute o monitor. Confira acionamento após três confirmações e desligamento após a ausência do rosto.
5. Interrompa o processo Python mantendo o Uno alimentado e confira o desligamento pelo watchdog em até três segundos.
6. Peça ao profissional que conclua e teste a instalação da lâmpada em caixa fechada.

Durante reset ou inicialização, os pinos do Uno podem ficar em alta impedância. O projeto de hardware deve manter a entrada do módulo no estado desligado nesse intervalo, por exemplo com polarização adequada ao módulo. O sketch prepara o nível desligado antes de ativar a saída, mas não controla o período anterior ao `setup()`.

## Protocolo

Serial USB, **9600 baud**, 8N1. Comandos ASCII terminados em nova linha:

| Comando | Resposta | Ação |
| --- | --- | --- |
| `ON\n` | `ACK ON\r\n` | Liga e renova o watchdog. |
| `OFF\n` | `ACK OFF\r\n` | Desliga e renova o watchdog. |
| Outro comando | `ERR\r\n` | Ignora; não renova o watchdog. |

O watchdog desliga depois de 3000 ms sem comando válido. Não há travamento mecânico, autenticação no protocolo serial nem realimentação do estado físico dos contatos.
