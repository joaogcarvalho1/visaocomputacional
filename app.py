"""Cadastro e verificação de rosto. O monitor local controla o Arduino."""

from pathlib import Path

import streamlit as st

from vision.faces import MAX_SAMPLES, MIN_SAMPLES, FaceEngine, decode_image

st.set_page_config(page_title="FaceLight · Visão computacional", page_icon="💡", layout="wide")
st.markdown(
    """
<style>
.block-container {max-width: 1200px; padding-top: 2rem;}
h1 {letter-spacing: -0.045em;}
[data-testid="stMetric"] {background: #edf2ec; padding: 16px; border-radius: 12px;}
.eyebrow {letter-spacing: .16em; font-size: .75rem; font-weight: 700; color: #167d59;}
</style><div class="eyebrow">FACELIGHT / VISÃO COMPUTACIONAL + ARDUINO</div>
""",
    unsafe_allow_html=True,
)
st.title("Seu rosto acende a luz.")
st.write("Cadastre uma pessoa, confira o reconhecimento e conecte o Arduino Uno ao relé.")

with st.sidebar:
    st.header("💡 FaceLight")
    st.caption("OpenCV · Arduino Uno · Relé 5 V")
    st.divider()
    page = st.radio(
        "Etapa", ["1 · Cadastrar rosto", "2 · Testar reconhecimento", "3 · Acionar lâmpada"]
    )
    threshold = st.slider(
        "Limite de reconhecimento LBPH",
        20,
        120,
        65,
        help="Menor = mais rigoroso. É uma distância, não uma porcentagem.",
    )
    st.caption(
        "O limite escolhido aqui vale para o teste. Copie o comando na etapa 3 para o monitor."
    )

engine = FaceEngine(Path("data"), threshold)
count = len(engine.samples)
metrics = st.columns(3)
count_metric = metrics[0].empty()
status_metric = metrics[1].empty()
count_metric.metric("FOTOS CADASTRADAS", count)
status_metric.metric("CADASTRO", "Pronto para testar" if count >= MIN_SAMPLES else "Em preparação")
metrics[2].metric("CONTROLE FÍSICO", "Monitor local")
st.write("")

if page == "1 · Cadastrar rosto":
    st.subheader("01 / Cadastre o rosto autorizado")
    st.write(
        "Use fotos da mesma pessoa, com autorização dela. Capture de 5 a 20 imagens "
        "frontais, variando levemente a pose e a iluminação. Apenas um rosto por foto."
    )
    method = st.radio(
        "Como adicionar fotos?", ["Enviar fotos", "Câmera do navegador"], horizontal=True
    )
    files = []
    if method == "Enviar fotos":
        files = st.file_uploader(
            "Fotos JPEG, PNG ou WebP · até 10 MB cada",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
    else:
        capture = st.camera_input("Capture uma foto frontal")
        if capture:
            files = [capture]
    if st.button("Adicionar ao cadastro", type="primary", disabled=not files):
        added = 0
        for file in files:
            try:
                engine.enroll(decode_image(file.getvalue()))
                added += 1
            except (ValueError, OSError) as error:
                st.warning(f"{file.name}: {error}")
        if added:
            count = len(engine.samples)
            count_metric.metric("FOTOS CADASTRADAS", count)
            status_metric.metric(
                "CADASTRO", "Pronto para testar" if count >= MIN_SAMPLES else "Em preparação"
            )
            st.success(f"{added} foto(s) adicionada(s). Total: {count}.")
            st.caption("Siga para a etapa 2 para testar com uma foto diferente das cadastradas.")
    st.caption(
        f"As amostras ficam em data/samples no computador/servidor que executa o app. "
        f"Máximo de {MAX_SAMPLES} fotos. Essa pasta está excluída do Git."
    )
    with st.expander("Excluir cadastro"):
        st.write(
            "Pare o monitor antes de excluir: ele mantém o modelo carregado até ser reiniciado."
        )
        confirmed = st.checkbox("Quero excluir todas as fotos cadastradas")
        if st.button("Excluir fotos", disabled=not confirmed):
            engine.clear()
            st.rerun()

elif page == "2 · Testar reconhecimento":
    st.subheader("02 / Confira antes de conectar a lâmpada")
    if count < MIN_SAMPLES:
        st.info(f"Cadastre pelo menos {MIN_SAMPLES} fotos na etapa 1 para começar.")
    else:
        st.write(
            "Use uma foto nova da pessoa cadastrada e depois teste outra pessoa. "
            "Ajuste o limite para reduzir aceitações indevidas."
        )
        method = st.radio("Fonte do teste", ["Enviar foto", "Câmera do navegador"], horizontal=True)
        photo = (
            st.file_uploader("Foto para teste", type=["jpg", "jpeg", "png", "webp"])
            if method == "Enviar foto"
            else st.camera_input("Foto para teste")
        )
        if photo:
            try:
                frame = decode_image(photo.getvalue())
                result = engine.recognize(frame)
                st.image(frame, channels="BGR", width=520)
                messages = {
                    "recognized": (
                        "Rosto reconhecido. Confirmações consecutivas no monitor acionam a lâmpada."
                    ),
                    "unknown": (
                        "Rosto não reconhecido. Esta imagem não autoriza um novo acionamento."
                    ),
                    "no_face": (
                        "Nenhum rosto frontal encontrado. Melhore a iluminação e aproxime-se."
                    ),
                    "multiple_faces": (
                        "Mais de um rosto encontrado. Deixe apenas a pessoa testada na imagem."
                    ),
                }
                (st.success if result.matched else st.warning)(messages[result.status])
                if result.distance is not None:
                    st.metric(
                        "Distância LBPH · menor significa mais parecido", f"{result.distance:.1f}"
                    )
            except (ValueError, OSError) as error:
                st.error(str(error))
    st.info("Esta tela testa fotos; o controle contínuo do relé é feito pelo monitor da etapa 3.")

else:
    st.subheader("03 / Conecte o Arduino no Windows")
    st.markdown(
        "1. Grave `arduino/face_lamp/face_lamp.ino` no Uno pela Arduino IDE.\n"
        "2. Feche o Monitor Serial da IDE e libere a câmera do navegador.\n"
        "3. Na pasta do projeto, liste as portas e execute o monitor abaixo."
    )
    st.code("uv run python -m vision.monitor --list-ports", language="powershell")
    st.code(
        f"uv run python -m vision.monitor --port COM3 --threshold {threshold}",
        language="powershell",
    )
    st.caption("Substitua COM3 pela porta do seu Uno. Instalação sem uv: consulte o README.")
    st.markdown("**Teste com a webcam, sem Arduino:**")
    st.code(
        f"uv run python -m vision.monitor --simulate --threshold {threshold}", language="powershell"
    )
    st.write(
        "O monitor exige 3 reconhecimentos consecutivos. A luz apaga 5 segundos após "
        "o último reconhecimento confirmado. Ctrl+C encerra e envia o desligamento."
    )
    st.warning(
        "A nuvem não acessa o USB do seu PC. Execute o cadastro e o monitor no Windows "
        "conectado à câmera e ao Arduino. Não execute dois monitores simultâneos."
    )
    st.info(
        "Lâmpada de 127/220 V: a instalação elétrica deve ser feita por profissional "
        "qualificado, com isolamento, proteção e relé adequado à carga. Consulte docs/hardware.md."
    )

st.divider()
st.caption(
    "Protótipo didático para iluminação. LBPH pode confundir pessoas e aceitar fotos; "
    "não possui detecção de presença real. Use com supervisão e calibre no local."
)
