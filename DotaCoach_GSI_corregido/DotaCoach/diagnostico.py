"""Punto de entrada del diagnostico (se compila como DotaDiagnostico.exe)."""
import traceback


def esperar():
    try:
        input("\nPulsa Enter para cerrar...")
    except EOFError:
        pass


if __name__ == "__main__":
    try:
        from coach import config
        from coach.diagnostico import ejecutar
        ejecutar(config.cargar())
    except Exception:
        traceback.print_exc()
    esperar()
