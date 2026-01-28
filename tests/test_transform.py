from src_old.entities.transform import categorize, normalize_literal


def test_normalize_literal_basic():
    assert normalize_literal("  Hola   Mundo  ") == "hola mundo"


def test_normalize_literal_keeps_punctuation():
    assert normalize_literal("Hola!!!  ") == "hola!!!"


def test_categorize_saludo():
    assert categorize("Hola, buen dia") == "saludo"


def test_categorize_precio():
    assert categorize("Cual es el precio?") == "precio"


def test_categorize_cotizacion():
    assert categorize("Necesito cotizacion") == "cotizacion"


def test_categorize_estado_pedido():
    assert categorize("Quiero el estado del pedido") == "estado_pedido"


def test_categorize_reclamo():
    assert categorize("Tengo un reclamo") == "reclamo"


def test_categorize_otro():
    assert categorize("Solo queria saludar") == "otro"
