# Analizador Léxico y Sintáctico — Teoría de Lenguajes Formales

Proyecto final del curso **Teoría de Lenguajes Formales / Autómatas / Análisis Léxico y Sintáctico**.

Aplicación de escritorio en Python que implementa **Autómatas Finitos Deterministas (AFD)**, análisis léxico y análisis sintáctico **sin usar la librería `re`** de Python.

---

## Instalación y ejecución paso a paso

### Paso 1 — Instalar Python

1. Ve a **https://www.python.org/downloads/** y descarga **Python 3.11** o **3.12** para Windows.
2. Ejecuta el instalador.
3. **MUY IMPORTANTE:** en la primera pantalla del instalador, marca la casilla **"Add Python to PATH"** antes de hacer clic en *Install Now*.

   ```
   [ ] Install launcher for all users
   [x] Add Python to PATH      ← MARCAR ESTA
   ```

4. Una vez instalado, **abre una terminal nueva** (PowerShell o cmd) y verifica:

   ```powershell
   python --version
   ```

   Debe mostrar algo como: `Python 3.12.3`

   > Si sigue diciendo que no se encontró Python, reinicia el equipo para que el PATH se actualice.

---

### Paso 2 — Abrir el proyecto

Abre **PowerShell** y navega a la carpeta del proyecto:

```powershell
cd C:\Users\leoga\workspace\proyectos\TLF
```

Confirma que estás en la carpeta correcta listando los archivos:

```powershell
ls
```

Debes ver `main.py`, las carpetas `gui/`, `validators/`, `automata/`, etc.

---

### Paso 3 — Ejecutar la aplicación

```powershell
python main.py
```

Aparecerá la ventana principal de la aplicación con tres pestañas.

> La aplicación **no requiere instalar ninguna librería externa**. Usa únicamente `tkinter`, que viene incluido con Python.

---

### Paso 4 — Ejecutar los tests (opcional pero recomendado)

```powershell
# Tests de todos los validadores (EMAIL, TELÉFONO, FECHA, URL, CONTRASEÑA, PLACA, USUARIO):
python tests/test_validators.py

# Tests del motor AFD y el Lexer:
python tests/test_automata.py
```

Al final de cada test verás:
```
=======================================================
  ✅ TODOS LOS TESTS PASARON
=======================================================
```

---

### Resumen rápido

| Acción | Comando |
|--------|---------|
| Verificar Python | `python --version` |
| Correr la app | `python main.py` |
| Tests validadores | `python tests/test_validators.py` |
| Tests autómatas | `python tests/test_automata.py` |

---

## Visita guiada al proyecto

Esta sección recorre **cada archivo y módulo** explicando qué hace, qué concepto teórico implementa y qué requisito del proyecto cumple.

---

### Estructura de carpetas

```
TLF/
│
├── main.py                        # Punto de entrada
│
├── automata/
│   └── dfa.py                     # ★ Motor AFD — núcleo del proyecto
│
├── validators/
│   ├── base.py                    # Clase abstracta BaseValidator
│   ├── email_validator.py         # AFD correo electrónico
│   ├── phone_validator.py         # AFD teléfono colombiano
│   ├── date_validator.py          # AFD fecha (dos formatos)
│   ├── url_validator.py           # AFD URL http/https
│   ├── password_validator.py      # AFD conjunto potencia (16 estados)
│   ├── plate_validator.py         # AFD placa colombiana
│   └── username_validator.py      # AFD nombre de usuario
│
├── lexical/
│   ├── token_types.py             # Enum TokenType + dataclass Token
│   └── lexer.py                   # ★ Analizador léxico — maximal munch
│
├── syntax/
│   ├── syntax_tree.py             # Árbol sintáctico n-ario
│   └── parser.py                  # ★ Analizador sintáctico — gramáticas BNF
│
├── utils/
│   ├── history.py                 # Historial persistente en JSON
│   └── exporter.py                # Exportación a TXT, CSV, JSON
│
├── gui/
│   ├── main_window.py             # Ventana principal
│   ├── tab_search.py              # Pestaña 1 — Búsqueda en texto
│   ├── tab_form.py                # Pestaña 2 — Formulario interactivo
│   ├── tab_automata.py            # Pestaña 3 — Simulador AFD visual
│   └── components/
│       └── result_panel.py        # Panel de resultados reutilizable
│
└── tests/
    ├── test_validators.py         # Suite de pruebas — validadores
    └── test_automata.py           # Suite de pruebas — autómatas y lexer
```

---

### `automata/dfa.py` — Motor AFD

**Requisito que cumple:** Implementación formal de Autómatas Finitos Deterministas.

Este es el núcleo del proyecto. Define la clase `DFA` que representa la quíntupla formal:

```
M = (Q, Σ, δ, q0, F)

  Q  → states        Conjunto finito de estados
  Σ  → alphabet      Alfabeto de clases de caracteres
  δ  → transitions   Función de transición Q × Σ → Q
  q0 → initial_state Estado inicial
  F  → accept_states Conjunto de estados de aceptación
```

**Puntos clave de la implementación:**

- **Clases de caracteres:** `δ` opera sobre clases (`ALPHA`, `DIGIT`, `DOT`…) en lugar de caracteres individuales. Así un arco `ALPHA → q1` cubre todas las letras del alfabeto con una sola transición.
- **Estado trampa:** Toda transición no definida va implícitamente al `DEAD_STATE`. Si el autómata llega ahí, no puede salir.
- **`process(cadena)`:** Recorre la cadena y retorna `True/False`.
- **`process_with_trace(cadena)`:** Lo mismo pero devuelve la lista completa de `TransitionStep`, registrando en cada paso: estado origen, carácter leído, clase del carácter, estado destino, y si se aceptó o murió.
- **`find_longest_match(texto, inicio)`:** Recorre el texto desde `inicio` y retorna la posición donde el AFD aceptó por última vez. Esto es lo que usa el Lexer para el maximal munch.

---

### `validators/` — Los 7 Validadores

**Requisito que cumple:** Un AFD específico por cada patrón, con análisis en dos fases.

Cada validador hereda de `BaseValidator` y sigue el mismo patrón:

1. **Fase léxica (AFD):** verifica que la estructura carácter a carácter es correcta.
2. **Fase sintáctica:** verifica rangos y semántica (ej. que el mes no sea 13).

#### `email_validator.py` — 6 estados

```
AFD de correo: [a-zA-Z0-9._-]+  @  [a-zA-Z0-9-]+  .  [a-zA-Z]{2,}

q0 → q1 (primer char del usuario)
q1 → q1 (más chars del usuario) | q2 (@)
q2 → q3 (primer char del dominio)
q3 → q3 (más chars del dominio) | q4 (punto separador)
q4 → q5 (primer char de extensión)  ★ ACEPTACIÓN
q5 → q5 (más chars de extensión)    ★ ACEPTACIÓN
```

Análisis sintáctico: extrae `usuario`, `dominio` y `extensión` como componentes.

---

#### `phone_validator.py` — 23 estados, 3 formatos

```
F1: 3001234567          (10 dígitos, empieza con 3)
F2: +573001234567       (indicativo +57 + F1)
F3: 300-123-4567        (grupos con guiones)
```

Detalle del camino F2 (indicativo exacto):
```
q0 → PLUS → CC5 → CC7 → D1 → … → D10 ★
          ↑     ↑
       solo '5'  solo '7'   (no acepta +59, +56, etc.)
```

Los estados `CC5` y `CC7` aceptan **únicamente** los dígitos `'5'` y `'7'` respectivamente, garantizando que solo `+57` (Colombia) sea válido.

---

#### `date_validator.py` — 19 estados, 2 formatos

```
F1: DD/MM/YYYY   →  bifurcación en A2 + SLASH
F2: YYYY-MM-DD   →  bifurcación en A2 + DIGIT
```

Los dos formatos comparten los primeros dos estados (`A1`, `A2`) y se bifurcan:
- `A2 + SLASH` → camino F1
- `A2 + DIGIT` → camino F2

Análisis sintáctico: valida rangos (1≤día≤31, 1≤mes≤12) y **años bisiestos** (regla divisible-por-4 con excepciones para siglos).

---

#### `url_validator.py` — 13 estados

```
Camino del protocolo:  q0 -h→ H1 -t→ H2 -t→ H3 -p→ H4
                       H4 -s→ HS -:→ C1   (https)
                       H4 -:→ C1          (http)
Separador "://":       C1 -/→ C2 -/→ D0
Dominio:               D0 → D1 → … → DOT → E1 ★
Ruta opcional:         E1 -/→ PATH ★
```

Análisis sintáctico: extrae `protocolo`, `dominio`, `extensión` y `ruta`.

---

#### `password_validator.py` — Construcción de Conjunto Potencia (16 estados)

Este es el validador teóricamente más sofisticado. Como un AFD lineal no puede verificar la **co-ocurrencia** de cuatro categorías sin explotar el número de estados, se usa la **construcción de conjunto potencia**:

```
Cada estado codifica en 4 bits qué categorías se han visto:

  bit 0 (valor 1) → ha visto MAYÚSCULA  [A-Z]
  bit 1 (valor 2) → ha visto MINÚSCULA  [a-z]
  bit 2 (valor 4) → ha visto DÍGITO     [0-9]
  bit 3 (valor 8) → ha visto ESPECIAL   [@$!%*?&…]

  Estados: S0000, S0001, S0010, … S1111   (16 estados = 2⁴)

  Función de transición:
    δ(Sxxxx, UPPER)   = S(xxxx | 0001)   ← activa bit 0
    δ(Sxxxx, LOWER)   = S(xxxx | 0010)   ← activa bit 1
    δ(Sxxxx, DIGIT)   = S(xxxx | 0100)   ← activa bit 2
    δ(Sxxxx, SPECIAL) = S(xxxx | 1000)   ← activa bit 3
    δ(Sxxxx, OTHER)   = S(xxxx)          ← sin cambio

  Estado inicial:    S0000
  Estado aceptador:  S1111  (todos los bits activados)
```

La longitud mínima (8 caracteres) se verifica en la fase sintáctica porque los AFDs puros no cuentan sin añadir estados adicionales.

---

#### `plate_validator.py` — Placas colombianas

```
Formato auto:  [A-Z]{3}[0-9]{3}   →  ABC123
Formato moto:  [A-Z]{3}[0-9]{2}[A-Z]  →  ABC12D
```

---

#### `username_validator.py` — Identificadores de usuario

```
Regla: comienza con letra, seguido de letras/dígitos/._-
       longitud entre 3 y 20 caracteres
```

---

### `lexical/` — Analizador Léxico

**Requisito que cumple:** Análisis léxico con la estrategia de máxima coincidencia (maximal munch).

#### `token_types.py`

Define el `Enum TokenType` con los 7 tipos de token (`EMAIL`, `PHONE`, `DATE`, `URL`, `PLATE`, `USERNAME`, `PASSWORD`). Cada tipo lleva su etiqueta en español, su color para la UI y su expresión regular **teórica** equivalente (solo documentativa — nunca se pasa a `re`).

La clase `Token` es un `dataclass` con todos los datos de un token identificado: tipo, valor, posición inicio/fin, si es válido, línea y columna.

#### `lexer.py` — Maximal Munch

Implementa el algoritmo estándar de los scanners de compiladores:

```
Para cada posición i en el texto:
  1. Ejecutar los AFDs de los 7 validadores desde i
  2. Cada AFD retorna la longitud de la coincidencia más larga
  3. Tomar el candidato más largo
  4. Si hay candidato → emitir Token, avanzar i hasta el fin del token
  5. Si no             → carácter no reconocido, avanzar i en 1
```

El orden de los validadores importa para desambiguar: `URL` va antes que `EMAIL` para que `https://user@host.com` se reconozca como URL y no como email.

La clase `LexerStats` acumula estadísticas: total de tokens, cuántos son válidos/inválidos, conteo por tipo, y caracteres que ningún AFD reconoció.

---

### `syntax/` — Analizador Sintáctico

**Requisito que cumple:** Análisis sintáctico con gramáticas BNF y árboles sintácticos.

#### `syntax_tree.py`

Árbol n-ario donde:
- La **raíz** es el tipo de token (`EMAIL`, `URL`…)
- Los **nodos internos** son constituyentes (`dominio`, `ruta`…)
- Las **hojas** son los valores terminales (`"user"`, `"@"`, `".com"`)

Método `display()` genera la representación visual con sangría:

```
EMAIL
├── usuario: "john.doe"
├── @: "@"
└── dominio
    ├── nombre: "empresa"
    ├── .: "."
    └── extensión: "com"
```

#### `parser.py`

Toma la lista de tokens del Lexer e invoca el validador correspondiente para obtener el `syntax_tree` ya construido. Retorna un `ParseResult` con el token, el resultado de validación, el árbol y la gramática BNF aplicada.

Gramáticas BNF documentadas en el parser (ejemplos):

```bnf
EMAIL:
  <email>     ::= <usuario> "@" <dominio>
  <dominio>   ::= <nombre> "." <extensión>

URL:
  <url>       ::= <protocolo> "://" <host> [ "/" <ruta> ]
  <protocolo> ::= "http" | "https"

FECHA:
  <fecha>     ::= <DD> "/" <MM> "/" <YYYY>
               |  <YYYY> "-" <MM> "-" <DD>
```

---

### `gui/` — Interfaz Gráfica

**Requisito que cumple:** Tres módulos de interfaz con visualización completa de resultados.

#### Pestaña 1 — Búsqueda en Texto (`tab_search.py`)

- Área de texto donde el usuario escribe o pega contenido libre.
- Botón para cargar archivos `.txt` del sistema.
- Al hacer clic en **Analizar**, el Lexer recorre todo el texto con maximal munch y lista todos los tokens encontrados con su tipo, valor, posición y estado de validez.
- Panel lateral muestra el árbol sintáctico del token seleccionado.
- Exportación de resultados a **TXT**, **CSV** o **JSON**.
- Historial de las últimas búsquedas.

#### Pestaña 2 — Formulario Interactivo (`tab_form.py`)

- Campos para: nombre, correo, teléfono, fecha de nacimiento, sitio web, nombre de usuario y contraseña.
- **Validación en tiempo real** mientras el usuario escribe (traza de evento `<KeyRelease>`).
- Retroalimentación visual inmediata:
  - Fondo **verde** → válido
  - Fondo **rojo** → inválido, con el mensaje de error específico
  - Fondo **blanco** → sin contenido aún
- Barra de **fortaleza de contraseña** (Muy débil → Muy fuerte) calculada en vivo.
- Panel lateral con el árbol sintáctico del campo que se está editando.
- Botón **Enviar** habilitado únicamente cuando todos los campos son válidos.

#### Pestaña 3 — Simulador AFD (`tab_automata.py`)

- **Catálogo de 9 AFDs** seleccionables desde un menú desplegable:
  - 5 de los validadores reales (Email, Teléfono, Fecha, URL, Placa)
  - 4 AFDs teóricos clásicos (Binario ÷3, Binario termina en '0', Identificadores, Números decimales)
- **Tabla de transiciones δ** completa con marcadores `→` (estado inicial) y `★` (estado aceptador).
- **Visualización gráfica** del AFD en canvas:
  - Círculos para estados
  - Doble círculo para estados de aceptación
  - Flechas para transiciones (con etiqueta de símbolo)
  - Auto-arcos para transiciones reflexivas
  - Estado activo resaltado en amarillo durante la simulación
- **Simulación paso a paso** y simulación completa con animación.
- **Traza textual** de la forma: `δ(qi, 'a' [CLASE]) → qj`
- Panel de **definición formal** M = (Q, Σ, δ, q0, F) con los valores reales del AFD seleccionado.

---

### `utils/` — Utilidades

#### `history.py`
Persiste el historial de validaciones en un archivo `history.json` en la carpeta del usuario. Permite recuperar búsquedas anteriores entre sesiones.

#### `exporter.py`
Exporta los tokens encontrados a tres formatos:
- **TXT**: reporte legible con estadísticas y árbol sintáctico.
- **CSV**: columnas `tipo, valor, posición, válido` para análisis en Excel.
- **JSON**: lista de objetos para integración con otras herramientas.

---

### `tests/` — Suite de Pruebas

**Requisito que cumple:** Verificación formal del comportamiento de los AFDs y los validadores.

#### `test_validators.py`

Prueba cada validador con casos válidos e inválidos, incluyendo casos límite:

| Validador | Casos límite verificados |
|-----------|--------------------------|
| URL | Dominios que empiezan con `t`, `p`, `s` (ej. `test.com`, `python.org`) |
| Teléfono | Indicativos incorrectos `+59`, `+56` son rechazados; `+57` es aceptado |
| Fecha | Año bisiesto 2000 (÷400 ✓), siglo 2100 (÷100 sin ÷400 ✗), 29/02 en no-bisiesto |
| Contraseña | Exactamente 8 caracteres, 7 caracteres rechazados |

#### `test_automata.py`

Prueba directa del motor AFD:

| Test | Qué verifica |
|------|-------------|
| Binario ÷3 | Transiciones clásicas de residuo modular |
| Binario termina en '0' | La cadena vacía `ε` es **rechazada** (q_start ≠ estado aceptador) |
| Identificadores | `[a-z][a-z0-9_]*` — solo letras minúsculas al inicio |
| Números decimales | `1.` es rechazado (q2 no acepta), `1.0` es aceptado (q3 acepta) |
| Contraseña — conjunto potencia | 16 estados no-muertos, único aceptador S1111, monotonía de bits |
| `find_longest_match` | Longitud correcta, retorna 0 sin coincidencia |

---

## Patrones reconocidos

| Tipo | Formatos aceptados | Expresión regular teórica |
|------|-------------------|--------------------------|
| EMAIL | `user@empresa.com`, `a.b@sub.domain.co` | `[a-zA-Z0-9._\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}` |
| TELÉFONO | `3001234567`, `+573001234567`, `300-123-4567` | `(\+57)?3[0-9]{9}\|3[0-9]{2}-[0-9]{3}-[0-9]{4}` |
| FECHA | `25/12/2024`, `2024-12-25` | `\d{2}/\d{2}/\d{4}\|\d{4}-\d{2}-\d{2}` |
| URL | `http://x.com`, `https://x.com/ruta?q=1` | `https?://[a-zA-Z0-9.\-]+(:[0-9]+)?(/[^\s]*)?` |
| PLACA | `ABC123`, `XYZ45T` | `[A-Z]{3}[0-9]{3}\|[A-Z]{3}[0-9]{2}[A-Z]` |
| USUARIO | `john_doe`, `Carlos.Lopez` | `[a-zA-Z][a-zA-Z0-9._\-]{2,19}` |
| CONTRASEÑA | `Mi$Clave2024` | `(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}` |

---

## Ejemplos para consola (sustentación)

```python
# ── Validar manualmente ────────────────────────────────────────────────
from validators import EmailValidator

v = EmailValidator()
result = v.validate("user@empresa.com")

print(result.is_valid)      # True
print(result.components)    # {'usuario': 'user', '@': '@', 'dominio': 'empresa', 'extensión': 'com'}
print(result.trace_text)    # Traza AFD paso a paso

# ── Analizar texto libre ───────────────────────────────────────────────
from lexical.lexer import Lexer

lexer = Lexer()
tokens = lexer.tokenize_word_boundary("Llama al 3001234567 o escribe a info@empresa.com")
for tok in tokens:
    print(f"[{tok.type.label()}] {tok.value!r}  válido={tok.is_valid}")

# ── Ver la traza del AFD ───────────────────────────────────────────────
from validators import PasswordValidator

v = PasswordValidator()
result = v.validate("Mi$Clave2024")
print(result.trace_text)
# → Estado inicial: S0000
# → Paso  1: δ(S0000, 'M' [UPPER]) → S0001
# → Paso  2: δ(S0001, 'i' [LOWER]) → S0011
# → ...
# → ACEPTADA ✓
```

---

## Restricción principal

> Este proyecto **no utiliza en ningún momento la librería `re` de Python**.
> Toda validación de patrones se realiza mediante recorrido carácter a carácter
> a través de los AFDs implementados en `automata/dfa.py`.
