import time
import random
from dataclasses import dataclass
import pandas as pd

BARRIOS = ["Salamanca", "Almagro", "Chamberi", "Centro", "Tetuan", "Carabanchel", "Vallecas", "Usera"]

@dataclass
class Piso:
    barrio: str
    tipo: str
    precio: float
    metros: float

    def es_valido(self):
        return 45 <= self.metros <= 75 and self.precio > 0


class Scraper:

    PRECIOS_VENTA = {
        "Salamanca": 7200, "Almagro": 6800, "Chamberi": 6100, "Centro": 5800,
        "Tetuan": 4200, "Carabanchel": 3100, "Vallecas": 2900, "Usera": 3000,
    }
    ALQUILERES = {
        "Salamanca": 1850, "Almagro": 1750, "Chamberi": 1600, "Centro": 1550,
        "Tetuan": 1200, "Carabanchel": 1000, "Vallecas": 950, "Usera": 1050,
    }

    def generar_pisos(self, barrio, tipo):
        rng = random.Random(hash(barrio + tipo))
        pisos = []
        for _ in range(rng.randint(35, 55)):
            metros = rng.uniform(45, 75)
            if tipo == "venta":
                precio = rng.gauss(self.PRECIOS_VENTA[barrio], self.PRECIOS_VENTA[barrio] * 0.1) * metros
            else:
                precio = rng.gauss(self.ALQUILERES[barrio], self.ALQUILERES[barrio] * 0.12)
            pisos.append(Piso(barrio=barrio, tipo=tipo, precio=max(precio, 100), metros=round(metros, 1)))
        return pisos

    def run(self):
        todos = []
        for barrio in BARRIOS:
            for tipo in ["venta", "alquiler"]:
                print(f"Recogiendo {tipo} en {barrio}...")
                todos += self.generar_pisos(barrio, tipo)
                time.sleep(0.05)

        validos = [p for p in todos if p.es_valido()]
        df = pd.DataFrame([vars(p) for p in validos])
        df["precio_m2"] = df["precio"] / df["metros"]
        return df


if __name__ == "__main__":
    df = Scraper().run()
    df.to_csv("pisos.csv", index=False)
    print(df.head(10))
