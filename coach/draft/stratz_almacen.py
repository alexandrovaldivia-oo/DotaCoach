"""SQLite experimental. Solo publica lotes completos en una transaccion."""
import sqlite3
from pathlib import Path

class AlmacenStratz:
    def __init__(self, ruta):
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(ruta)
        self.db.executescript('''CREATE TABLE IF NOT EXISTS relaciones_v1 (
            semana INTEGER, rango_solicitado TEXT, heroe INTEGER, relacion TEXT,
            otro INTEGER, rango_devuelto TEXT, partidas INTEGER, victorias INTEGER,
            synergy REAL, base1 REAL, base2 REAL,
            PRIMARY KEY(semana,rango_solicitado,heroe,relacion,otro));
        CREATE TABLE IF NOT EXISTS lotes_v1 (
            semana INTEGER, rango TEXT, heroe INTEGER, cantidad INTEGER,
            PRIMARY KEY(semana,rango,heroe));''')

    def guardar(self, semana, rango, heroe, filas):
        with self.db:
            self.db.execute('DELETE FROM relaciones_v1 WHERE semana=? AND rango_solicitado=? AND heroe=?', (semana,rango,heroe))
            self.db.executemany('INSERT INTO relaciones_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                [(semana,rango,heroe,*f) for f in filas])
            self.db.execute('INSERT OR REPLACE INTO lotes_v1 VALUES (?,?,?,?)', (semana,rango,heroe,len(filas)))

    def completo(self, semana, rango, heroe, ids):
        filas = self.db.execute('SELECT relacion,otro FROM relaciones_v1 WHERE semana=? AND rango_solicitado=? AND heroe=?', (semana,rango,heroe)).fetchall()
        return set(filas) == {(r,i) for r in ('with','vs') for i in set(ids)-{heroe}} and bool(filas)

    def cerrar(self):
        self.db.close()
