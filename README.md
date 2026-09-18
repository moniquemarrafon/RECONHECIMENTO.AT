# Sistema de Segurança — Reconhecimento Facial

Sistema de segurança em tempo real desenvolvido em Python, que usa a câmara para detetar,
reconhecer e controlar o acesso de utilizadores através do rosto.

---

## O que faz

O sistema abre a câmara e, em tempo real:

1. **Deteta rostos** no vídeo, usando o modelo `buffalo_l` do InsightFace
2. **Extrai o embedding** (assinatura numérica) de cada rosto detetado
3. **Reconhece o utilizador**, comparando o embedding com os utilizadores guardados em `utilizadores.json` (distância euclidiana, limiar de 0.9)
4. **Regista o acesso** — permitido ou negado — no ficheiro `logs.txt`
5. **Guarda imagens de pessoas desconhecidas** que permaneçam à frente da câmara mais de 10 segundos, em `imagens/desconhecidos/`
6. Permite **registar novos utilizadores** em tempo real, pressionando `c` durante a deteção

---

## Tecnologias utilizadas

- Python 3.x
- OpenCV (`cv2`) — captura de vídeo e processamento de imagem
- InsightFace — deteção facial e extração de embeddings
- NumPy — cálculo de distâncias entre embeddings
- `threading` — captura de vídeo e reconhecimento em paralelo, para manter a interface fluida

---

## Estrutura do projeto

```
RECONHECIMENTO.AT/
├── reconhecimento.py     → sistema principal (deteção, reconhecimento, registo, logs)
├── requirements.txt
├── imagens/
│   ├── conhecidos/       → fotos dos utilizadores registados (gerado em runtime)
│   └── desconhecidos/    → capturas de pessoas não reconhecidas (gerado em runtime)
├── utilizadores.json     → base de dados de utilizadores e embeddings (gerado em runtime)
└── logs.txt              → registo de acessos (gerado em runtime)
```

> As pastas e ficheiros gerados em runtime não são versionados (ver `.gitignore`) porque
> contêm dados pessoais — fotos e embeddings de rostos reais. São criados automaticamente
> na primeira execução.

---

## Instalação

### 1. Instalar Python
Descarrega em: https://www.python.org/downloads/
Durante a instalação, marca **"Add Python to PATH"**

### 2. Criar ambiente virtual
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as bibliotecas
```bash
python -m pip install -r requirements.txt
```

---

## Como correr

```bash
python reconhecimento.py
```

- Na primeira execução, o InsightFace descarrega automaticamente o modelo `buffalo_l`.
- Com a câmara aberta:
  - Pressiona **`c`** para registar um novo utilizador (com um rosto visível na câmara)
  - Pressiona **`q`** para sair
- Utilizadores reconhecidos aparecem com o nome sobre o rosto e o acesso é registado como permitido.
- Rostos não reconhecidos são marcados como acesso negado e, se persistirem, a imagem é guardada em `imagens/desconhecidos/`.

---

## Aviso

Este projeto foi desenvolvido para fins educativos, como demonstração de um sistema de
controlo de acesso por reconhecimento facial. Antes de o usar com dados de pessoas reais,
garante que tens o consentimento delas — o sistema guarda fotos e embeddings faciais, que
são dados biométricos sensíveis (ex. RGPD).

---

## Autoras/Autores

Monique Marrafon e Marcos
