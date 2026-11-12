"""Sistema visual: tokens, simbolo, lockups, mosaico e utilitarios de cor."""
import math
import random

NAVY = "#14274E"
NAVY2 = "#0D1B38"
OURO = "#F0C04F"       # sobre escuro
OURO_ESC = "#9C6C0E"   # sobre claro
NEVOA = "#F3F5F7"
LINHA = "#D9DEE5"
CINZA = "#4B5563"
PAPEL = "#FFFFFF"

UNIDADES = {
    "dados":    ("Dados Públicos", "#B80F2D", "Estatísticas, orçamento e indicadores nacionais."),
    "research": ("Research", "#0F6E73", "Estudos sociais, económicos e de mercado."),
    "politics": ("Politics", "#5B3A8E", "Opinião pública e confiança institucional."),
    "media":    ("Media", "#B45309", "Jornalismo de dados, vídeo e explicadores."),
}


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_txt(h):
    return " ".join(str(v) for v in _rgb(h))


def cmyk_txt(h):
    r, g, b = [v / 255 for v in _rgb(h)]
    k = 1 - max(r, g, b)
    if k == 1:
        return "0 0 0 100"
    c, m, y = [(1 - v - k) / (1 - k) for v in (r, g, b)]
    return " ".join(str(round(v * 100)) for v in (c, m, y, k))


def _lum(h):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = [f(v) for v in _rgb(h)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def barras(n=5, gap=5.0):
    """Corta o D (recta + semicirculo de raio 50) em n barras horizontais."""
    h = (100 - gap * (n - 1)) / n
    x = lambda y: 50 + math.sqrt(max(0, 2500 - (y - 50) ** 2))
    out = []
    for i in range(n):
        y0 = i * (h + gap)
        y1 = y0 + h
        out.append(f"M0 {y0:.3f}H{x(y0):.3f}A50 50 0 0 1 {x(y1):.3f} {y1:.3f}H0Z")
    return out


def simbolo(cor=NAVY, acento=OURO_ESC, n=5, px=None, estilo=""):
    gap = 5 if n == 5 else 9
    caminhos = barras(n, gap)
    meio = n // 2
    corpo = "".join(
        f'<path d="{d}" fill="{acento if i == meio else cor}"/>' for i, d in enumerate(caminhos)
    )
    tam = f'width="{px}" height="{px}"' if px else ""
    return f'<svg viewBox="0 0 100 100" {tam} style="display:block;flex:none;{estilo}" aria-hidden="true">{corpo}</svg>'


def lockup(fs=48, cor=NAVY, acento=OURO_ESC, sub=None, subcor=None):
    """Horizontal: simbolo + nome. fs = corpo do texto em px."""
    s = round(fs * 1.34)
    extra = ""
    if sub:
        extra = (
            f'<span style="width:{max(1, fs * .04):.1f}px;height:{fs * 1.1:.0f}px;background:{cor};opacity:.28;'
            f'margin:0 {fs * .36:.0f}px"></span>'
            f'<span style="font:600 {fs}px Plex;letter-spacing:-.012em;color:{subcor or cor}">{sub}</span>'
        )
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{fs * .36:.0f}px;white-space:nowrap">'
        f'{simbolo(cor, acento, px=s)}'
        f'<span style="font:600 {fs}px Plex;letter-spacing:-.016em;color:{cor}">Dados da Banda</span>{extra}</span>'
    )


def vertical(fs=44, cor=NAVY, acento=OURO_ESC):
    return (
        f'<span style="display:inline-flex;flex-direction:column;align-items:center;gap:{fs * .5:.0f}px">'
        f'{simbolo(cor, acento, px=round(fs * 2.3))}'
        f'<span style="font:600 {fs}px Plex;letter-spacing:-.016em;color:{cor};white-space:nowrap">Dados da Banda</span></span>'
    )


def mosaico(cols, rows, t, paleta, fundo, semente=7, densidade=.84):
    """Padrao modular: quartos de circulo, D, barras e pontos, tudo derivado do simbolo."""
    rnd = random.Random(semente)
    c = []
    for j in range(rows):
        for i in range(cols):
            x, y = i * t, j * t
            if rnd.random() > densidade:
                continue
            cor = rnd.choice(paleta)
            r = rnd.choice((0, 90, 180, 270))
            tipo = rnd.choice(("q", "q", "d", "b", "b", "o", "s"))
            g = f'transform="translate({x} {y}) rotate({r} {t / 2} {t / 2})" fill="{cor}"'
            if tipo == "q":
                c.append(f'<path {g} d="M0 0H{t}A{t} {t} 0 0 1 0 {t}Z"/>')
            elif tipo == "d":
                c.append(f'<path {g} d="M0 0H{t / 2}A{t / 2} {t / 2} 0 0 1 {t / 2} {t}H0Z"/>')
            elif tipo == "b":
                h = t / 4
                c.append(
                    f'<g {g}><rect width="{t}" height="{h}"/><rect y="{1.5 * h}" width="{t}" height="{h}"/>'
                    f'<rect y="{3 * h}" width="{t}" height="{h}"/></g>'
                )
            elif tipo == "o":
                c.append(f'<circle {g} cx="{t / 2}" cy="{t / 2}" r="{t / 2}"/>')
            else:
                c.append(f'<rect {g} width="{t}" height="{t}"/>')
    w, h = cols * t, rows * t
    return (
        f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="display:block">'
        f'<rect width="{w}" height="{h}" fill="{fundo}"/>{"".join(c)}</svg>'
    )


FONTES = (
    '<link rel="preconnect" href="https://fonts.gstatic.com">'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700'
    '&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500&display=block" rel="stylesheet">'
)
CSS_BASE = """
*{box-sizing:border-box}html,body{margin:0;padding:0}
body{font-family:'IBM Plex Sans',sans-serif;color:#14274E;-webkit-print-color-adjust:exact;print-color-adjust:exact}
"""
