import flet as ft
import math
import os
import sqlite3

# flet-ads só funciona em Android/iOS. O import é opcional para o app
# continuar rodando no navegador/desktop mesmo sem o pacote instalado.
try:
    import flet_ads as fta
except ImportError:
    fta = None

# --- IDs DE TESTE OFICIAIS DO GOOGLE ADMOB (Android) ---
# Troque pelos seus IDs reais do AdMob antes de publicar na Play Store
ID_BANNER_ANDROID = "ca-app-pub-3940256099942544/6300978111"

# No celular, a pasta do app é somente leitura: o Flet informa a pasta de dados
# persistente em FLET_APP_STORAGE_DATA. No PC, usa a pasta do main.py.
PASTA_DADOS = os.getenv("FLET_APP_STORAGE_DATA") or os.path.dirname(os.path.abspath(__file__))
os.makedirs(PASTA_DADOS, exist_ok=True)
DB_PATH = os.path.join(PASTA_DADOS, "avisala.db")

# Coordenadas fixas de simulação para os alvos (Gatilhos)
COORDENADAS_GATILHOS = {
    "Ao chegar no Supermercado (GPS)": {"lat": -26.9150, "lon": -49.0660},
    "Ao chegar no Trabalho (GPS)": {"lat": -26.9200, "lon": -49.0750},
}

# Posições do "celular simulado" (usadas pelos botões do simulador)
POSICOES_SIMULADAS = {
    "supermercado": {"lat": -26.9151, "lon": -49.0661, "texto": "📍 GPS Atual: Próximo ao Supermercado (<50m)"},
    "trabalho": {"lat": -26.9201, "lon": -49.0751, "texto": "📍 GPS Atual: Próximo ao Trabalho (<50m)"},
    "casa": {"lat": -26.9000, "lon": -49.0500, "texto": "📍 GPS Atual: Em Casa (Longe de tudo)"},
}


# --- FUNÇÕES DO BANCO DE DADOS (SQLITE) ---
def iniciar_banco():
    """Cria o arquivo do banco de dados e a tabela se não existirem."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lembretes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarefa TEXT NOT NULL,
            contexto TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def salvar_lembrete_db(tarefa, contexto):
    """Salva um novo lembrete e retorna o ID gerado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO lembretes (tarefa, contexto) VALUES (?, ?)", (tarefa, contexto))
    conn.commit()
    id_gerado = cursor.lastrowid
    conn.close()
    return id_gerado


def carregar_lembretes_db():
    """Busca todos os lembretes salvos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, tarefa, contexto FROM lembretes ORDER BY id")
    linhas = cursor.fetchall()
    conn.close()
    return [{"id": l[0], "tarefa": l[1], "contexto": l[2]} for l in linhas]


def deletar_lembrete_db(id_lembrete):
    """Remove um lembrete pelo ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lembretes WHERE id = ?", (id_lembrete,))
    conn.commit()
    conn.close()


# --- FUNÇÃO MATEMÁTICA DO GPS ---
def calcular_distancia(lat1, lon1, lat2, lon2):
    """Distância em metros entre dois pontos (Haversine)."""
    R = 6371000  # Raio da Terra em metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# --- INTERFACE PRINCIPAL ---
def main(page: ft.Page):
    page.title = "Avisa Lá - Lembretes Contextuais"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Cria o banco (se preciso) e carrega o que já estava salvo
    iniciar_banco()
    lembretes = carregar_lembretes_db()
    is_premium = False
    gps_atual = {"lat": -26.9000, "lon": -49.0500}

    # --- ANÚNCIO ---
    def criar_anuncio():
        """Banner real do AdMob no celular; espaço reservado no navegador/desktop."""
        if fta is not None and not page.web and page.platform.is_mobile():
            return fta.BannerAd(unit_id=ID_BANNER_ANDROID)
        return ft.Text(
            "Anúncio Google AdMob - Espaço Publicitário",
            color=ft.Colors.GREY_600,
            size=11,
            text_align=ft.TextAlign.CENTER,
        )

    banner_propaganda = criar_anuncio()

    # --- COMPONENTES ---
    dlg_alerta = ft.AlertDialog(
        title=ft.Text("🚨 AVISA LÁ! VOCÊ CHEGOU!"),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Entendido, obrigado!", on_click=lambda e: page.pop_dialog()),
        ],
    )

    def fechar_dialog(e):
        page.pop_dialog()

    def assinar_premium(e):
        nonlocal is_premium
        is_premium = True
        page.pop_dialog()
        status_premium.value = "Plano: Avisa Lá PRO 💎"
        status_premium.color = ft.Colors.AMBER_400
        atualizar_lista()
        page.update()

    dlg_premium = ft.AlertDialog(
        title=ft.Text("🚀 Limite do Plano Grátis Atingido!"),
        content=ft.Text(
            "Para cadastrar mais de 3 lembretes por contexto e remover os anúncios, "
            "mude para o Avisa Lá PRO por apenas R$ 4,90/mês."
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialog),
            ft.Button(
                "Assinar PRO 💎",
                bgcolor=ft.Colors.AMBER_500,
                color=ft.Colors.BLACK,
                on_click=assinar_premium,
            ),
        ],
    )

    header = ft.Container(
        content=ft.Column(
            [
                ft.Text("Avisa Lá 📍", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_ACCENT),
                ft.Text("Nunca mais esqueça nada no lugar certo.", size=14, color=ft.Colors.GREY_400),
            ]
        ),
        padding=10,
    )

    status_premium = ft.Text("Plano: Gratuito (Limite: 3)", color=ft.Colors.GREY_500, size=12)
    texto_status_gps = ft.Text(POSICOES_SIMULADAS["casa"]["texto"], size=12, color=ft.Colors.GREY_300)

    input_tarefa = ft.TextField(
        label="O que você quer lembrar?",
        hint_text="Ex: Comprar leite, pegar chaves...",
        width=340,
    )

    texto_contexto = ft.Dropdown(
        label="Quando avisar?",
        width=340,
        options=[
            ft.DropdownOption("Ao chegar no Supermercado (GPS)"),
            ft.DropdownOption("Ao chegar no Trabalho (GPS)"),
            ft.DropdownOption("Quando a bateria baixar de 20% 🔋"),
            ft.DropdownOption("30 minutos após acordar ⏰"),
        ],
        value="Ao chegar no Supermercado (GPS)",
    )

    lista_lembretes_ui = ft.Column(spacing=10, width=340)

    # --- LÓGICA ---
    def deletar_lembrete_fluxo(id_lembrete):
        """Apaga do banco e da lista em memória, e atualiza a tela."""
        deletar_lembrete_db(id_lembrete)
        lembretes[:] = [l for l in lembretes if l["id"] != id_lembrete]
        atualizar_lista()
        page.update()

    def atualizar_lista():
        lista_lembretes_ui.controls.clear()
        for item in lembretes:
            id_atual = item["id"]
            lista_lembretes_ui.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.LOCATION_ON if "GPS" in item["contexto"] else ft.Icons.NOTIFICATIONS_ACTIVE,
                            color=ft.Colors.BLUE_200,
                        ),
                        title=ft.Text(item["tarefa"], weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(f"Gatilho: {item['contexto']}", size=12, color=ft.Colors.GREY_400),
                        trailing=ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            on_click=lambda e, id_del=id_atual: deletar_lembrete_fluxo(id_del),
                        ),
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    border_radius=10,
                    padding=5,
                )
            )
        if not is_premium:
            lista_lembretes_ui.controls.append(
                ft.Container(
                    content=banner_propaganda,
                    alignment=ft.Alignment.CENTER,
                    height=50,
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                    border_radius=5,
                    margin=ft.Margin.only(top=20),
                )
            )

    def verificar_gatilhos_gps():
        """Varre os lembretes ativos e verifica se o usuário chegou perto de algum local."""
        for item in list(lembretes):
            contexto = item["contexto"]
            if contexto in COORDENADAS_GATILHOS:
                alvo = COORDENADAS_GATILHOS[contexto]
                distancia = calcular_distancia(
                    gps_atual["lat"], gps_atual["lon"], alvo["lat"], alvo["lon"]
                )

                if distancia <= 200:  # Raio de ativação de 200 metros
                    dlg_alerta.content = ft.Text(
                        f"Lembrete ativo encontrado:\n\n👉 {item['tarefa']}\n\n"
                        f"Você está a {int(distancia)} metros do local alvo."
                    )

                    # Deleta do banco e da lista visual
                    deletar_lembrete_db(item["id"])
                    lembretes.remove(item)
                    atualizar_lista()
                    page.show_dialog(dlg_alerta)
                    page.update()
                    break

    def simular_movimento(e):
        posicao = POSICOES_SIMULADAS[e.control.data]
        gps_atual["lat"] = posicao["lat"]
        gps_atual["lon"] = posicao["lon"]
        texto_status_gps.value = posicao["texto"]
        page.update()
        verificar_gatilhos_gps()

    def adicionar_lembrete(e):
        if len(lembretes) >= 3 and not is_premium:
            page.show_dialog(dlg_premium)
            return

        if input_tarefa.value == "":
            return

        tarefa_texto = input_tarefa.value
        tipo_contexto = texto_contexto.value

        # 1. Salva no SQLite e pega o ID gerado
        id_banco = salvar_lembrete_db(tarefa_texto, tipo_contexto)

        # 2. Adiciona na lista em memória
        lembretes.append({"id": id_banco, "tarefa": tarefa_texto, "contexto": tipo_contexto})
        input_tarefa.value = ""

        atualizar_lista()
        page.update()
        verificar_gatilhos_gps()

    painel_simulador = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "🎮 Simulador de GPS (Ambiente de Testes)",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.AMBER_400,
                ),
                texto_status_gps,
                ft.Row(
                    [
                        ft.Button("Ir p/ Supermercado", data="supermercado", on_click=simular_movimento),
                        ft.Button("Ir p/ Trabalho", data="trabalho", on_click=simular_movimento),
                        ft.Button("Voltar p/ Casa", data="casa", on_click=simular_movimento),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                    wrap=True,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER_500),
        border_radius=10,
        padding=10,
        width=340,
        margin=ft.Margin.only(bottom=10),
    )

    btn_adicionar = ft.Button(
        "Criar Lembrete Inteligente",
        icon=ft.Icons.ADD_ALERT,
        on_click=adicionar_lembrete,
        width=340,
        bgcolor=ft.Colors.BLUE_ACCENT,
        color=ft.Colors.WHITE,
    )

    atualizar_lista()

    page.add(
        header,
        status_premium,
        ft.Divider(),
        painel_simulador,
        input_tarefa,
        texto_contexto,
        btn_adicionar,
        # Text não tem "padding": o espaçamento vai num Container
        ft.Container(
            content=ft.Text("Seus Lembretes Ativos:", size=16, weight=ft.FontWeight.W_600),
            padding=ft.Padding.only(top=15),
        ),
        lista_lembretes_ui,
    )


ft.run(main, view=ft.AppView.WEB_BROWSER)