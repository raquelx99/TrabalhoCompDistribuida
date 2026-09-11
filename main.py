"""Console de Quorum, simulador estocastico de disponibilidade (Exercicio 1.2).

App desktop para o simulador: sorteia a disponibilidade de cada
servidor a cada rodada, mostra o estado do cluster ao vivo como um "jardim"
de servidores (flor aberta = disponivel, botao fechado = indisponivel) e
compara a frequencia experimental acumulada com o valor previsto pela
formula analitica (mesma logica que está no notebook).
"""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pygame

WIDTH, HEIGHT = 1040, 720
FPS = 60

BASE_DIR = Path(__file__).resolve().parent
FONT_DISPLAY = BASE_DIR / "assets" / "fonts" / "Baloo2.ttf"
FONT_BODY = BASE_DIR / "assets" / "fonts" / "Nunito.ttf"

CREAM = (255, 247, 230)
SURFACE = (255, 255, 250)
TILE_BG = (255, 252, 244)
BORDER = (227, 217, 196)
INK = (58, 46, 34)
INK_2 = (107, 90, 70)
INK_MUTED = (156, 141, 119)

LEAF = (108, 162, 74)
LEAF_DARK = (79, 122, 51)
SUNSHINE = (244, 197, 66)
MARIGOLD = (242, 140, 56)
MARIGOLD_DARK = (191, 103, 32)
BLUSH = (247, 183, 196)
BLUSH_DARK = (214, 133, 150)
SAGE = (199, 221, 174)
SAGE_DARK = (140, 168, 108)

GOOD = LEAF
CRITICAL = MARIGOLD
CRITICAL_DARK = MARIGOLD_DARK


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_font(size: int, display: bool = False, bold: bool = False) -> pygame.font.Font:
    path = FONT_DISPLAY if display else FONT_BODY
    font = pygame.font.Font(str(path), size)
    if bold:
        font.set_bold(True)
    return font


def analytical_availability(n: int, k: int, p: float) -> float:
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    soma = sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k))
    return clamp(1 - soma, 0.0, 1.0)


@dataclass
class Simulation:
    n: int = 12
    k: int = 7
    p: float = 0.85
    rounds: int = 0
    successes: int = 0
    server_states: list[bool] = field(default_factory=list)
    history: list[tuple[int, int, bool, float]] = field(default_factory=list)

    def run_round(self) -> None:
        states = [random.random() <= self.p for _ in range(self.n)]
        avail = sum(states)
        success = avail >= self.k
        self.rounds += 1
        if success:
            self.successes += 1
        self.server_states = states
        self.history.append((self.rounds, avail, success, self.successes / self.rounds))

    def reset_sampling(self) -> None:
        self.rounds = 0
        self.successes = 0
        self.history = []
        self.server_states = []

    @property
    def experimental(self) -> float:
        return self.successes / self.rounds if self.rounds else 0.0

    @property
    def analytical(self) -> float:
        return analytical_availability(self.n, self.k, self.p)


class Slider:
    def __init__(self, x, y, w, value, minv, maxv, step, label, fmt):
        self.rect = pygame.Rect(x, y, w, 8)
        self.value = value
        self.minv = minv
        self.maxv = maxv
        self.step = step
        self.label = label
        self.fmt = fmt
        self.dragging = False

    def _set_from_x(self, x: int) -> None:
        frac = clamp((x - self.rect.x) / self.rect.w, 0.0, 1.0)
        raw = self.minv + frac * (self.maxv - self.minv)
        stepped = round(raw / self.step) * self.step
        self.value = clamp(stepped, self.minv, self.maxv)

    def handle_rect(self) -> pygame.Rect:
        span = (self.maxv - self.minv) or 1
        frac = (self.value - self.minv) / span
        cx = self.rect.x + frac * self.rect.w
        return pygame.Rect(int(cx) - 8, self.rect.centery - 8, 16, 16)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self.handle_rect().inflate(10, 10)
            track_hit = self.rect.inflate(0, 16)
            if hit.collidepoint(event.pos) or track_hit.collidepoint(event.pos):
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        return False

    def draw(self, surf, font_label, font_val):
        pygame.draw.rect(surf, SAGE, self.rect, border_radius=self.rect.h // 2)
        span = (self.maxv - self.minv) or 1
        frac = (self.value - self.minv) / span
        fill_w = int(self.rect.w * frac)
        if fill_w > 0:
            pygame.draw.rect(
                surf, LEAF, (self.rect.x, self.rect.y, fill_w, self.rect.h), border_radius=self.rect.h // 2
            )
        handle = self.handle_rect()
        pygame.draw.circle(surf, SUNSHINE, handle.center, 9)
        pygame.draw.circle(surf, LEAF_DARK, handle.center, 9, width=2)

        label_surf = font_label.render(self.label, True, INK_2)
        surf.blit(label_surf, (self.rect.x, self.rect.y - 24))
        val_surf = font_val.render(self.fmt(self.value), True, LEAF_DARK)
        surf.blit(val_surf, (self.rect.right - val_surf.get_width(), self.rect.y - 24))


class Button:
    def __init__(self, rect, label, style="ghost"):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.style = style  # "ghost" | "leaf" | "blush"

    def draw(self, surf, font):
        radius = self.rect.h // 2
        if self.style == "leaf":
            fill, text_color = LEAF, CREAM
        elif self.style == "blush":
            fill, text_color = BLUSH, INK
        else:
            fill, text_color = SURFACE, INK
        pygame.draw.rect(surf, fill, self.rect, border_radius=radius)
        border_color = fill if self.style != "ghost" else SAGE_DARK
        pygame.draw.rect(surf, border_color, self.rect, width=2, border_radius=radius)
        label_surf = font.render(self.label, True, text_color)
        surf.blit(label_surf, label_surf.get_rect(center=self.rect.center))

    def clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


def draw_card(surf, rect, radius=18):
    shadow = pygame.Surface((rect.w + 16, rect.h + 16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (58, 46, 34, 28), (6, 9, rect.w, rect.h), border_radius=radius)
    surf.blit(shadow, (rect.x - 6, rect.y - 5))
    pygame.draw.rect(surf, SURFACE, rect, border_radius=radius)
    pygame.draw.rect(surf, BORDER, rect, width=2, border_radius=radius)


def draw_flower(surf, cx, cy, r):
    petal_r = max(3, int(r * 0.52))
    for i in range(6):
        ang = i * (math.pi / 3)
        px = cx + math.cos(ang) * r * 0.5
        py = cy + math.sin(ang) * r * 0.5
        pygame.draw.circle(surf, LEAF, (int(px), int(py)), petal_r)
    pygame.draw.circle(surf, SUNSHINE, (int(cx), int(cy)), max(3, int(r * 0.4)))


def draw_bud(surf, cx, cy, r):
    stem_h = int(r * 0.6)
    stem_w = max(2, int(r * 0.16))
    pygame.draw.line(
        surf, SAGE_DARK, (cx, cy + int(r * 0.45)), (cx, cy + int(r * 0.45) + stem_h), stem_w
    )
    pygame.draw.circle(surf, CRITICAL, (int(cx), int(cy)), max(4, int(r * 0.5)))
    pygame.draw.circle(surf, CRITICAL_DARK, (int(cx), int(cy)), max(4, int(r * 0.5)), width=2)


def draw_panel_title(surf, rect, title, font_h2):
    title_surf = font_h2.render(title, True, INK)
    surf.blit(title_surf, (rect.x + 20, rect.y + 16))


def draw_server_grid(surf, rect, sim: Simulation, fonts):
    top = rect.y + 52
    inner_w = rect.w - 40
    cell, gap = 34, 8
    cols = max(1, min(sim.n, inner_w // (cell + gap)))
    grid_w = cols * cell + (cols - 1) * gap
    ox = rect.x + (rect.w - grid_w) // 2
    show_id = sim.n <= 30

    for i in range(sim.n):
        col, row = i % cols, i // cols
        x = ox + col * (cell + gap)
        y = top + row * (cell + gap)
        cell_rect = pygame.Rect(x, y, cell, cell)
        pygame.draw.rect(surf, TILE_BG, cell_rect, border_radius=10)
        pygame.draw.rect(surf, BORDER, cell_rect, width=1, border_radius=10)
        cx, cy = cell_rect.center
        icon_cy = cy - (3 if show_id else 0)
        if i < len(sim.server_states):
            if sim.server_states[i]:
                draw_flower(surf, cx, icon_cy, cell * 0.36)
            else:
                draw_bud(surf, cx, icon_cy, cell * 0.32)
        if show_id:
            idl = fonts["tiny"].render(f"{i + 1:02d}", True, INK_MUTED)
            surf.blit(idl, idl.get_rect(center=(cx, cell_rect.bottom - 7)))


def draw_stats_row(surf, x, y, w, sim: Simulation, fonts):
    tiles = [
        ("RODADAS", str(sim.rounds), INK),
        ("SUCESSOS", str(sim.successes), INK),
        ("FREQ. EXPERIMENTAL", f"{sim.experimental * 100:.1f}%", LEAF_DARK),
        ("VALOR ANALITICO", f"{sim.analytical * 100:.1f}%", INK),
        ("DIFERENCA ABS.", f"{abs(sim.analytical - sim.experimental) * 100:.2f}%", INK),
    ]
    gap = 12
    tile_w = (w - gap * (len(tiles) - 1)) / len(tiles)
    for i, (label, value, color) in enumerate(tiles):
        tx = x + i * (tile_w + gap)
        rect = pygame.Rect(int(tx), y, int(tile_w), 70)
        draw_card(surf, rect, radius=14)
        lab = fonts["tiny"].render(label, True, INK_MUTED)
        surf.blit(lab, (rect.x + 14, rect.y + 12))
        val = fonts["stat"].render(value, True, color)
        surf.blit(val, (rect.x + 14, rect.y + 32))


def draw_chart(surf, rect, sim: Simulation, fonts):
    pad_l, pad_r, pad_t, pad_b = 46, 16, 78, 28
    plot = pygame.Rect(rect.x + pad_l, rect.y + pad_t, rect.w - pad_l - pad_r, rect.h - pad_t - pad_b)

    legend_x = rect.x + 20
    legend_y = rect.y + 46
    pygame.draw.line(surf, LEAF, (legend_x, legend_y + 6), (legend_x + 16, legend_y + 6), 3)
    lg1 = fonts["tiny"].render("Frequencia experimental (acumulada)", True, INK_2)
    surf.blit(lg1, (legend_x + 22, legend_y))
    legend2_x = legend_x + 22 + lg1.get_width() + 24
    x = legend2_x
    while x < legend2_x + 16:
        pygame.draw.line(surf, INK_MUTED, (x, legend_y + 6), (min(x + 6, legend2_x + 16), legend_y + 6), 2)
        x += 9
    lg2 = fonts["tiny"].render("Valor analitico (p, k, n atuais)", True, INK_2)
    surf.blit(lg2, (legend2_x + 22, legend_y))

    if not sim.history:
        empty = fonts["label"].render("Aguardando rodadas...", True, INK_MUTED)
        surf.blit(empty, empty.get_rect(center=plot.center))
        return

    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        yy = plot.bottom - int(frac * plot.h)
        pygame.draw.line(surf, SAGE, (plot.x, yy), (plot.right, yy), 1)
        lab = fonts["tiny"].render(f"{int(frac * 100)}%", True, INK_MUTED)
        surf.blit(lab, (plot.x - lab.get_width() - 8, yy - 6))

    max_round = sim.history[-1][0]

    def xs(r):
        return plot.x + (0 if max_round <= 1 else (r - 1) / (max_round - 1) * plot.w)

    def ys(v):
        return plot.bottom - v * plot.h

    analytic = sim.analytical
    ay = int(ys(analytic))
    x = plot.x
    while x < plot.right:
        pygame.draw.line(surf, INK_MUTED, (x, ay), (min(x + 8, plot.right), ay), 2)
        x += 13

    step = max(1, len(sim.history) // 500)
    pts = sim.history[::step]
    if pts[-1] is not sim.history[-1]:
        pts.append(sim.history[-1])
    poly = [(xs(r), ys(cf)) for r, _avail, _ok, cf in pts]
    if len(poly) >= 2:
        pygame.draw.lines(surf, LEAF, False, poly, 3)
    last_x, last_y = poly[-1]
    pygame.draw.circle(surf, LEAF, (int(last_x), int(last_y)), 5)
    pygame.draw.circle(surf, CREAM, (int(last_x), int(last_y)), 5, width=2)

    exp_lab = fonts["tiny"].render(f"{sim.experimental * 100:.1f}%", True, LEAF_DARK)
    surf.blit(exp_lab, (min(last_x + 8, plot.right - exp_lab.get_width()), last_y - 16))
    ana_lab = fonts["tiny"].render(f"{analytic * 100:.1f}%", True, INK_MUTED)
    surf.blit(ana_lab, (plot.right - ana_lab.get_width(), ay - 16 if ay > plot.y + 16 else ay + 4))

    r_lab = fonts["tiny"].render(f"rodada {max_round}", True, INK_MUTED)
    surf.blit(r_lab, (plot.right - r_lab.get_width(), plot.bottom + 8))
    r0_lab = fonts["tiny"].render("rodada 1", True, INK_MUTED)
    surf.blit(r0_lab, (plot.x, plot.bottom + 8))


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Console de Quorum")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    fonts = {
        "title": load_font(26, display=True, bold=True),
        "h2": load_font(16, display=True, bold=True),
        "label": load_font(13),
        "small": load_font(12),
        "tiny": load_font(11),
        "val": load_font(13, bold=True),
        "stat": load_font(21, display=True, bold=True),
        "btn": load_font(13, bold=True),
    }

    sim = Simulation()

    n_slider = Slider(40, 160, 190, sim.n, 1, 50, 1, "n - servidores", lambda v: str(int(v)))
    k_slider = Slider(40, 222, 190, sim.k, 1, sim.n, 1, "k - quorum minimo", lambda v: str(int(v)))
    p_slider = Slider(40, 284, 190, sim.p * 100, 0, 100, 1, "p - disponibilidade", lambda v: f"{int(v)}%")
    speed_slider = Slider(40, 540, 190, 5, 1, 20, 1, "velocidade", lambda v: f"{int(v)} rodadas/s")

    step_btn = Button((40, 346, 190, 36), "Rodar 1 rodada", style="ghost")
    auto_btn = Button((40, 390, 190, 36), "Pausar", style="blush")
    reset_btn = Button((40, 434, 190, 36), "Reiniciar amostragem", style="ghost")

    auto_running = True
    round_timer = 0.0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    auto_running = not auto_running
                elif event.key == pygame.K_r:
                    sim.reset_sampling()

            if n_slider.handle_event(event):
                new_n = int(n_slider.value)
                if new_n != sim.n:
                    sim.n = new_n
                    k_slider.maxv = new_n
                    if sim.k > new_n:
                        sim.k = new_n
                        k_slider.value = new_n
                    sim.reset_sampling()

            if k_slider.handle_event(event):
                new_k = int(k_slider.value)
                if new_k != sim.k:
                    sim.k = new_k
                    sim.reset_sampling()

            if p_slider.handle_event(event):
                new_p = p_slider.value / 100
                if abs(new_p - sim.p) > 1e-9:
                    sim.p = new_p
                    sim.reset_sampling()

            speed_slider.handle_event(event)

            if step_btn.clicked(event):
                sim.run_round()
            elif auto_btn.clicked(event):
                auto_running = not auto_running
            elif reset_btn.clicked(event):
                sim.reset_sampling()

        auto_btn.style = "blush" if auto_running else "leaf"
        auto_btn.label = "Pausar" if auto_running else "Retomar"

        if auto_running:
            interval = 1.0 / speed_slider.value
            round_timer += dt
            guard = 0
            while round_timer >= interval and guard < 200:
                sim.run_round()
                round_timer -= interval
                guard += 1

        screen.fill(CREAM)

        draw_flower(screen, 30, 36, 13)
        screen.blit(fonts["title"].render("Console de Quorum", True, INK), (52, 22))
        screen.blit(
            fonts["small"].render("Exercicio 1.2 - cada servidor floresce com probabilidade p", True, LEAF_DARK),
            (52, 56),
        )

        last = sim.history[-1] if sim.history else None
        avail = last[1] if last else 0
        success = last[2] if last else (avail >= sim.k)
        banner = pygame.Rect(WIDTH - 300, 18, 280, 66)
        draw_card(screen, banner, radius=banner.h // 2)
        if success:
            draw_flower(screen, banner.x + 30, banner.centery, 13)
        else:
            draw_bud(screen, banner.x + 30, banner.centery - 2, 12)
        status_text = "Sistema disponivel" if success else "Sistema indisponivel"
        status_color = LEAF_DARK if success else CRITICAL_DARK
        screen.blit(fonts["h2"].render(status_text, True, status_color), (banner.x + 54, banner.y + 12))
        sub = f"{avail} de {sim.n} disponiveis - minimo k={sim.k}"
        screen.blit(fonts["small"].render(sub, True, INK_MUTED), (banner.x + 54, banner.y + 38))

        panel_rect = pygame.Rect(20, 116, 230, 578)
        draw_card(screen, panel_rect, radius=20)
        n_slider.draw(screen, fonts["label"], fonts["val"])
        k_slider.draw(screen, fonts["label"], fonts["val"])
        p_slider.draw(screen, fonts["label"], fonts["val"])
        step_btn.draw(screen, fonts["btn"])
        auto_btn.draw(screen, fonts["btn"])
        reset_btn.draw(screen, fonts["btn"])

        divider_y = reset_btn.rect.bottom + 20
        pygame.draw.line(screen, BORDER, (panel_rect.x + 20, divider_y), (panel_rect.right - 20, divider_y), 2)

        speed_slider.draw(screen, fonts["label"], fonts["val"])

        hint_lines = ["Espaco: pausar/retomar", "R: reiniciar - Esc: sair"]
        for i, line in enumerate(hint_lines):
            hs = fonts["tiny"].render(line, True, INK_MUTED)
            screen.blit(hs, (panel_rect.x + 20, panel_rect.bottom - 40 + i * 16))

        grid_rect = pygame.Rect(270, 116, WIDTH - 290, 258)
        draw_card(screen, grid_rect, radius=20)
        draw_panel_title(screen, grid_rect, "Jardim de servidores - ultima rodada", fonts["h2"])
        draw_server_grid(screen, grid_rect, sim, fonts)

        stats_y = grid_rect.bottom + 16
        draw_stats_row(screen, 270, stats_y, WIDTH - 290, sim, fonts)

        chart_rect = pygame.Rect(270, stats_y + 86, WIDTH - 290, HEIGHT - (stats_y + 86) - 20)
        draw_card(screen, chart_rect, radius=20)
        draw_panel_title(screen, chart_rect, "Convergencia da frequencia experimental", fonts["h2"])
        draw_chart(screen, chart_rect, sim, fonts)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
