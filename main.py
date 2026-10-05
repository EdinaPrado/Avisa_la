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

LIMITE_GRATIS = 3
RAIO_ALERTA_METROS = 100

# No celular, a pasta do app é somente leitura: o Flet informa a pasta de dados
# persistente em FLET_APP_STORAGE_DATA. No PC, usa a pasta do main.py.
PASTA_DADOS = os.getenv("FLET_APP_STORAGE_DATA") or os.path.dirname(os.path.abspath(__file__))
os.makedirs(PASTA_DADOS, exist_ok=True)
DB_PATH = os.path.join(PASTA_DADOS, "avisala.db")

# Contextos disponíveis
CTX_SUPERMERCADO = "Ao chegar no Supermercado (GPS)"
CTX_TRABALHO = "Ao chegar no Trabalho (GPS)"
CTX_BATERIA = "Quando a bateria baixar de 20% 🔋"
CTX_ACORDAR = "30 minutos após acordar ⏰"

# Coordenadas fixas de simulação para os alvos (Gatilhos)
COORDENADAS_GATILHOS = {
    CTX_SUPERMERCADO: {"lat": -26.9150, "lon": -49.0660},
    CTX_TRABALHO: {"lat": -26.9200, "lon": -49.0750},
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
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # Cria o banco (se preciso) e carrega o que já estava salvo
    iniciar_banco()
    lembretes = carregar_lembretes_db()
    is_premium = False
    gps_atual = {"lat": POSICOES_SIMULADAS["casa"]["lat"], "lon": POSICOES_SIMULADAS["casa"]["lon"]}

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

    # --- DIÁLOGOS ---
    def fechar_dialog(e):
        page.pop_dialog()

    dlg_alerta = ft.AlertDialog(
        title=ft.Text("🚨 AVISA LÁ! VOCÊ CHEGOU!"),
        content=ft.Text(""),
        actions=[ft.TextButton("Entendido, obrigado!", on_click=fechar_dialog)],
    )

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
            f"Para cadastrar mais de {LIMITE_GRATIS} lembretes e remover os anúncios, "
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

    # --- COMPONENTES ---
    header = ft.Container(
        content=ft.Column(
            [
                ft.Text("Avisa Lá 📍", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_ACCENT),
                ft.Text("Nunca mais esqueça nada no lugar certo.", size=14, color=ft.Colors.GREY_400),
            ]
        ),
        padding=10,
    )

    status_premium = ft.Text(f"Plano: Gratuito (Limite: {LIMITE_GRATIS})", color=ft.Colors.GREY_500, size=12)
    texto_status_gps = ft.Text(POSICOES_SIMULADAS["casa"]["texto"], size=12, color=ft.Colors.GREY_300)

    input_tarefa = ft.TextField(
        label="O que você quer lembrar?",
        hint_text="Ex: Comprar leite, pegar chaves...",
        width=340,
    )

    dropdown_contexto = ft.Dropdown(
        label="Quando avisar?",
        width=340,
        options=[
            ft.DropdownOption(CTX_SUPERMERCADO),
            ft.DropdownOption(CTX_TRABALHO),
            ft.DropdownOption(CTX_BATERIA),
            ft.DropdownOption(CTX_ACORDAR),
        ],
        value=CTX_SUPERMERCADO,
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
        """Redesenha a lista. Quem chama é responsável por page.update()."""
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
                ft.Row([banner_propaganda], alignment=ft.MainAxisAlignment.CENTER)
            )

    def adicionar_lembrete(e):
        tarefa = (input_tarefa.value or "").strip()
        contexto = dropdown_contexto.value

        if not tarefa:
            input_tarefa.error_text = "Escreva o que você quer lembrar"
            page.update()
            return
        input_tarefa.error_text = None

        if not is_premium and len(lembretes) >= LIMITE_GRATIS:
            page.show_dialog(dlg_premium)
            return

        novo_id = salvar_lembrete_db(tarefa, contexto)
        lembretes.append({"id": novo_id, "tarefa": tarefa, "contexto": contexto})
        input_tarefa.value = ""
        atualizar_lista()
        page.update()

    def avisar(tarefas):
        """Abre o alerta listando as tarefas disparadas."""
        dlg_alerta.content = ft.Column(
            [ft.Text(f"• {t}") for t in tarefas],
            tight=True,
        )
        page.show_dialog(dlg_alerta)

    def verificar_gps():
        """Dispara os lembretes de GPS cujo alvo está a menos de RAIO_ALERTA_METROS."""
        tarefas = []
        for item in lembretes:
            alvo = COORDENADAS_GATILHOS.get(item["contexto"])
            if not alvo:
                continue
            dist = calcular_distancia(gps_atual["lat"], gps_atual["lon"], alvo["lat"], alvo["lon"])
            if dist <= RAIO_ALERTA_METROS:
                tarefas.append(item["tarefa"])
        if tarefas:
            avisar(tarefas)
        else:
            page.update()

    def mover_para(chave):
        pos = POSICOES_SIMULADAS[chave]
        gps_atual["lat"] = pos["lat"]
        gps_atual["lon"] = pos["lon"]
        texto_status_gps.value = pos["texto"]
        page.update()
        verificar_gps()

    def disparar_contexto(contexto):
        tarefas = [l["tarefa"] for l in lembretes if l["contexto"] == contexto]
        if tarefas:
            avisar(tarefas)

    botao_adicionar = ft.Button(
        "Adicionar lembrete",
        icon=ft.Icons.ADD,
        width=340,
        on_click=adicionar_lembrete,
    )

    # --- SIMULADOR ---
    simulador = ft.Container(
        content=ft.Column(
            [
                ft.Text("🧪 Simulador", size=14, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.OutlinedButton("Supermercado", on_click=lambda e: mover_para("supermercado")),
                        ft.OutlinedButton("Trabalho", on_click=lambda e: mover_para("trabalho")),
                        ft.OutlinedButton("Casa", on_click=lambda e: mover_para("casa")),
                    ],
                    wrap=True,
                    spacing=8,
                ),
                ft.Row(
                    [
                        ft.OutlinedButton("🔋 Bateria 19%", on_click=lambda e: disparar_contexto(CTX_BATERIA)),
                        ft.OutlinedButton("⏰ Acordei", on_click=lambda e: disparar_contexto(CTX_ACORDAR)),
                    ],
                    wrap=True,
                    spacing=8,
                ),
            ],
            spacing=8,
        ),
        width=340,
        padding=10,
        border=ft.Border.all(1, ft.Colors.GREY_700),
        border_radius=10,
    )

    atualizar_lista()
    page.add(
        header,
        status_premium,
        texto_status_gps,
        input_tarefa,
        dropdown_contexto,
        botao_adicionar,
        lista_lembretes_ui,
        simulador,
    )


# No Flet 1.0 o ft.app() foi removido: use ft.run().
# No PC/WSL abre no navegador; no APK (flet build) o Flet usa o main() direto.
if __name__ == "__main__":
     ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8550)