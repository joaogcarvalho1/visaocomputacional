# FaceLight — lâmpada automática por detecção de rosto

O programa lê a webcam continuamente. **Qualquer rosto detectado por 5 segundos contínuos liga a lâmpada. Cinco segundos contínuos sem nenhum rosto desligam a lâmpada.** Se a condição mudar antes de completar o atraso, a contagem reinicia.

Não é necessário cadastrar pessoas, tirar fotos ou clicar em capturar. O programa não identifica quem é a pessoa e não salva imagens. Um ou vários rostos têm o mesmo efeito de presença.

## O que roda em cada lugar

- **VS Code / computador Windows:** Python lê a webcam, detecta rostos e conta os atrasos.
- **Arduino IDE:** serve para gravar o sketch no Uno. Feche o Monitor Serial antes de iniciar Python.
- **Arduino Uno:** recebe os comandos USB e controla o módulo relé 5 V pelo pino D8.
- **Módulo relé:** aciona a lâmpada. Para 127/220 V, a montagem deve ser feita por profissional qualificado; consulte [hardware](docs/hardware.md).

O computador deve permanecer ligado com o programa em execução. Não é necessária GPU ou API externa.

## 1. Abrir no VS Code e instalar

Abra a pasta que contém este README em **Arquivo → Abrir Pasta**. Abra **Terminal → Novo Terminal** e execute, um comando por vez:

```powershell
py install 3.12
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.txt
```

O primeiro comando usa o Python Install Manager atual. Se o seu launcher não oferecer `py install`, instale o Python 3.12 de 64 bits pelo site oficial. Se o Python 3.12 já estiver instalado, comece pelo segundo comando.

**Atualizando a versão anterior:** baixe o ZIP da branch `feat/facelight`, extraia e copie os arquivos de dentro da pasta extraída para a pasta atual do projeto, substituindo os arquivos antigos. Preserve sua pasta `.venv`; as dependências são as mesmas. O cadastro antigo em `data/` não é mais utilizado e não será apagado automaticamente.

## 2. Gravar o Arduino Uno

1. Conecte o Uno ao PC por USB.
2. Abra `arduino/face_lamp/face_lamp.ino` na **Arduino IDE**.
3. Selecione **Arduino Uno** e a porta correta em **Ferramentas → Porta**.
4. Clique em **Carregar** e aguarde a conclusão.
5. Feche o **Monitor Serial** e o **Plotter Serial** para liberar a porta ao Python.

O sketch usa módulo **ativo em LOW** no pino D8. Para módulo ativo em HIGH, altere `RELAY_ACTIVE_LOW` para `false` antes de gravar. O mesmo sketch da versão anterior continua válido.

## 3. Rodar automaticamente

Feche o aplicativo antigo de cadastro com **Ctrl+C** no terminal. Libere a webcam fechando capturas no navegador, Teams ou outros programas.

No terminal do VS Code, na pasta do projeto, descubra a porta:

```powershell
.\.venv\Scripts\python.exe -m vision.monitor --list-ports
```

Substitua **COM3** abaixo pela porta do Uno exibida na lista ou na Arduino IDE:

```powershell
.\.venv\Scripts\python.exe -m vision.monitor --port COM3
```

Pronto: a webcam é lida automaticamente em tempo real. O programa mostra no terminal quantos rostos detectou e o estado solicitado para a lâmpada. Não abre uma janela de vídeo nem exige interação pelo navegador. Mantenha o terminal aberto.

Os dois atrasos já são **5 segundos**. Para deixá-los explícitos no comando:

```powershell
.\.venv\Scripts\python.exe -m vision.monitor --port COM3 --on-delay 5 --off-delay 5
```

- Rosto começa a aparecer em `0 s`: a luz liga em aproximadamente `5 s`, se a detecção continuar.
- Todos os rostos somem em `10 s`: a luz apaga em aproximadamente `15 s`, se ninguém reaparecer.
- Se o rosto some antes de ligar, a contagem de ligar reinicia. Se reaparece antes de desligar, a contagem de desligar é cancelada.
- A atualização ocorre a cada quadro processado. Falhas momentâneas na detecção podem reiniciar o atraso.

**Ctrl+C** encerra o programa e envia o desligamento imediatamente, sem aguardar os cinco segundos. Erros de câmera/serial também encerram e tentam desligar. Se Python travar ou desconectar, o watchdog do Uno desliga em até **3 segundos sem comando válido**, enquanto estiver alimentado. Esse watchdog é separado dos atrasos normais de presença/ausência.

## Testar sem Arduino

```powershell
.\.venv\Scripts\python.exe -m vision.monitor --simulate
```

Usa a webcam de verdade e simula o relé no terminal com os mesmos atrasos. Para outra câmera, acrescente `--camera 1`. Teste inicialmente com a rede elétrica da lâmpada desconectada.

## Guia opcional no navegador

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Essa página apenas explica o uso e monta os comandos para o terminal. O monitor automático não depende dela.

## Problemas comuns

| Problema | O que fazer |
| --- | --- |
| Ainda aparece a tela de cadastro | Atualize os arquivos do ZIP e reinicie o processo. Use o comando `vision.monitor` acima. |
| Nenhum rosto detectado | Ilumine o rosto de frente, olhe para a câmera e aproxime-se. O detector procura rostos frontais de pelo menos 80 × 80 pixels. |
| A contagem nunca completa | Verifique no terminal se a detecção oscila entre zero e um rosto. Melhore iluminação e posição para manter a detecção por cinco segundos. |
| Câmera indisponível | Feche outros programas que a usam e teste `--camera 1`. |
| Porta COM não abre | Feche Monitor Serial/Plotter, confira cabo USB de dados e selecione a COM correta. |
| Arduino não confirma | Grave o sketch correto; o protocolo usa 9600 baud. |
| Relé invertido | Confira o modo LOW/HIGH e a montagem do módulo. |

É um protótipo para iluminação: o detector pode falhar com perfil, pouca luz ou obstrução e pode detectar uma foto de rosto. Não comprova identidade ou presença de uma pessoa real.

## Desenvolvimento e nuvem

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

O ambiente na nuvem executa os testes e o guia, mas não acessa a webcam nem o USB do Windows. Rode o monitor no PC conectado ao Arduino. O teste de firmware compila o sketch real com GPIO, relógio e serial simulados usando `g++`; não substitui compilação AVR e teste físico na placa.

`requirements.txt` contém versões e hashes exportados de `uv.lock`. Para regenerá-lo após atualizar dependências: `uv export --locked --no-dev --format requirements-txt --output-file requirements.txt --quiet`. Veja [a validação realizada](docs/validation.md).
