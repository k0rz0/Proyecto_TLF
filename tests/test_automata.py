"""
Casos de prueba para el módulo AFD y el Lexer.

Ejecutar:
    python tests/test_automata.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automata.dfa import DFA, DEAD_STATE
from lexical.lexer import Lexer
from lexical.token_types import TokenType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert(cond: bool, msg: str) -> int:
    if cond:
        print(f"  [PASS] {msg}")
        return 0
    else:
        print(f"  [FAIL] {msg}")
        return 1


# ---------------------------------------------------------------------------
# Test AFD base — binario divisible por 3
# ---------------------------------------------------------------------------

def test_dfa_binary_div3() -> int:
    """
    AFD clásico: acepta binarios divisibles por 3.
    q0=residuo0 (aceptación), q1=residuo1, q2=residuo2
    """
    print("\n== DFA Binario divisible por 3 ==")
    failures = 0

    def classify(c: str) -> str:
        return c if c in ("0", "1") else "ELSE"

    dfa = DFA(
        states={"q0", "q1", "q2"},
        alphabet={"0", "1", "ELSE"},
        transitions={
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q2", "1": "q0"},
            "q2": {"0": "q1", "1": "q2"},
        },
        initial_state="q0",
        accept_states={"q0"},
        char_classifier=classify,
        name="Div3",
    )

    # Casos válidos (divisible por 3)
    valid = [
        ("0",    "0 = 0"),
        ("11",   "11 = 3"),
        ("110",  "110 = 6"),
        ("1001", "1001 = 9"),
        ("1100", "1100 = 12"),
    ]
    for s, label in valid:
        failures += _assert(dfa.process(s), f"{label} → aceptada")

    # Casos inválidos
    invalid = [
        ("1",   "1 = 1"),
        ("10",  "10 = 2"),
        ("100", "100 = 4"),
        ("101", "101 = 5"),
    ]
    for s, label in invalid:
        failures += _assert(not dfa.process(s), f"{label} → rechazada")

    # Traza de "110"
    accepted, trace = dfa.process_with_trace("110")
    failures += _assert(accepted, "Traza de '110' aceptada")
    failures += _assert(len(trace) == 4, "Traza tiene 4 pasos (inicial + 3 chars)")
    print(f"  Traza '110':")
    for step in trace:
        print(f"    {step.to_str()}")

    return failures


# ---------------------------------------------------------------------------
# Test AFD — binario termina en '0' (FIX C5: ε debe ser rechazada)
# ---------------------------------------------------------------------------

def test_dfa_binary_ends0() -> int:
    """
    AFD que acepta cadenas binarias NO VACÍAS que terminan en '0'.

    Verifica la corrección C5: el estado inicial q_start NO es aceptador,
    por lo que la cadena vacía ε es rechazada.
    """
    print("\n== DFA Binario termina en '0' (FIX C5: rechaza ε) ==")
    failures = 0

    def classify(c: str) -> str:
        return c if c in ("0", "1") else "ELSE"

    dfa = DFA(
        states={"q_start", "q_par", "q_impar"},
        alphabet={"0", "1", "ELSE"},
        transitions={
            "q_start": {"0": "q_par",   "1": "q_impar"},
            "q_par":   {"0": "q_par",   "1": "q_impar"},
            "q_impar": {"0": "q_par",   "1": "q_impar"},
        },
        initial_state="q_start",
        accept_states={"q_par"},
        char_classifier=classify,
        name="Binario termina en 0",
    )

    # ε NO debe ser aceptada — verificación del fix C5
    failures += _assert(not dfa.process(""), "ε rechazada (cadena vacía)")

    # Válidos: no vacías y terminan en 0
    valid = [
        ("0",     "'0' acepta (un solo cero)"),
        ("10",    "'10' acepta"),
        ("110",   "'110' acepta"),
        ("1010",  "'1010' acepta"),
        ("00",    "'00' acepta"),
    ]
    for s, label in valid:
        failures += _assert(dfa.process(s), label)

    # Inválidos: terminan en 1 o vacías
    invalid = [
        ("1",    "'1' rechazada"),
        ("01",   "'01' rechazada"),
        ("11",   "'11' rechazada"),
        ("101",  "'101' rechazada"),
    ]
    for s, label in invalid:
        failures += _assert(not dfa.process(s), label)

    return failures


# ---------------------------------------------------------------------------
# Test AFD — Identificadores [a-z][a-z0-9_]*
# ---------------------------------------------------------------------------

def test_dfa_identifier() -> int:
    """
    AFD que reconoce identificadores: comienzan con letra minúscula,
    seguidos de letras minúsculas, dígitos o guión bajo.
    """
    print("\n== DFA Identificadores [a-z][a-z0-9_]* ==")
    failures = 0

    def classify(c: str) -> str:
        if "a" <= c <= "z":
            return "LOWER"
        if c.isdigit():
            return "DIGIT"
        if c == "_":
            return "UNDER"
        return "ELSE"

    dfa = DFA(
        states={"q0", "q1"},
        alphabet={"LOWER", "DIGIT", "UNDER", "ELSE"},
        transitions={
            "q0": {"LOWER": "q1"},
            "q1": {"LOWER": "q1", "DIGIT": "q1", "UNDER": "q1"},
        },
        initial_state="q0",
        accept_states={"q1"},
        char_classifier=classify,
        name="Identificadores",
    )

    valid = [
        "a",
        "abc",
        "variable",
        "var123",
        "my_var",
        "x_1_2",
        "nombre_completo",
    ]
    for s in valid:
        failures += _assert(dfa.process(s), f"{s!r} aceptada")

    invalid = [
        "",          # vacía
        "1abc",      # empieza con dígito
        "_var",      # empieza con guión bajo
        "ABC",       # letras mayúsculas → ELSE
        "var name",  # espacio → ELSE
        "var!",      # carácter especial → ELSE
    ]
    for s in invalid:
        failures += _assert(not dfa.process(s), f"{s!r} rechazada")

    # q1 es estado de aceptación, q0 no
    failures += _assert(dfa.delta("q0", "LOWER") == "q1", "δ(q0, LOWER) = q1")
    failures += _assert(dfa.delta("q0", "DIGIT") == DEAD_STATE, "δ(q0, DIGIT) = DEAD")
    failures += _assert(dfa.delta("q1", "DIGIT") == "q1", "δ(q1, DIGIT) = q1")

    return failures


# ---------------------------------------------------------------------------
# Test AFD — Números decimales [0-9]+(.[0-9]+)?
# ---------------------------------------------------------------------------

def test_dfa_decimal() -> int:
    """
    AFD que reconoce enteros y reales.
    Cadenas que terminan en '.' son rechazadas (q2 no es aceptador).
    """
    print("\n== DFA Números decimales [0-9]+(.[0-9]+)? ==")
    failures = 0

    def classify(c: str) -> str:
        if c.isdigit():
            return "DIGIT"
        if c == ".":
            return "DOT"
        return "ELSE"

    dfa = DFA(
        states={"q0", "q1", "q2", "q3"},
        alphabet={"DIGIT", "DOT", "ELSE"},
        transitions={
            "q0": {"DIGIT": "q1"},
            "q1": {"DIGIT": "q1", "DOT": "q2"},
            "q2": {"DIGIT": "q3"},
            "q3": {"DIGIT": "q3"},
        },
        initial_state="q0",
        accept_states={"q1", "q3"},
        char_classifier=classify,
        name="Decimales",
    )

    valid = [
        "0",
        "42",
        "123",
        "3.14",
        "0.5",
        "100.001",
        "9999.9999",
    ]
    for s in valid:
        failures += _assert(dfa.process(s), f"{s!r} aceptada")

    invalid = [
        "",       # vacía
        ".",      # solo punto
        "1.",     # termina en punto (q2 no acepta)
        ".5",     # empieza con punto
        "1.2.3",  # dos puntos — después de q3, DOT → DEAD
        "abc",
        "1a2",
    ]
    for s in invalid:
        failures += _assert(not dfa.process(s), f"{s!r} rechazada")

    # Verificar que q2 no es aceptador
    failures += _assert("q2" not in dfa.accept_states, "q2 no es estado de aceptación")
    failures += _assert("q1" in dfa.accept_states,     "q1 es estado de aceptación")
    failures += _assert("q3" in dfa.accept_states,     "q3 es estado de aceptación")

    return failures


# ---------------------------------------------------------------------------
# Test AFD — función de transición
# ---------------------------------------------------------------------------

def test_dfa_delta() -> int:
    """Prueba directa de la función δ."""
    print("\n== Test función δ ==")
    failures = 0

    def classify(c: str) -> str:
        return "A" if c == "a" else ("B" if c == "b" else "ELSE")

    # AFD sencillo: acepta cadenas que terminan en 'a'
    dfa = DFA(
        states={"q0", "q1"},
        alphabet={"A", "B", "ELSE"},
        transitions={
            "q0": {"A": "q1", "B": "q0"},
            "q1": {"A": "q1", "B": "q0"},
        },
        initial_state="q0",
        accept_states={"q1"},
        char_classifier=classify,
    )

    failures += _assert(dfa.delta("q0", "A") == "q1",    "δ(q0, A) = q1")
    failures += _assert(dfa.delta("q0", "B") == "q0",    "δ(q0, B) = q0")
    failures += _assert(dfa.delta("q1", "B") == "q0",    "δ(q1, B) = q0")
    failures += _assert(dfa.delta("q0", "ELSE") == DEAD_STATE, "δ(q0, ELSE) = DEAD")
    failures += _assert(dfa.delta(DEAD_STATE, "A") == DEAD_STATE, "δ(DEAD, A) = DEAD")

    failures += _assert(dfa.process("a"),    "'a' aceptada")
    failures += _assert(dfa.process("ba"),   "'ba' aceptada")
    failures += _assert(dfa.process("bba"),  "'bba' aceptada")
    failures += _assert(not dfa.process("b"),   "'b' rechazada")
    failures += _assert(not dfa.process("ab"),  "'ab' rechazada")
    failures += _assert(not dfa.process(""),    "'' rechazada")

    return failures


# ---------------------------------------------------------------------------
# Test tabla de transiciones
# ---------------------------------------------------------------------------

def test_transition_table() -> int:
    """Verifica que la tabla generada tenga la forma correcta."""
    print("\n== Test tabla de transiciones ==")
    failures = 0

    def classify(c: str) -> str:
        return c if c in ("0", "1") else "ELSE"

    dfa = DFA(
        states={"q0", "q1"},
        alphabet={"0", "1", "ELSE"},
        transitions={
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q0", "1": "q1"},
        },
        initial_state="q0",
        accept_states={"q1"},
        char_classifier=classify,
    )

    table = dfa.get_transition_table()
    failures += _assert("states"   in table, "Tabla tiene 'states'")
    failures += _assert("alphabet" in table, "Tabla tiene 'alphabet'")
    failures += _assert("rows"     in table, "Tabla tiene 'rows'")
    failures += _assert("q0" in table["states"], "q0 en states")
    failures += _assert("q1" in table["states"], "q1 en states")
    failures += _assert(DEAD_STATE not in table["states"], "DEAD no aparece en tabla")

    return failures


# ---------------------------------------------------------------------------
# Test AFD de contraseña — construcción de conjunto potencia (16 estados)
# ---------------------------------------------------------------------------

def test_dfa_password_powerset() -> int:
    """
    Verifica el AFD de contraseña:
    - 16 estados (S0000…S1111)
    - Estado inicial S0000
    - Único estado de aceptación S1111
    - Cada símbolo activa el bit correspondiente (monotónico)
    """
    print("\n== DFA Contraseña — Conjunto potencia (16 estados) ==")
    failures = 0

    from validators.password_validator import PasswordValidator
    dfa = PasswordValidator().dfa

    # dfa.states incluye DEAD_STATE implícito → 16 máscara + 1 DEAD = 17 total
    non_dead = dfa.states - {DEAD_STATE}
    failures += _assert(len(non_dead) == 16, f"16 estados de conjunto potencia (hay {len(non_dead)})")
    failures += _assert(dfa.initial_state == "S0000", "Estado inicial S0000")
    failures += _assert(dfa.accept_states == {"S1111"}, "Único aceptador S1111")

    # Clasificar cadena con todos los tipos de carácter → debe llegar a S1111
    failures += _assert(dfa.process("Aa1@"), "Aa1@ → S1111 (todos los bits)")

    # Sin mayúscula → máscara sin bit0 → no alcanza S1111
    failures += _assert(not dfa.process("aa1@"), "aa1@ rechazada (sin mayúscula)")

    # Sin minúscula → máscara sin bit1
    failures += _assert(not dfa.process("AA1@"), "AA1@ rechazada (sin minúscula)")

    # Sin dígito → máscara sin bit2
    failures += _assert(not dfa.process("Aa!#"), "Aa!# rechazada (sin dígito)")

    # Sin especial → máscara sin bit3
    failures += _assert(not dfa.process("Aa12"), "Aa12 rechazada (sin especial)")

    # Cadena vacía → permanece en S0000 (no acepta)
    failures += _assert(not dfa.process(""), "ε rechazada")

    # Monotonía: los estados solo avanzan (bits se suman, nunca se quitan)
    accepted, trace = dfa.process_with_trace("A")
    # Después de 'A' (UPPER, bit0=1) el estado debe ser S0001
    if len(trace) >= 2:
        failures += _assert(trace[1].to_state == "S0001",
                            f"Después de 'A' → S0001 (actual: {trace[1].to_state})")

    return failures


# ---------------------------------------------------------------------------
# Test Lexer con texto de ejemplo
# ---------------------------------------------------------------------------

def test_lexer() -> int:
    """Prueba el Lexer con un texto que contiene múltiples tokens."""
    print("\n== Test Lexer ==")
    failures = 0

    lexer = Lexer()
    text = (
        "Contacto: info@empresa.com "
        "Tel: 3001234567 "
        "Web: https://www.empresa.com "
        "Fecha: 25/12/2024 "
        "Placa: ABC123"
    )

    tokens = lexer.tokenize_word_boundary(text)
    token_types = {t.type for t in tokens}

    failures += _assert(TokenType.EMAIL  in token_types, "EMAIL encontrado")
    failures += _assert(TokenType.PHONE  in token_types, "PHONE encontrado")
    failures += _assert(TokenType.URL    in token_types, "URL encontrada")
    failures += _assert(TokenType.DATE   in token_types, "DATE encontrada")
    failures += _assert(TokenType.PLATE  in token_types, "PLATE encontrada")

    print(f"  Tokens encontrados: {len(tokens)}")
    for tok in tokens:
        mark = "✓" if tok.is_valid else "✗"
        print(f"    {mark} [{tok.type.label():<12}] {tok.value!r}")

    # Verificar stats
    stats = lexer.stats
    failures += _assert(stats.total_tokens == len(tokens), "Stats.total coincide")

    # Texto con dominio que empieza en 't' — verifica fix C1 del URL validator
    lexer2 = Lexer()
    text2 = "Visita https://test.com para más info"
    tokens2 = lexer2.tokenize_word_boundary(text2)
    url_tokens = [t for t in tokens2 if t.type == TokenType.URL]
    failures += _assert(len(url_tokens) > 0, "URL con dominio 't' (test.com) encontrada")
    if url_tokens:
        failures += _assert(url_tokens[0].is_valid, "https://test.com es válida")

    return failures


# ---------------------------------------------------------------------------
# Test find_longest_match
# ---------------------------------------------------------------------------

def test_longest_match() -> int:
    """Prueba la búsqueda de coincidencia más larga."""
    print("\n== Test find_longest_match ==")
    failures = 0

    from validators.email_validator import EmailValidator
    v = EmailValidator()

    text = "user@example.com resto del texto"
    end = v.find_longest_match(text, 0)
    failures += _assert(end == len("user@example.com"), f"Longitud correcta: {end}")

    # Sin coincidencia
    end2 = v.find_longest_match("sin_arroba_aqui", 0)
    failures += _assert(end2 == 0, f"Sin coincidencia retorna 0: {end2}")

    # URL con dominio iniciando en 't' — verifica fix C1
    from validators.url_validator import UrlValidator
    url_v = UrlValidator()
    url_text = "https://test.com"
    end3 = url_v.find_longest_match(url_text, 0)
    failures += _assert(end3 == len(url_text), f"URL test.com longitud correcta: {end3}")

    return failures


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    total = 0
    total += test_dfa_binary_div3()
    total += test_dfa_binary_ends0()
    total += test_dfa_identifier()
    total += test_dfa_decimal()
    total += test_dfa_delta()
    total += test_transition_table()
    total += test_dfa_password_powerset()
    total += test_lexer()
    total += test_longest_match()

    print(f"\n{'='*55}")
    if total == 0:
        print("  ✅ TODOS LOS TESTS DEL AFD Y LEXER PASARON")
    else:
        print(f"  ❌ {total} FALLO(S) EN TESTS DE AUTÓMATA/LEXER")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
