import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORES = {
    "Salamanca": "#C0392B", "Almagro": "#C0392B",
    "Chamberi": "#E67E22", "Centro": "#E67E22",
    "Tetuan": "#27AE60", "Carabanchel": "#27AE60",
    "Vallecas": "#27AE60", "Usera": "#27AE60",
}


def scatter(resumen):
    fig, ax = plt.subplots(figsize=(8, 5))
    for barrio, row in resumen.iterrows():
        ax.scatter(row["precio_m2"], row["yield_bruto"], s=180, color=COLORES[barrio], zorder=3)
        ax.annotate(barrio, (row["precio_m2"], row["yield_bruto"]), xytext=(6, 4), textcoords="offset points", fontsize=9)

    x = resumen["precio_m2"].values
    y = resumen["yield_bruto"].values
    m, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, m * xs + b, "--", color="gray", linewidth=1.5)

    ax.set_xlabel("Precio mediano (€/m²)")
    ax.set_ylabel("Yield bruto (%)")
    ax.set_title("Precio vs Yield — Madrid barrios")
    ax.grid(True, alpha=0.2)
    fig.savefig("grafico_scatter.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado: grafico_scatter.png")


def barras(resumen):
    df = resumen.sort_values("yield_bruto")
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(df.index, df["yield_bruto"], color=[COLORES[b] for b in df.index])
    for bar, val in zip(bars, df["yield_bruto"]):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, f"{val:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("Yield bruto (%)")
    ax.set_title("Yield por barrio")
    ax.grid(True, axis="x", alpha=0.2)
    fig.savefig("grafico_barras.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado: grafico_barras.png")


def gap_card(gap, ci_lo, ci_hi):
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.set_xlim(-0.5, max(ci_hi + 1, 3.5))
    ax.set_ylim(0, 1)
    ax.barh(0.5, ci_hi - ci_lo, left=ci_lo, height=0.3, color="#27AE60", alpha=0.3)
    ax.vlines(gap, 0.25, 0.75, color="#27AE60", linewidth=3)
    ax.vlines(1.5, 0.1, 0.9, color="#C0392B", linestyle="--", linewidth=2, label="Umbral H2 (+1.5pp)")
    ax.text(gap, 0.82, f"{gap:+.2f} pp", ha="center", fontsize=14, fontweight="bold", color="#27AE60")
    ax.text((ci_lo + ci_hi) / 2, 0.12, f"IC 95%: [{ci_lo:+.2f}, {ci_hi:+.2f}]", ha="center", fontsize=9, color="gray")
    ax.set_yticks([])
    ax.set_xlabel("Diferencia de yield (pp)")
    ax.set_title("Gap: Tetuán & Carabanchel vs Salamanca & Almagro")
    ax.legend(fontsize=9)
    ax.grid(True, axis="x", alpha=0.2)
    fig.savefig("grafico_gap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado: grafico_gap.png")


def veredictos(h1, h2):
    colores_v = {"confirmada": "#27AE60", "rechazada": "#C0392B", "inconclusa": "#E67E22"}
    fig, axes = plt.subplots(1, 2, figsize=(8, 3))
    for ax, (h, titulo) in zip(axes, [("H1", h1["hipotesis"]), ("H2", h2["hipotesis"])]):
        resultado = h1["resultado"] if h == "H1" else h2["resultado"]
        ax.set_facecolor(colores_v[resultado])
        ax.axis("off")
        ax.text(0.5, 0.65, h, ha="center", fontsize=28, fontweight="bold", color="white", transform=ax.transAxes)
        ax.text(0.5, 0.38, titulo, ha="center", fontsize=9, color="white", style="italic", transform=ax.transAxes)
        ax.text(0.5, 0.15, resultado.upper(), ha="center", fontsize=12, fontweight="bold", color="white", transform=ax.transAxes)
    fig.suptitle("Veredictos hipótesis — Yield Inversión Madrid", fontsize=12, fontweight="bold")
    fig.savefig("grafico_veredictos.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Guardado: grafico_veredictos.png")


if __name__ == "__main__":
    import json
    resumen = pd.read_csv("resumen.csv", index_col="barrio")

    try:
        with open("hipotesis.json") as f:
            datos = json.load(f)
        h1, h2 = datos["H1"], datos["H2"]
    except FileNotFoundError:
        h1 = {"hipotesis": "Mayor precio/m² → menor yield", "resultado": "inconclusa"}
        h2 = {"hipotesis": "Tetuán & Carabanchel ≥ +1.5pp", "resultado": "inconclusa", "gap_pp": 1.8, "ci_95": "[-0.5, 2.5]"}

    scatter(resumen)
    barras(resumen)
    gap = h2.get("gap_pp", 1.8)
    ci = h2.get("ci_95", "[1.2, 2.4]").strip("[]").split(", ")
    gap_card(gap, float(ci[0]), float(ci[1]))
    veredictos(h1, h2)
