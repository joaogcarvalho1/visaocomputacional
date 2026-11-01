"""Guia do monitor automático. A webcam e o Arduino são usados pelo monitor local."""

import re

import streamlit as st

st.set_page_config(page_title="FaceLight · Controle automático", page_icon="💡", layout="centered")
st.title("Um rosto presente. A luz acende.")
st.write("A webcam detecta rostos continuamente, sem cadastro e sem precisar tirar fotos.")
st.info(
    "Esta página é o guia. Execute o monitor no terminal do VS Code para ativar a webcam "
    "e controlar o Arduino conectado ao seu computador."
)

st.subheader("1 · Prepare o Arduino")
st.markdown(
    "Abra `arduino/face_lamp/face_lamp.ino` na Arduino IDE, selecione **Arduino Uno** "
    "e a porta correta e clique em **Carregar**. Depois feche o Monitor Serial da IDE."
)
st.caption("O sketch usa D8 para o módulo relé 5 V, ativo em LOW por padrão.")

st.subheader("2 · Inicie no VS Code")
st.write("Abra o terminal na pasta do projeto. Feche outros aplicativos que usem a webcam.")
st.code(r".\.venv\Scripts\python.exe -m vision.monitor --list-ports", language="powershell")
port = st.text_input("Porta do Arduino", value="COM3").strip().upper()
on_delay = st.number_input("Segundos contínuos com rosto para ligar", min_value=0, value=5)
off_delay = st.number_input("Segundos contínuos sem rosto para desligar", min_value=0, value=5)
if re.fullmatch(r"COM[1-9][0-9]*", port):
    st.code(
        rf".\.venv\Scripts\python.exe -m vision.monitor --port {port} "
        f"--on-delay {on_delay} --off-delay {off_delay}",
        language="powershell",
    )
else:
    st.warning("Informe uma porta Windows válida, como COM3 ou COM4.")
st.caption("Os controles acima montam o comando. Copie-o para o terminal para aplicá-los.")

st.subheader("3 · Deixe funcionar automaticamente")
st.write(
    "Qualquer rosto detectado mantém a contagem para ligar. Sem nenhum rosto, começa "
    "a contagem para desligar. Se a condição mudar, a contagem pendente reinicia."
)
st.write(
    "O monitor lê a webcam em tempo real e mostra o estado no terminal. "
    "Ctrl+C encerra o programa e desliga a saída imediatamente."
)
with st.expander("Testar a webcam sem Arduino"):
    st.code(r".\.venv\Scripts\python.exe -m vision.monitor --simulate", language="powershell")
st.warning(
    "Lâmpada de 127/220 V: a parte da rede elétrica deve ser montada por profissional "
    "qualificado. Consulte docs/hardware.md."
)
st.caption(
    "A nuvem não acessa a webcam nem o USB do Windows. O programa não salva imagens. "
    "O detector pode aceitar fotos de rostos; este é um protótipo para iluminação."
)
