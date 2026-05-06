#=
Gera artigos/hawkes_dominoes.gif com 3 paineis sincronizados:
  1. λ(t) — intensidade do processo de Hawkes ao longo do tempo
  2. fileira de dominos posicionados pelo tempo de evento (cascata fisica
     por contato; corrente quebra naturalmente onde os eventos se afastam)
  3. caixa + HQLA monetizavel — curva descendente que cruza o piso Bₜ em τ

Cenario pedagogico:
  - 0h..8h:  μ=2/h, α=0.30, β=5/h  -> α/β = 0.06 (regime estavel)
  - 8h..24h: μ=2/h, α=1.50, β=2/h  -> α/β = 0.75 (regime de cascata)
  Em t = T_REGIME_SHIFT eh injetado um "evento de noticia" (saque grande).
  A simulacao para quando o caixa disponivel (C₀ + HQLA monetizavel) zera.

Reprodutivel via seed fixa (SEED).

Como rodar:
  julia --project=. artigos/_gen_hawkes_dominoes.jl
=#

using Random
using Plots

const SEED               = 20260504
const T_TOTAL            = 24.0
const T_REGIME_SHIFT     = 8.0
const DT_FRAME           = 0.10
const FPS                = 10

const MU                 = 2.0
const ALPHA_LOW, BETA_LOW   = 0.30, 5.0    # α/β = 0.06
const ALPHA_HIGH, BETA_HIGH = 1.50, 2.0    # α/β = 0.75

const C0                 = 100.0
const HQLA_MONETIZAVEL   = 30.0
const B_PISO             = 25.0
const SAQUE_MEDIO        = 3.0

const DURACAO_QUEDA      = 0.40   # horas para o domino tombar de 0 a 90 graus
const LARGURA_DOMINO     = 0.05   # horas (x-extent em pe)
const ALTURA_DOMINO      = 0.40   # alcance fisico em horas quando tombado

# paleta alinhada ao header e ao restante do projeto
const COR_LARANJA       = RGB(1.0,        103/255,  25/255)   # #ff6719
const COR_LARANJA_CLARO = RGB(1.0,        178/255, 122/255)   # #ffb27a
const COR_GRAFITE       = RGB( 31/255,     41/255,  51/255)   # #1f2933
const COR_CINZA         = RGB(154/255,    165/255, 177/255)   # #9aa5b1
const COR_CINZA_CLARO   = RGB(230/255,    230/255, 240/255)   # #e6e6f0
const COR_AZUL          = RGB( 30/255,     58/255, 138/255)   # #1e3a8a
const COR_VERMELHO      = RGB(185/255,     28/255,  28/255)   # #b91c1c
const COR_FUNDO         = RGB(250/255,    250/255, 247/255)   # #fafaf7

struct Evento
    t::Float64
    volume::Float64
end

alpha_beta(t) = t < T_REGIME_SHIFT ? (ALPHA_LOW, BETA_LOW) : (ALPHA_HIGH, BETA_HIGH)

function intensidade(t, eventos)
    a, _ = alpha_beta(t)
    _, b = alpha_beta(t)
    soma = 0.0
    @inbounds for ev in eventos
        if ev.t < t
            soma += a * exp(-b * (t - ev.t))
        end
    end
    return MU + soma
end

function simular_hawkes(rng::AbstractRNG)
    eventos = Evento[]
    cum_outflow = 0.0
    caixa_total = C0 + HQLA_MONETIZAVEL
    t = 0.0
    while t < T_TOTAL
        a, b = alpha_beta(t)
        lam_max = max(MU + (a / max(b, 1e-6)) * 5.0,
                      intensidade(t, eventos) * 1.5,
                      5.0)
        u = rand(rng)
        t += -log(max(u, 1e-12)) / lam_max
        t >= T_TOTAL && break

        # injeta o evento de noticia exatamente em T_REGIME_SHIFT
        if !any(abs(ev.t - T_REGIME_SHIFT) < 1e-6 for ev in eventos) && t > T_REGIME_SHIFT
            volume = SAQUE_MEDIO * 3.5
            push!(eventos, Evento(T_REGIME_SHIFT, volume))
            cum_outflow += volume
            cum_outflow >= caixa_total && break
            continue
        end

        lam = intensidade(t, eventos)
        if rand(rng) <= lam / lam_max
            base = t < T_REGIME_SHIFT ? SAQUE_MEDIO : SAQUE_MEDIO * 1.4
            volume = base * (0.6 + rand(rng) * 0.9)
            if cum_outflow + volume > caixa_total
                volume = caixa_total - cum_outflow
                if volume > 1e-3
                    push!(eventos, Evento(t, volume))
                    cum_outflow += volume
                end
                break
            end
            push!(eventos, Evento(t, volume))
            cum_outflow += volume
        end
    end
    return eventos
end

"""
Gera um Shape (poligono fechado) de retangulo (largura w, altura h) centrado
em x_center na base, rotacionado por ang_deg graus em torno do canto inferior
direito. ang_deg positivo = tomba para frente (sentido horario).
"""
function domino_shape(x_center, w, h, ang_deg)
    pivot_x = x_center + w/2
    pivot_y = 0.0
    θ = -deg2rad(ang_deg)   # negativo: rotacao horaria
    c, s = cos(θ), sin(θ)
    cantos = ((x_center - w/2, 0.0),
              (x_center + w/2, 0.0),
              (x_center + w/2, h),
              (x_center - w/2, h))
    xs = Float64[]
    ys = Float64[]
    sizehint!(xs, 4); sizehint!(ys, 4)
    for (x, y) in cantos
        dx, dy = x - pivot_x, y - pivot_y
        push!(xs, pivot_x + dx*c - dy*s)
        push!(ys, pivot_y + dx*s + dy*c)
    end
    return Shape(xs, ys)
end

function compute_fall_times(eventos)
    n = length(eventos)
    fall_times = Vector{Float64}(undef, n)
    @inbounds for i in 1:n
        own_t = eventos[i].t
        if i == 1
            fall_times[i] = own_t
            continue
        end
        delta_x = eventos[i].t - eventos[i-1].t
        gap = max(0.0, delta_x - LARGURA_DOMINO)
        prev_fall = fall_times[i-1]
        if gap < ALTURA_DOMINO
            ratio = min(1.0, gap / ALTURA_DOMINO)
            ang_contact = rad2deg(asin(ratio))
            push_time = prev_fall + DURACAO_QUEDA * (ang_contact / 90.0)
            fall_times[i] = min(own_t, push_time)
        else
            fall_times[i] = own_t
        end
    end
    return fall_times
end

function main()
    rng = MersenneTwister(SEED)
    eventos = simular_hawkes(rng)
    sort!(eventos, by = ev -> ev.t)
    t_ultimo = isempty(eventos) ? 0.0 : eventos[end].t
    t_fim = min(T_TOTAL, max(t_ultimo + 1.5, T_REGIME_SHIFT + 4.0))
    println("[hawkes] simulados $(length(eventos)) saques; ultimo em ",
            round(t_ultimo, digits=2), "h; janela exibida ate ",
            round(t_fim, digits=2), "h")

    n_frames = Int(round(t_fim / DT_FRAME)) + 1
    ts = collect(range(0.0, t_fim, length=n_frames))
    lam_arr = [intensidade(t, eventos) for t in ts]
    lam_ymax = maximum(lam_arr) * 1.15

    cum_por_frame = zeros(n_frames)
    cum = 0.0
    idx_ev = 1
    @inbounds for (i, t) in enumerate(ts)
        while idx_ev <= length(eventos) && eventos[idx_ev].t <= t
            cum += eventos[idx_ev].volume
            idx_ev += 1
        end
        cum_por_frame[i] = cum
    end
    caixa = max.(0.0, (C0 + HQLA_MONETIZAVEL) .- cum_por_frame)

    tau = nothing
    for (i, c) in enumerate(caixa)
        if c < B_PISO
            tau = ts[i]; break
        end
    end
    t_quebra = nothing
    for (i, c) in enumerate(caixa)
        if c <= 1e-3
            t_quebra = ts[i]; break
        end
    end

    fall_times = compute_fall_times(eventos)

    anim = @animate for fi in 1:n_frames
        t_now = ts[fi]

        # painel 1: λ(t)
        p1 = plot(ts[1:fi], lam_arr[1:fi];
                  color=COR_LARANJA, lw=2, label="",
                  xlim=(0, t_fim), ylim=(0, lam_ymax),
                  xlabel="tempo (horas)", ylabel="λ(t)  saques/h",
                  title="Intensidade do processo de Hawkes",
                  titlefontsize=11, titlelocation=:left,
                  framestyle=:box, grid=false,
                  background_color=COR_FUNDO,
                  foreground_color=COR_GRAFITE,
                  foreground_color_axis=COR_GRAFITE,
                  foreground_color_text=COR_GRAFITE)
        hline!(p1, [MU]; color=COR_CINZA, ls=:dash, lw=1, label="μ (basal)")
        vline!(p1, [T_REGIME_SHIFT]; color=COR_AZUL, ls=:dot, lw=1,
               alpha=0.6, label="")
        annotate!(p1, T_REGIME_SHIFT + 0.2, lam_ymax * 0.92,
                  text("evento de notícia\nα/β: 0,06 → 0,75", :left, 8, COR_AZUL))

        # painel 2: dominos
        p2 = plot(; xlim=(0, t_fim), ylim=(-0.02, 0.55),
                  framestyle=:none, ticks=false, label="",
                  title="Cada dominó é um saque no instante do evento; vizinhos só caem na cascata quando se tocam",
                  titlefontsize=10, titlelocation=:left,
                  background_color=COR_FUNDO,
                  foreground_color=COR_GRAFITE)
        plot!(p2, [0.0, t_fim], [0.0, 0.0]; color=COR_CINZA, lw=0.8, label="")
        for (i, ev) in enumerate(eventos)
            ft = fall_times[i]
            if t_now >= ft
                progresso = min(1.0, (t_now - ft) / DURACAO_QUEDA)
                ang = 90.0 * progresso
                cor = ev.volume > SAQUE_MEDIO * 1.3 ? COR_LARANJA : COR_LARANJA_CLARO
                plot!(p2, domino_shape(ev.t, LARGURA_DOMINO, ALTURA_DOMINO, ang);
                      fillcolor=cor, linecolor=COR_GRAFITE, lw=0.5, label="")
            else
                plot!(p2, domino_shape(ev.t, LARGURA_DOMINO, ALTURA_DOMINO, 0.0);
                      fillcolor=COR_CINZA_CLARO, linecolor=COR_GRAFITE,
                      lw=0.5, label="")
            end
        end

        # painel 3: caixa + tau + insolvencia
        cx_ymax = (C0 + HQLA_MONETIZAVEL) * 1.05
        p3 = plot(ts[1:fi], caixa[1:fi];
                  color=COR_LARANJA, lw=2, label="",
                  xlim=(0, t_fim), ylim=(0, cx_ymax),
                  xlabel="tempo (horas)", ylabel="C₀ + Mₜ(HQLA) − Oₜ",
                  title="Caixa monetizável até cruzar o piso Bₜ em τ",
                  titlefontsize=11, titlelocation=:left,
                  framestyle=:box, grid=false,
                  background_color=COR_FUNDO,
                  foreground_color=COR_GRAFITE,
                  foreground_color_axis=COR_GRAFITE,
                  foreground_color_text=COR_GRAFITE)
        hline!(p3, [B_PISO]; color=COR_AZUL, ls=:dash, lw=1.2,
               label="Bₜ (piso operacional)", legend=:topright)
        if tau !== nothing && t_now >= tau
            vline!(p3, [tau]; color=COR_GRAFITE, ls=:dot, lw=1.5, label="")
            tau_anchor = tau > 0.75 * t_fim ? :right : :left
            tau_offset = tau_anchor === :right ? -0.20 : 0.15
            annotate!(p3, tau + tau_offset, B_PISO + 6,
                      text("τ ≈ $(round(tau, digits=1)) h", tau_anchor, 10,
                           COR_GRAFITE))
        end
        if t_quebra !== nothing && t_now >= t_quebra
            vline!(p3, [t_quebra]; color=COR_VERMELHO, lw=1.8, label="")
            quebra_anchor = t_quebra > 0.75 * t_fim ? :right : :left
            quebra_offset = quebra_anchor === :right ? -0.25 : 0.15
            annotate!(p3, t_quebra + quebra_offset, cx_ymax * 0.78,
                      text("insolvência\nt = $(round(t_quebra, digits=1)) h",
                           quebra_anchor, 10, COR_VERMELHO))
        end

        plot(p1, p2, p3;
             layout=grid(3, 1, heights=[0.40, 0.22, 0.38]),
             size=(1100, 836),
             plot_title="Como uma corrida digital se mede em horas",
             plot_titlefontsize=13)
    end

    out = joinpath(@__DIR__, "hawkes_dominoes.gif")
    gif(anim, out; fps=FPS)

    sz_kb = round(filesize(out) / 1024, digits=0)
    println("[hawkes] GIF salvo em $out ($(sz_kb) KB)")
    tau !== nothing && println("[hawkes] tau = ",
                               round(tau, digits=2), " h  (caixa cruzou Bt=",
                               B_PISO, ")")
    t_quebra !== nothing && println("[hawkes] insolvencia: caixa zerou em t = ",
                                    round(t_quebra, digits=2), " h")
end

main()
