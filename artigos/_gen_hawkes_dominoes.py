"""
Gera artigos/hawkes_dominoes.gif com 3 paineis sincronizados:
  1. lambda(t) — intensidade do processo de Hawkes ao longo do tempo
  2. fileira de dominos — cada saque derruba um domino, com cascata visivel
  3. caixa + HQLA monetizavel — curva descendente que cruza o piso B em tau

Cenario pedagogico:
  - 0h..8h:  regime estavel    mu=2/h,  alpha=0.3, beta=5/h  -> alpha/beta = 0.06
  - 8h..24h: regime de cascata mu=2/h,  alpha=1.5, beta=2/h  -> alpha/beta = 0.75
  Em t=8h ha um "evento de noticia" injetado.

Algoritmo: thinning de Ogata.
Reprodutivel via seed fixa.

Justificativa para Python (em vez de Julia, conforme skill pq-deep-research):
  Os demais scripts de geracao de figura do projeto sao Python+Selenium e
  Julia nao esta instalado neste host. matplotlib.FuncAnimation entrega GIF
  diretamente, sem dependencia adicional.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.transforms import Affine2D

# ---------- Parametros do cenario ----------
SEED = 20260504
T_TOTAL = 24.0          # horas simuladas
T_REGIME_SHIFT = 8.0    # instante de mudanca de regime (evento de noticia)
DT_FRAME = 0.10         # passo de tempo por frame (h)
FPS = 10

MU = 2.0                # saques/hora basais
ALPHA_LOW, BETA_LOW = 0.30, 5.0    # regime estavel  -> alpha/beta = 0.06
ALPHA_HIGH, BETA_HIGH = 1.50, 2.0  # regime cascata  -> alpha/beta = 0.75

# Caixa e piso operacional (unidades arbitrarias, ex.: % do funding)
C0 = 100.0              # caixa + reservas iniciais
HQLA_MONETIZAVEL = 30.0 # buffer adicional disponivel
B_PISO = 25.0           # colchao minimo Bt
SAQUE_MEDIO = 3.0       # tamanho medio de cada saque (mesma unidade)

# Cores (alinhadas com a paleta do projeto: laranja #FF6719 sobre grafite)
COR_LARANJA = "#ff6719"
COR_LARANJA_CLARO = "#ffb27a"
COR_GRAFITE = "#1f2933"
COR_CINZA = "#9aa5b1"
COR_CINZA_CLARO = "#e6e6f0"
COR_AZUL = "#1e3a8a"
COR_FUNDO = "#fafaf7"


@dataclass
class Evento:
    t: float
    volume: float


def alpha_beta(t: float) -> tuple[float, float]:
    if t < T_REGIME_SHIFT:
        return ALPHA_LOW, BETA_LOW
    return ALPHA_HIGH, BETA_HIGH


def intensidade(t: float, eventos: list[Evento]) -> float:
    """lambda(t) = mu + sum alpha * exp(-beta (t - ti))"""
    a, b = alpha_beta(t)
    soma = 0.0
    for ev in eventos:
        if ev.t < t:
            soma += a * math.exp(-b * (t - ev.t))
    return MU + soma


def simular_hawkes() -> list[Evento]:
    """Thinning de Ogata adaptado a parametros variaveis no tempo.

    A simulacao para quando o caixa disponivel (C0 + HQLA monetizavel) se exaure:
    o banco nao consegue mais honrar saques, a demanda pode continuar mas as
    realizacoes param. Pedagogicamente, esse instante eh o fim da historia.
    """
    rng = random.Random(SEED)
    eventos: list[Evento] = []
    cum_outflow = 0.0
    caixa_total = C0 + HQLA_MONETIZAVEL
    t = 0.0
    while t < T_TOTAL:
        a, b = alpha_beta(t)
        lam_max = MU + a / max(b, 1e-6) * 5.0
        lam_max = max(lam_max, intensidade(t, eventos) * 1.5, 5.0)
        u = rng.random()
        delta = -math.log(max(u, 1e-12)) / lam_max
        t = t + delta
        if t >= T_TOTAL:
            break
        if not any(abs(ev.t - T_REGIME_SHIFT) < 1e-6 for ev in eventos) and t > T_REGIME_SHIFT:
            volume = SAQUE_MEDIO * 3.5
            eventos.append(Evento(t=T_REGIME_SHIFT, volume=volume))
            cum_outflow += volume
            if cum_outflow >= caixa_total:
                break
            continue
        lam = intensidade(t, eventos)
        if rng.random() <= lam / lam_max:
            base = SAQUE_MEDIO if t < T_REGIME_SHIFT else SAQUE_MEDIO * 1.4
            volume = base * (0.6 + rng.random() * 0.9)
            # se o proximo saque esvaziaria o caixa, ajusta volume para zerar
            # exatamente e encerra
            if cum_outflow + volume > caixa_total:
                volume = caixa_total - cum_outflow
                if volume > 1e-3:
                    eventos.append(Evento(t=t, volume=volume))
                    cum_outflow += volume
                break
            eventos.append(Evento(t=t, volume=volume))
            cum_outflow += volume
    return eventos


# ---------- Construcao da animacao ----------

def main() -> None:
    eventos = simular_hawkes()
    eventos_sorted = sorted(eventos, key=lambda e: e.t)
    t_ultimo = eventos_sorted[-1].t if eventos_sorted else 0.0
    # encerra a animacao 1.5h depois do ultimo saque honrado, para mostrar
    # claramente o "banco quebrou" sem cauda vazia
    t_fim = min(T_TOTAL, max(t_ultimo + 1.5, T_REGIME_SHIFT + 4.0))
    print(f"[hawkes] simulados {len(eventos)} saques; ultimo em {t_ultimo:.2f}h; janela exibida ate {t_fim:.2f}h")

    n_frames = int(t_fim / DT_FRAME) + 1
    ts = np.linspace(0.0, t_fim, n_frames)
    lam_arr = np.array([intensidade(float(t), eventos) for t in ts])

    cum_por_frame = np.zeros_like(ts)
    cum = 0.0
    idx_ev = 0
    for i, t in enumerate(ts):
        while idx_ev < len(eventos_sorted) and eventos_sorted[idx_ev].t <= t:
            cum += eventos_sorted[idx_ev].volume
            idx_ev += 1
        cum_por_frame[i] = cum
    caixa = np.maximum(0.0, (C0 + HQLA_MONETIZAVEL) - cum_por_frame)

    # tau: primeiro instante em que caixa < B_PISO (perda de capacidade operacional)
    abaixo_piso = np.where(caixa < B_PISO)[0]
    tau = float(ts[abaixo_piso[0]]) if len(abaixo_piso) > 0 else None
    # t_quebra: instante em que o caixa zera (banco insolvente)
    zerou = np.where(caixa <= 1e-3)[0]
    t_quebra = float(ts[zerou[0]]) if len(zerou) > 0 else None

    # -------- Layout dos paineis --------
    fig = plt.figure(figsize=(10.0, 7.6), facecolor=COR_FUNDO)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.1, 0.6, 1.0], hspace=0.55,
                          left=0.10, right=0.96, top=0.93, bottom=0.08)
    ax_lam = fig.add_subplot(gs[0])
    ax_dom = fig.add_subplot(gs[1])
    ax_cx = fig.add_subplot(gs[2])

    for ax in (ax_lam, ax_dom, ax_cx):
        ax.set_facecolor(COR_FUNDO)
        for spine in ax.spines.values():
            spine.set_color(COR_CINZA)
        ax.tick_params(colors=COR_GRAFITE)
        ax.title.set_color(COR_GRAFITE)
        ax.xaxis.label.set_color(COR_GRAFITE)
        ax.yaxis.label.set_color(COR_GRAFITE)

    # painel 1: lambda(t)
    ax_lam.set_xlim(0, t_fim)
    ax_lam.set_ylim(0, max(lam_arr) * 1.15)
    ax_lam.set_ylabel("λ(t)  saques/h", fontsize=10)
    ax_lam.set_title("Intensidade do processo de Hawkes", fontsize=12, loc="left",
                     color=COR_GRAFITE, fontweight="bold")
    ax_lam.axhline(MU, color=COR_CINZA, lw=1.0, ls="--", label="μ (basal)")
    ax_lam.axvline(T_REGIME_SHIFT, color=COR_AZUL, lw=1.0, ls=":", alpha=0.6)
    ax_lam.text(T_REGIME_SHIFT + 0.2, max(lam_arr) * 1.05,
                "evento de notícia\nα/β: 0,06 → 0,75",
                fontsize=8, color=COR_AZUL, va="top")
    line_lam, = ax_lam.plot([], [], color=COR_LARANJA, lw=2.0)
    ax_lam.set_xlabel("tempo (horas)", fontsize=9)
    ax_lam.legend(loc="upper left", fontsize=8, frameon=False)

    # painel 2: dominos posicionados pelo TEMPO DE EVENTO no eixo x
    # (mesmo eixo do painel lambda) — em regime estavel os eventos ficam
    # espacados e os dominos longe um do outro; em cascata, eventos
    # aglomeram-se e os dominos se tocam fisicamente.
    n_dom = len(eventos_sorted)
    eventos_para_dom = eventos_sorted
    dominos = []
    largura = 0.05      # horas (x-extent do domino em pe)
    altura = 0.40       # y-units; APOS rotacao, vira o alcance fisico em horas
    DURACAO_QUEDA = 0.40  # horas de 0 a 90 graus
    ax_dom.set_xlim(0, t_fim)
    ax_dom.set_ylim(-0.02, 0.55)
    ax_dom.set_yticks([])
    ax_dom.set_xticks([])
    ax_dom.set_title("Cada dominó é um saque no instante do evento; vizinhos só caem na cascata quando se tocam",
                     fontsize=11, loc="left", color=COR_GRAFITE, fontweight="bold")
    for spine in ("top", "right", "left"):
        ax_dom.spines[spine].set_visible(False)
    ax_dom.spines["bottom"].set_color(COR_CINZA)

    for ev in eventos_para_dom:
        x = ev.t
        rect = Rectangle((x - largura / 2, 0), largura, altura,
                         facecolor=COR_CINZA_CLARO, edgecolor=COR_GRAFITE, lw=0.6)
        ax_dom.add_patch(rect)
        dominos.append({"rect": rect, "evento": ev, "x": x, "queda_inicio": None})

    # Propagacao fisica via alcance: o topo do domino i, quando tombado em
    # angulo theta, avanca largura/2 + altura*sin(theta) a partir do centro
    # do domino. Quando esse alcance encosta no vizinho i+1, o vizinho cai.
    # Se delta_x > largura + altura, o vizinho esta fora de alcance e a
    # corrente quebra naturalmente — exatamente o que ocorre em regime
    # estavel, com eventos esparsos no tempo.
    for i, d in enumerate(dominos):
        own_t = d["evento"].t
        if i == 0:
            d["fall_time"] = own_t
            continue
        delta_x = d["x"] - dominos[i - 1]["x"]  # centro a centro, em horas
        gap = max(0.0, delta_x - largura)        # distancia entre superficies
        prev_fall = dominos[i - 1]["fall_time"]
        if gap < altura:
            ratio = min(1.0, gap / altura)
            ang_contact = math.degrees(math.asin(ratio))
            push_time = prev_fall + DURACAO_QUEDA * (ang_contact / 90.0)
            d["fall_time"] = min(own_t, push_time)
        else:
            d["fall_time"] = own_t

    # painel 3: caixa + tau
    ax_cx.set_xlim(0, t_fim)
    ax_cx.set_ylim(0, (C0 + HQLA_MONETIZAVEL) * 1.05)
    ax_cx.set_ylabel("C₀ + Mₜ(HQLA) − Oₜ", fontsize=10)
    ax_cx.set_xlabel("tempo (horas)", fontsize=9)
    ax_cx.set_title("Caixa monetizável até cruzar o piso Bₜ em τ",
                    fontsize=12, loc="left", color=COR_GRAFITE, fontweight="bold")
    ax_cx.axhline(B_PISO, color=COR_AZUL, lw=1.2, ls="--", label="Bₜ (piso operacional)")
    line_cx, = ax_cx.plot([], [], color=COR_LARANJA, lw=2.0)
    tau_line = ax_cx.axvline(0, color=COR_GRAFITE, lw=1.5, ls=":", visible=False)
    tau_text = ax_cx.text(0, B_PISO + 4, "", fontsize=10, color=COR_GRAFITE,
                          fontweight="bold", visible=False)
    quebra_line = ax_cx.axvline(0, color="#b91c1c", lw=1.8, ls="-", visible=False)
    quebra_text = ax_cx.text(0, (C0 + HQLA_MONETIZAVEL) * 0.78, "", fontsize=10,
                             color="#b91c1c", fontweight="bold", visible=False)
    ax_cx.legend(loc="upper right", fontsize=8, frameon=False)

    fig.suptitle("Como uma corrida digital se mede em horas", fontsize=13,
                 color=COR_GRAFITE, fontweight="bold", y=0.985)

    # ---------- update por frame ----------
    def update(i: int):
        t_now = float(ts[i])
        line_lam.set_data(ts[: i + 1], lam_arr[: i + 1])
        line_cx.set_data(ts[: i + 1], caixa[: i + 1])

        # dominos: cada um cai no fall_time pre-computado (com propagacao fisica)
        for d in dominos:
            ev = d["evento"]
            if t_now >= d["fall_time"] and d["queda_inicio"] is None:
                d["queda_inicio"] = d["fall_time"]
            if d["queda_inicio"] is not None:
                progresso = min(1.0, (t_now - d["queda_inicio"]) / DURACAO_QUEDA)
                ang = 90.0 * progresso
                cor = COR_LARANJA if ev.volume > SAQUE_MEDIO * 1.3 else COR_LARANJA_CLARO
                d["rect"].set_facecolor(cor)
                # pivot no canto inferior DIREITO -> domino tomba para frente
                # (rotacao -ang = sentido horario)
                trans = Affine2D().rotate_deg_around(d["x"] + largura / 2, 0, -ang) + ax_dom.transData
                d["rect"].set_transform(trans)

        # tau aparece quando cruzado
        if tau is not None and t_now >= tau:
            tau_line.set_xdata([tau, tau])
            tau_line.set_visible(True)
            tau_text.set_x(tau + 0.15)
            tau_text.set_text(f"τ ≈ {tau:.1f} h")
            tau_text.set_visible(True)

        # ponto de insolvencia (caixa zerou)
        if t_quebra is not None and t_now >= t_quebra:
            quebra_line.set_xdata([t_quebra, t_quebra])
            quebra_line.set_visible(True)
            quebra_text.set_x(t_quebra + 0.15)
            quebra_text.set_ha("left")
            quebra_text.set_text(f"insolvência\nt = {t_quebra:.1f} h")
            quebra_text.set_visible(True)

        return [line_lam, line_cx, tau_line, tau_text, quebra_line, quebra_text] + \
               [d["rect"] for d in dominos]

    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / FPS,
                         blit=False, repeat=False)

    out = Path(__file__).parent / "hawkes_dominoes.gif"
    writer = PillowWriter(fps=FPS)
    anim.save(out, writer=writer, dpi=110)
    print(f"[hawkes] GIF salvo em {out} ({out.stat().st_size / 1024:.0f} KB)")
    if tau is not None:
        print(f"[hawkes] tau = {tau:.2f} h  (caixa cruzou Bt={B_PISO})")
    else:
        print("[hawkes] aviso: caixa nao cruzou Bt na janela simulada")
    if t_quebra is not None:
        print(f"[hawkes] insolvencia: caixa zerou em t = {t_quebra:.2f} h")


if __name__ == "__main__":
    main()
