# Avisa Lá 📍

Aplicativo de **lembretes contextuais**: em vez de avisar por horário, o Avisa Lá lembra você da tarefa **no lugar ou na situação certa** (ao chegar no supermercado, quando a bateria baixar, depois de acordar...).

Feito em Python com [Flet](https://flet.dev) 1.0, roda no navegador, no desktop e como app Android (APK).

## Funcionalidades

- Cadastro de lembretes com um gatilho de contexto:
  - 📍 Ao chegar no Supermercado (GPS)
  - 📍 Ao chegar no Trabalho (GPS)
  - 🔋 Quando a bateria baixar de 20%
  - ⏰ 30 minutos após acordar
- Lembretes salvos em **SQLite** (continuam ali depois de fechar o app)
- Alerta "AVISA LÁ! VOCÊ CHEGOU!" listando as tarefas do gatilho disparado
- Plano grátis com limite de **3 lembretes** e anúncio (Google AdMob)
- Plano **PRO** (simulado): sem limite e sem anúncios
- **Simulador** na própria tela para testar os gatilhos sem sair de casa

## Estado atual do projeto

Este é um protótipo. Alguns pontos ainda são simulados:

| Recurso | Situação |
|---|---|
| GPS | Simulado pelos botões do simulador (distância calculada com Haversine, raio de 100 m) |
| Bateria / acordar | Simulados pelos botões do simulador |
| Assinatura PRO | Apenas liga uma variável; falta integrar o Google Play Billing |
| Banner AdMob | Usa o **ID de teste** do Google; só aparece no APK, não no navegador |

## Tecnologias

- Python 3.12+
- [Flet](https://flet.dev) 1.0.x
- SQLite (módulo `sqlite3` da biblioteca padrão)
- [flet-ads](https://pypi.org/project/flet-ads/) (opcional, só Android/iOS)

## Estrutura

```
.
├── main.py            # app completo (interface, banco e lógica de gatilhos)
├── assets/            # logo e imagens
├── pyproject.toml     # configuração do projeto e do build
└── requirements.txt   # dependências
```

## Como rodar

```bash
git clone https://github.com/EdinaPrado/Avisa_la.git
cd Avisa_la

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

O app abre no navegador em `http://localhost:8550`.

Para acessar de outro aparelho na mesma rede Wi-Fi (por exemplo, o celular), abra `http://IP-DO-PC:8550`. No Windows com WSL2, pode ser necessário liberar a porta 8550 no firewall do Windows e do Hyper-V.

## Como gerar o APK

```bash
source .venv/bin/activate
flet build apk --arch arm64-v8a -v
```

O arquivo fica em `build/apk/`. A primeira compilação baixa o Flutter, o Android SDK e o Gradle e pode demorar bastante.

**Dicas importantes:**

- No WSL, compile a partir de uma pasta do **disco do Linux** (por exemplo `~/Avisa_la`), e não de `/mnt/c/...` ou do OneDrive. Nessas pastas o build falha por falta de permissões.
- Deixe o PC sem dormir durante o build.
- O `requirements.txt` precisa listar `flet` e `flet-ads`, senão o banner não entra no APK.

## Antes de publicar na Play Store

- [ ] Trocar o ID de teste do AdMob (`ID_BANNER_ANDROID` em `main.py`) pelo ID real
- [ ] Integrar o Google Play Billing no plano PRO
- [ ] Trocar o GPS simulado por localização real do dispositivo
- [ ] Definir ícone, nome e identificador do app no `pyproject.toml`
- [ ] Assinar o app com uma chave de release própria

## Licença

Defina a licença do projeto (por exemplo, MIT) e adicione o arquivo `LICENSE`.