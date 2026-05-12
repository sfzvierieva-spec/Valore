import numpy as np
import pandas as pd
from scipy import stats

BARRIOS = ["Salamanca", "Almagro", "Chamberi", "Centro", "Tetuan", "Carabanchel", "Vallecas", "Usera"]


def bootstrap_ci(valores, n=2000, nivel=0.95):
    rng = np.random.default_rng(42)
    muestras = [np.median(rng.choice(valores, size=len(valores), replace=True)) for _ in range(n)]
    alpha = (1 - nivel) / 2
    return np.quantile(muestras, alpha), np.quantile(muestras, 1 - alpha)


def calcular_resumen(df):
    filas = []
    venta = df[df["tipo"] == "venta"]
    alquiler = df[df["tipo"] == "alquiler"]

    for barrio in BARRIOS:
        v = venta[venta["barrio"] == barrio]
        a = alquiler[alquiler["barrio"] == barrio]

        if v.empty or a.empty:
            continue

        precio_m2 = v["precio_m2"].median()
        renta_mes = a["precio"].rolling(window=min(30, len(a)), min_periods=1).median().median()
        metros_medio = v["metros"].median()
        precio_total = precio_m2 * metros_medio
        yield_bruto = (renta_mes * 12 / precio_total) * 100

        filas.append({
            "barrio": barrio,
            "precio_m2": round(precio_m2, 0),
            "renta_mes": round(renta_mes, 0),
            "yield_bruto": round(yield_bruto, 2),
            "n_venta": len(v),
            "n_alquiler": len(a),
        })

    resumen = pd.DataFrame(filas).set_index("barrio")
    resumen["gap_vs_salamanca"] = (resumen["yield_bruto"] - resumen.loc["Salamanca", "yield_bruto"]).round(2)
    return resumen


def hipotesis(df, resumen):
    rho, p = stats.spearmanr(resumen["precio_m2"], resumen["yield_bruto"])

    h1 = {
        "hipotesis": "Mayor precio/m² → menor yield",
        "rho": round(rho, 4),
        "p_valor": round(p, 4),
        "resultado": "confirmada" if rho < -0.5 and p < 0.05 else "rechazada" if rho > 0 and p < 0.05 else "inconclusa",
    }

    venta = df[df["tipo"] == "venta"]
    alquiler = df[df["tipo"] == "alquiler"]

    target = ["Tetuan", "Carabanchel"]
    base = ["Salamanca", "Almagro"]

    yields_target = []
    for b in target:
        renta = alquiler[alquiler["barrio"] == b]["precio"].median()
        for _, row in venta[venta["barrio"] == b].iterrows():
            yields_target.append((renta * 12 / row["precio"]) * 100)

    renta_base = alquiler[alquiler["barrio"].isin(base)]["precio"].median()
    precio_base = venta[venta["barrio"].isin(base)]["precio"].median()
    yield_base = (renta_base * 12 / precio_base) * 100

    gap = np.median(yields_target) - yield_base
    ci_lo, ci_hi = bootstrap_ci(np.array(yields_target) - yield_base)

    h2 = {
        "hipotesis": "Tetuán & Carabanchel ≥ +1.5pp sobre Salamanca & Almagro",
        "gap_pp": round(gap, 2),
        "ci_95": f"[{ci_lo:+.2f}, {ci_hi:+.2f}]",
        "resultado": "confirmada" if ci_lo > 1.5 else "rechazada" if ci_hi < 1.5 else "inconclusa",
        "frase": f"Gap de {gap:+.2f} pp (IC 95%: {ci_lo:+.2f} a {ci_hi:+.2f} pp)",
    }

    return h1, h2


if __name__ == "__main__":
    df = pd.read_csv("pisos.csv")
    resumen = calcular_resumen(df)
    resumen.to_csv("resumen.csv")
    print(resumen[["precio_m2", "renta_mes", "yield_bruto", "gap_vs_salamanca"]].to_string())

    h1, h2 = hipotesis(df, resumen)
    print("\nH1:", h1)
    print("H2:", h2)
