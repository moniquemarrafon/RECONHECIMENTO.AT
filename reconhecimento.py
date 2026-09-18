# SISTEMA DE SEGURANÇA — Reconhecimento facial
# Responsáveis: Monique e Marcos

# Bibliotecas do Python
import logging                     # Regista tudo o que acontece no sistema
import json                        # Guarda utilizadores em ficheiro JSON
from pathlib import Path           # Gerencia caminhos de ficheiros e pastas
from datetime import datetime      # Guarda data e hora
import threading                   # Captura de vídeo e reconhecimento em paralelo

# Bibliotecas externas
import numpy as np                 # Manipulação de matrizes e imagens
import cv2                         # Captura vídeo da câmara e processamento de imagem
import insightface                 # Deteta, extrai características e reconhece rostos


# CONFIGURAÇÕES

BASE = Path(__file__).parent

LOG = BASE / "logs.txt"
JSON = BASE / "utilizadores.json"

PASTA_CONHECIDOS = BASE / "imagens" / "conhecidos"
PASTA_DESCONHECIDOS = BASE / "imagens" / "desconhecidos"


# VARIÁVEIS GLOBAIS
frame_atual = None
executando = True
resultado_atual = []
tempo_desconhecido = None


# FUNÇÕES

def criar_pastas():
    PASTA_CONHECIDOS.mkdir(parents=True, exist_ok=True)
    PASTA_DESCONHECIDOS.mkdir(parents=True, exist_ok=True)


def criar_log():
    if not LOG.exists():
        with open(LOG, "w", encoding="utf-8") as ficheiro:
            ficheiro.write("===== LOGS DO SISTEMA =====\n")
        print("Ficheiro de log criado com sucesso.")
    else:
        print("O ficheiro de log já existe.")


def criar_json():
    if not JSON.exists():
        with open(JSON, "w", encoding="utf-8") as ficheiro:
            json.dump([], ficheiro, indent=4)  # lista vazia para armazenar os utilizadores
        print("Ficheiro JSON criado com sucesso.")
    else:
        print("O ficheiro JSON já existe.")


def carregar_utilizadores():
    with open(JSON, "r", encoding="utf-8") as ficheiro:
        utilizadores = json.load(ficheiro)
    return utilizadores


def iniciar_ia():
    ia = insightface.app.FaceAnalysis()
    ia.prepare(ctx_id=-1, det_size=(320, 320))
    logging.info("InsightFace inicializado.")
    return ia


def reconhecer_utilizador(embedding, utilizadores):
    embedding = embedding / np.linalg.norm(embedding)

    melhor_nome = "Desconhecido"
    menor_distancia = float("inf")

    for utilizador in utilizadores:
        distancia = np.linalg.norm(embedding - utilizador["embedding"])

        if distancia < menor_distancia:
            menor_distancia = distancia
            melhor_nome = utilizador["nome"]

    if menor_distancia < 0.9:
        return melhor_nome

    return "Desconhecido"


def controlar_acesso(nome, ultimo_nome):
    if nome != ultimo_nome:
        ultimo_nome = nome

        if nome != "Desconhecido":
            print(f"{nome} - Acesso permitido")
            logging.info(f"Acesso permitido: {nome}")
        else:
            print("Acesso negado")
            logging.warning("Tentativa de acesso por pessoa desconhecida.")

    return ultimo_nome


def preparar_embeddings(utilizadores):
    for utilizador in utilizadores:
        utilizador["embedding"] = np.array(utilizador["embedding"], dtype=np.float32)

    return utilizadores


def reconhecer_camera(ia, utilizadores):
    global frame_atual
    global resultado_atual
    global executando

    contador = 0

    while executando:
        if frame_atual is None:
            continue

        contador = (contador + 1) % 15

        if contador != 0:
            continue

        frame = frame_atual.copy()
        pequeno = cv2.resize(frame, (320, 320))

        resultado_atual = ia.get(pequeno)


def abrir_camera(ia, utilizadores):
    global frame_atual
    global executando

    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not camera.isOpened():
        print("Erro ao abrir a câmara.")
        return

    print("Câmara aberta com sucesso.")

    thread_camera = threading.Thread(target=capturar_camera, args=(camera,), daemon=True)
    thread_camera.start()

    thread_ia = threading.Thread(target=reconhecer_camera, args=(ia, utilizadores), daemon=True)
    thread_ia.start()

    rostos = []
    ultimo_nome = ""

    while True:
        if frame_atual is None:
            cv2.waitKey(1)
            continue

        frame = frame_atual
        rostos = resultado_atual

        for rosto in rostos:
            embedding = rosto.embedding
            nome = reconhecer_utilizador(embedding, utilizadores)
            ultimo_nome = controlar_acesso(nome, ultimo_nome)

            if nome == "Desconhecido":
                salvar_desconhecido(frame)

            escala_x = frame.shape[1] / 320
            escala_y = frame.shape[0] / 320

            x1, y1, x2, y2 = rosto.bbox
            x1 = int(x1 * escala_x)
            y1 = int(y1 * escala_y)
            x2 = int(x2 * escala_x)
            y2 = int(y2 * escala_y)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame, nome, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )

            if nome != "Desconhecido":
                executando = False
                break

        cv2.imshow("Sistema de segurança", frame)
        tecla = cv2.waitKey(1)

        if not executando:
            cv2.waitKey(1000)
            break

        if tecla == ord("c") and len(rostos) > 0:
            nome = input("Nome do utilizador: ")
            registrar_utilizador(nome, frame, rostos[0])

            utilizadores = carregar_utilizadores()
            utilizadores = preparar_embeddings(utilizadores)

        if tecla == ord("q"):
            executando = False
            break

    thread_camera.join(timeout=1)
    thread_ia.join(timeout=1)

    camera.release()
    cv2.destroyAllWindows()


def capturar_camera(camera):
    global frame_atual
    global executando

    while executando:
        sucesso, frame = camera.read()

        if sucesso:
            frame_atual = frame.copy()
        cv2.waitKey(1)


def salvar_desconhecido(frame):
    global tempo_desconhecido
    global executando

    agora = datetime.now()

    if tempo_desconhecido is None:
        tempo_desconhecido = agora
        return

    diferenca = (agora - tempo_desconhecido).seconds

    if diferenca >= 10:
        nome_ficheiro = agora.strftime("desconhecido_%Y%m%d_%H%M%S.jpg")
        caminho = PASTA_DESCONHECIDOS / nome_ficheiro

        cv2.imwrite(str(caminho), frame)

        logging.warning(f"Pessoa desconhecida guardada: {nome_ficheiro}")
        print(f"Pessoa desconhecida guardada: {nome_ficheiro}")

        tempo_desconhecido = None
        executando = False


def registrar_utilizador(nome, frame, rosto):
    embedding = rosto.embedding
    embedding = embedding / np.linalg.norm(embedding)
    embedding = embedding.tolist()

    with open(JSON, "r", encoding="utf-8") as ficheiro:
        utilizadores = json.load(ficheiro)

    for utilizador in utilizadores:
        if utilizador["nome"].lower() == nome.lower():
            print("Utilizador já cadastrado.")
            return

    novo_utilizador = {
        "nome": nome,
        "foto": f"{nome}.jpg",
        "embedding": embedding
    }
    utilizadores.append(novo_utilizador)

    with open(JSON, "w", encoding="utf-8") as ficheiro:
        json.dump(utilizadores, ficheiro, indent=4, ensure_ascii=False)

    print(f"Nome: {nome}")
    print(f"Embedding possui: {len(embedding)} números.")

    caminho_imagem = PASTA_CONHECIDOS / f"{nome}.jpg"
    cv2.imwrite(str(caminho_imagem), frame)


def iniciar_sistema():
    criar_pastas()
    criar_log()

    logging.basicConfig(
        filename=LOG,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )

    logging.info("Sistema iniciado.")
    logging.info("Pastas verificadas.")

    criar_json()
    logging.info("Ficheiro json verificado.")

    ia = iniciar_ia()

    utilizadores = carregar_utilizadores()
    utilizadores = preparar_embeddings(utilizadores)

    abrir_camera(ia, utilizadores)


# PROGRAMA INICIAL

if __name__ == "__main__":
    iniciar_sistema()
