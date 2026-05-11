"""
Casos de prueba para todos los validadores.

Ejecutar:
    python -m pytest tests/ -v
    o
    python tests/test_validators.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators import (
    EmailValidator,
    PhoneValidator,
    DateValidator,
    UrlValidator,
    PasswordValidator,
    PlateValidator,
    UsernameValidator,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_cases(validator, valid_cases, invalid_cases, name: str) -> int:
    failures = 0
    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")

    print("\n  ✅ Casos VÁLIDOS:")
    for val in valid_cases:
        result = validator.validate(val)
        ok = result.is_valid
        mark = "PASS" if ok else "FAIL"
        print(f"    [{mark}] {val!r:<35} → {result.summary()[:50]}")
        if not ok:
            failures += 1
            for e in result.errors:
                print(f"           ✗ {e}")

    print("\n  ❌ Casos INVÁLIDOS:")
    for val in invalid_cases:
        result = validator.validate(val)
        ok = not result.is_valid
        mark = "PASS" if ok else "FAIL"
        print(f"    [{mark}] {val!r:<35} → {'Rechazado correctamente' if ok else 'ERROR: aceptado'}")
        if not ok:
            failures += 1

    return failures


# ---------------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------------

def test_email() -> int:
    v = EmailValidator()
    valid = [
        "user@example.com",
        "nombre.apellido@empresa.co",
        "admin@universidad.edu.co",
        "test123@correo.org",
        "a@b.io",
        "user_name-123@sub.domain.net",
        # Dominios con letras que el clasificador trata especialmente (t, p, s)
        "info@test.com",
        "me@python.org",
        "sales@shop.io",
    ]
    invalid = [
        "usuario@",           # sin dominio
        "@dominio.com",       # sin usuario
        "sin_arroba.com",     # sin @
        "user@@dom.com",      # doble @
        "user@dom",           # sin extensión
        "user@.com",          # dominio vacío
        "",                   # vacío
        "us er@dom.com",      # espacio
        "user@dom.",          # punto al final (extensión vacía)
    ]
    return _run_cases(v, valid, invalid, "EMAIL VALIDATOR")


# ---------------------------------------------------------------------------
# TELÉFONO
# ---------------------------------------------------------------------------

def test_phone() -> int:
    v = PhoneValidator()
    valid = [
        "3001234567",
        "3219876543",
        "+573001234567",
        "+573219876543",
        "300-123-4567",
        "321-987-6543",
        "3500000000",         # otro prefijo válido (35x)
        "+573500000001",      # +57 + número que empieza en 3
    ]
    invalid = [
        "123456789",          # no empieza con 3
        "30012345",           # muy corto
        "300123456789",       # muy largo
        "+593001234567",      # indicativo +59 (Ecuador), no +57 — C6 fix
        "+563001234567",      # indicativo +56 (Chile), no +57 — C6 fix
        "+583001234567",      # indicativo +58 (Venezuela), no +57
        "+573",               # incompleto
        "3001234a67",         # letra en medio
        "+570001234567",      # después de +57 no empieza en 3
        "",
    ]
    return _run_cases(v, valid, invalid, "PHONE VALIDATOR")


# ---------------------------------------------------------------------------
# FECHA
# ---------------------------------------------------------------------------

def test_date() -> int:
    v = DateValidator()
    valid = [
        "01/01/2024",
        "31/12/2023",
        "29/02/2024",         # 2024 es bisiesto (÷4, no ÷100)
        "29/02/2000",         # 2000 es bisiesto (÷400)
        "28/02/2100",         # 2100 no es bisiesto → día 28 válido
        "2024-06-15",
        "2023-12-31",
        "2000-01-01",
        "2000-02-29",         # 2000 bisiesto en formato F2
        "1900-03-01",         # 1900 no bisiesto (÷100 pero no ÷400) → 1 de marzo ok
    ]
    invalid = [
        "32/01/2024",         # día inválido
        "01/13/2024",         # mes inválido
        "29/02/2023",         # 2023 no es bisiesto
        "29/02/2100",         # 2100 no es bisiesto (÷100, no ÷400)
        "29/02/1900",         # 1900 no es bisiesto
        "2024/01/01",         # separador incorrecto
        "15-06-2024",         # formato mezclado (DD-MM-YYYY no soportado)
        "01-01-24",           # año corto
        "abc",
        "",
    ]
    return _run_cases(v, valid, invalid, "DATE VALIDATOR")


# ---------------------------------------------------------------------------
# URL
# ---------------------------------------------------------------------------

def test_url() -> int:
    v = UrlValidator()
    valid = [
        "http://example.com",
        "https://www.google.com",
        "https://portal.gov.co/pagina",
        "http://sub.domain.org/path?q=1",
        "https://api.site.io",
        # Dominios que comienzan con letras t, p, s — verificación FIX C1
        "https://test.com",
        "http://python.org",
        "https://shop.io",
        "http://super.dev",
        "https://t.co",          # dominio de una letra
        "https://python.example.com",
        "http://stackoverflow.com/questions/123",
        "https://support.apple.com",
    ]
    invalid = [
        "ftp://example.com",     # protocolo no soportado
        "http://",               # sin dominio
        "http://nodot",          # sin extensión
        "www.example.com",       # sin protocolo
        "http://example.c",      # extensión de 1 carácter
        "https://.com",          # dominio vacío
        "",
    ]
    return _run_cases(v, valid, invalid, "URL VALIDATOR")


# ---------------------------------------------------------------------------
# CONTRASEÑA
# ---------------------------------------------------------------------------

def test_password() -> int:
    v = PasswordValidator()
    valid = [
        "Mi$Clave2024",
        "Segur@Pass1",
        "Ab1!cdef",              # exactamente 8 caracteres — longitud mínima
        "P@ssw0rd",
        "Tr0ub4d0r&3",
        "X1$aaaaa",              # 8 chars: 1 mayo, 1 spec, 1 digit, 5 lower
    ]
    invalid = [
        "password",              # sin mayúscula, dígito, especial
        "PASSWORD1!",            # sin minúscula
        "Password!",             # sin dígito
        "Password1",             # sin especial
        "Mi$c1",                 # muy corto (6 chars)
        "Ab1!cde",               # 7 caracteres — un menos del mínimo
        "aaaaaaaa",              # solo minúsculas
        "AAAAAAAA",              # solo mayúsculas
        "12345678",              # solo dígitos
        "!@#$%^&*",              # solo especiales
        "",
    ]
    return _run_cases(v, valid, invalid, "PASSWORD VALIDATOR")


# ---------------------------------------------------------------------------
# PLACA
# ---------------------------------------------------------------------------

def test_plate() -> int:
    v = PlateValidator()
    valid = [
        "ABC123",
        "XYZ999",
        "AAA000",
        "ZZZ45T",               # formato moto: 3 letras + 2 dígitos + 1 letra
        "ABC12D",
    ]
    invalid = [
        "AB1234",               # solo 2 letras al inicio
        "ABCD123",              # 4 letras
        "ABC12",                # solo 5 chars
        "abc123",               # letras minúsculas
        "123ABC",               # empieza con número
        "ABC12!",               # carácter especial
        "",
    ]
    return _run_cases(v, valid, invalid, "PLATE VALIDATOR")


# ---------------------------------------------------------------------------
# USUARIO
# ---------------------------------------------------------------------------

def test_username() -> int:
    v = UsernameValidator()
    valid = [
        "john_doe",
        "user123",
        "Carlos.Lopez",
        "dev-team",
        "abc",                  # longitud mínima exacta (3)
        "usuario_admin",
        "a" * 20,               # longitud máxima exacta (20)
    ]
    invalid = [
        "1user",                # empieza con dígito
        "ab",                   # muy corto (2 chars)
        "user name",            # espacio
        "_user",                # empieza con _
        "u" * 21,               # muy largo (21 chars)
        "-user",                # empieza con guión
        ".user",                # empieza con punto
        "",
    ]
    return _run_cases(v, valid, invalid, "USERNAME VALIDATOR")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    total_failures = 0
    total_failures += test_email()
    total_failures += test_phone()
    total_failures += test_date()
    total_failures += test_url()
    total_failures += test_password()
    total_failures += test_plate()
    total_failures += test_username()

    print(f"\n{'='*55}")
    if total_failures == 0:
        print("  ✅ TODOS LOS TESTS PASARON")
    else:
        print(f"  ❌ {total_failures} FALLO(S) ENCONTRADO(S)")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
