# Avisa Lá 📍

> Nunca mais esqueça nada no lugar certo.

Aplicativo de **lembretes contextuais** feito em Python com [Flet](https://flet.dev). Em vez de avisar em um horário fixo, o Avisa Lá dispara o lembrete quando você **chega a um lugar** (por exemplo, o supermercado).

Projeto em desenvolvimento, criado como estudo e com o objetivo de virar um app Android.

## Funcionalidades

- Cadastro de lembretes com um gatilho de contexto (ex.: "Ao chegar no Supermercado")
- Alerta na tela quando o gatilho é ativado, com a distância até o local
- Lembretes salvos em banco **SQLite** (continuam ali depois de fechar o app)
- Simulador de GPS para testar os gatilhos sem sair de casa
- Plano gratuito (limite de 3 lembretes) e plano **PRO** (sem limite e sem anúncios)
- Banner de anúncios do **Google AdMob** no plano gratuito (apenas no celular)

## Tecnologias

| Item | Uso |
| --- | --- |
| Python 3.12 | Linguagem |
| Flet 1.0.x | Interface (web, desktop e mobile) |
| SQLite | Banco de dados local |
| flet-ads | Banner do AdMob (Android e iOS) |

## Estrutura

```
avisa-la/
├── main.py            # App completo (interface, banco e lógica de GPS)
├── requirements.txt   # Dependências (flet, flet-ads)
└── README.md
```

## Como rodar no navegador

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flet run --web main.py
```

O terminal mostra um endereço parecido com `http://127.0.0.1:PORTA`. Abra no navegador (a porta muda a cada execução).

> **WSL:** as mensagens `xdg-open: not found` são só o aviso de que não há navegador para abrir sozinho. Copie o endereço e abra no navegador do Windows.
>
> Use `--web`. Sem essa opção, o `flet run` tenta abrir uma janela desktop e baixar o cliente do Flet, o que falha em redes com proxy.

No navegador, o espaço do banner aparece como um bloco de texto "Anúncio Google AdMob". O anúncio real só é exibido no app instalado no celular.

## Como testar o GPS

1. Crie um lembrete com o gatilho **"Ao chegar no Supermercado (GPS)"**.
2. No painel **Simulador de GPS**, clique em **Ir p/ Supermercado**.
3. O alerta 🚨 aparece com o lembrete e a distância, e o item é removido da lista e do banco.

O gatilho dispara a até **200 metros** do local, com a distância calculada pela fórmula de Haversine. As coordenadas dos locais estão em `COORDENADAS_GATILHOS`, no início do `main.py`.

## Gerar o APK (Android)

```bash
flet build apk --android-meta-data com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-3940256099942544~3347511713
```

- O `flet-ads` precisa estar no `requirements.txt` para entrar no APK.
- O `APPLICATION_ID` acima é o **ID de teste do Google**. Sem ele, o app com anúncios pode fechar ao abrir.
- O APK sai em `build/apk/`.
- No celular, o banco fica na pasta de dados do app (variável `FLET_APP_STORAGE_DATA`). No PC, fica ao lado do `main.py` (`avisala.db`).

A primeira compilação baixa JDK, Flutter e Android SDK e pode levar bastante tempo. Ela usa vários GB de disco e de memória.

## Problemas comuns

**`CERTIFICATE_VERIFY_FAILED` ao baixar o JDK ou o Flutter**
O Python não confia no certificado da rede (comum em rede de escola ou empresa). Use o pacote de certificados do `certifi` no terminal atual:

```bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
```

**O build trava ou o computador fica lento (WSL)**
- Rode o projeto dentro do WSL (`~/avisa-la`), e não em `/mnt/c/...` nem na pasta do OneDrive.
- Limite a memória do Gradle e do Kotlin em `~/.gradle/gradle.properties`:

  ```
  org.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=1g
  kotlin.daemon.jvmargs=-Xmx2g
  ```
- Se precisar, aumente a memória do WSL em `C:\Users\SEU_USUARIO\.wslconfig` e rode `wsl --shutdown` em seguida.
- Rode o build em segundo plano e acompanhe pelo log, assim fechar o terminal não interrompe nada:

  ```bash
  nohup flet build apk ... > build.log 2>&1 &
  tail -f build.log
  ```

**`module 'flet' has no attribute 'app'` (ou `colors`, `icons`)**
Código escrito para uma versão antiga do Flet. Na 1.0 use `ft.run(...)`, `ft.Colors`, `ft.Icons`, `page.show_dialog(...)` e `page.pop_dialog()`.

## Limitações atuais

- **GPS simulado.** A localização vem dos botões do simulador, não do aparelho.
- **Só os gatilhos de GPS funcionam.** As opções "bateria abaixo de 20%" e "30 minutos após acordar" existem na lista, mas ainda não têm lógica de disparo.
- **Plano PRO de demonstração.** O botão "Assinar PRO" só altera o estado na tela, não há cobrança real.
- **O estado do PRO não é salvo.** Ao reabrir o app, ele volta ao plano gratuito.
- **Anúncios de teste.** Os IDs do AdMob no código são os IDs públicos de teste do Google.

## Próximos passos

- [ ] Usar a localização real do aparelho (geolocalização e permissões)
- [ ] Avisar com o app fechado (execução em segundo plano)
- [ ] Implementar os gatilhos de bateria e de horário
- [ ] Cobrança real do plano PRO (Google Play Billing) e persistência da assinatura
- [ ] Trocar os IDs de teste do AdMob pelos IDs reais
- [ ] Gerar o pacote `.aab` assinado e publicar na Google Play (exige política de privacidade)

> **Segurança:** nunca suba para o repositório chaves de assinatura do app (`.jks`, `.keystore`) nem senhas.
