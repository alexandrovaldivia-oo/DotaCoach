"""Nombres legibles de objetos. Ampliar a medida que se usen.
Si un objeto no esta aqui, se muestra su nombre interno limpio."""

NOMBRES_OBJETOS = {
    "item_black_king_bar": "BKB",
    "item_blink": "Blink Dagger",
    "item_boots": "Botas de Velocidad",
    "item_magic_wand": "Magic Wand",
    "item_bottle": "Botella",
    "item_tpscroll": "Pergamino de Teletransporte",
    "item_power_treads": "Power Treads",
    "item_phase_boots": "Phase Boots",
    "item_force_staff": "Force Staff",
    "item_manta": "Manta Style",
    "item_desolator": "Desolator",
    "item_butterfly": "Butterfly",
}


def nombre_legible(clave):
    if clave in NOMBRES_OBJETOS:
        return NOMBRES_OBJETOS[clave]
    limpio = clave.replace("item_", "").replace("_", " ").strip()
    return limpio.title() if limpio else clave
