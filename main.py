import heapq
import json
import pandas as pd
from scraper import Scraper
from processor import calcular_resumen, hipotesis
from visualizer import scatter, barras, gap_card, veredictos


class GrafoBarrios:

    def __init__(self, resumen):
        self.yields = resumen["yield_bruto"].to_dict()
        self.barrios = list(self.yields.keys())
        self.grafo = {b: [] for b in self.barrios}
        for i, a in enumerate(self.barrios):
            for b in self.barrios[i + 1:]:
                peso = abs(self.yields[a] - self.yields[b])
                self.grafo[a].append((peso, b))
                self.grafo[b].append((peso, a))

    def dijkstra(self, origen):
        dist = {b: float("inf") for b in self.barrios}
        dist[origen] = 0
        heap = [(0, origen)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for peso, v in self.grafo[u]:
                if dist[u] + peso < dist[v]:
                    dist[v] = dist[u] + peso
                    heapq.heappush(heap, (dist[v], v))
        return {k: round(v, 3) for k, v in dist.items()}

    def mas_parecido(self, barrio):
        dist = self.dijkstra(barrio)
        dist.pop(barrio)
        vecino = min(dist, key=dist.get)
        return vecino, dist[vecino]

    def clusters(self, umbral=0.5):
        visitados = set()
        grupos = []
        filtrado = {b: [n for p, n in vecinos if p <= umbral] for b, vecinos in self.grafo.items()}
        for inicio in self.barrios:
            if inicio in visitados:
                continue
            grupo = set()
            cola = [inicio]
            while cola:
                nodo = cola.pop()
                if nodo in visitados:
                    continue
                visitados.add(nodo)
                grupo.add(nodo)
                cola.extend(filtrado[nodo])
            grupos.append(grupo)
        return grupos


def main():
    print("=== Yield Inversión Madrid ===\n")

    print("1. Recogiendo pisos...")
    df = Scraper().run()
    df.to_csv("pisos.csv", index=False)

    print("\n2. Calculando yields...")
    resumen = calcular_resumen(df)
    resumen.to_csv("resumen.csv")
    print(resumen[["precio_m2", "renta_mes", "yield_bruto", "gap_vs_salamanca"]].to_string())

    print("\n3. Hipótesis...")
    h1, h2 = hipotesis(df, resumen)
    print("H1:", h1["resultado"], "| rho =", h1["rho"], "| p =", h1["p_valor"])
    print("H2:", h2["resultado"], "|", h2["frase"])

    with open("hipotesis.json", "w") as f:
        json.dump({"H1": h1, "H2": h2}, f, indent=2, ensure_ascii=False)

    print("\n4. Grafo de barrios...")
    grafo = GrafoBarrios(resumen)
    for b in grafo.barrios:
        vecino, dist = grafo.mas_parecido(b)
        print(f"  {b} → más parecido a {vecino} (diff yield: {dist:.2f} pp)")

    print("\n  Clusters (umbral ≤ 0.5 pp):")
    for grupo in grafo.clusters(umbral=0.5):
        print(" ", sorted(grupo))

    print("\n  Dijkstra desde Salamanca:")
    for barrio, d in sorted(grafo.dijkstra("Salamanca").items(), key=lambda x: x[1]):
        print(f"    {barrio}: {d:.3f} pp")

    print("\n5. Generando gráficos...")
    scatter(resumen)
    barras(resumen)
    ci = h2["ci_95"].strip("[]").split(", ")
    gap_card(h2["gap_pp"], float(ci[0]), float(ci[1]))
    veredictos(h1, h2)

    print("\nListo. Archivos generados:")
    for f in ["pisos.csv", "resumen.csv", "hipotesis.json",
              "grafico_scatter.png", "grafico_barras.png", "grafico_gap.png", "grafico_veredictos.png"]:
        print(f"  {f}")


if __name__ == "__main__":
    main()
