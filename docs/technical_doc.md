# Documentación Técnica — Analizador Léxico y Sintáctico

## 1. Marco Teórico

### 1.1 Expresiones Regulares

Una **expresión regular** sobre un alfabeto Σ define un lenguaje regular L(r).
Las operaciones fundamentales son:
- **Unión**: r₁ | r₂
- **Concatenación**: r₁r₂
- **Estrella de Kleene**: r*
- **Cerradura positiva**: r+  ≡  rr*
- **Opcionalidad**: r?  ≡  ε | r

En este proyecto **no se usa la librería `re`**. En su lugar cada
expresión regular se implementa manualmente mediante un AFD.

### 1.2 Autómatas Finitos Deterministas (AFD)

**Definición formal**: Un AFD es una 5-tupla M = (Q, Σ, δ, q₀, F) donde:

| Componente | Descripción |
|-----------|-------------|
| Q | Conjunto finito no vacío de **estados** |
| Σ | **Alfabeto** finito de símbolos de entrada |
| δ : Q × Σ → Q | **Función de transición** (total) |
| q₀ ∈ Q | **Estado inicial** |
| F ⊆ Q | Conjunto de **estados de aceptación** |

**Extensión de δ a cadenas** (δ*):
```
δ*(q, ε) = q
δ*(q, wa) = δ(δ*(q,w), a)
```

**Lenguaje aceptado**:
```
L(M) = { w ∈ Σ* | δ*(q₀, w) ∈ F }
```

### 1.3 Equivalencia AFD — Expresiones Regulares

Por el **Teorema de Kleene**: todo lenguaje regular puede describirse
mediante una expresión regular y reconocerse mediante un AFD.

En este proyecto implementamos la dirección ER → AFD construyendo
el autómata manualmente a partir del análisis de la estructura del patrón.

---

## 2. AFDs Implementados

### 2.1 AFD Email

**Expresión regular**: `[a-zA-Z0-9._-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}`

**M_email = ({q0,q1,q2,q3,q4,q5}, Σ_e, δ_e, q0, {q5})**

**Alfabeto Σ_e** = {ALPHA, DIGIT, DOT, UNDER, DASH, AT, ELSE}

**Tabla de transiciones δ_e**:

```
Estado │ ALPHA │ DIGIT │ DOT │ UNDER │ DASH │ AT │ ELSE
───────┼───────┼───────┼─────┼───────┼──────┼────┼─────
  q0   │  q1   │  q1   │  —  │   —   │  —   │ —  │  —
  q1   │  q1   │  q1   │  q1 │   q1  │  q1  │ q2 │  —
  q2   │  q3   │  q3   │  —  │   —   │  —   │ —  │  —
  q3   │  q3   │  q3   │  q4 │   —   │  q3  │ —  │  —
  q4   │  q5   │  —   │  —  │   —   │  —   │ —  │  —
  q5★  │  q5   │  —   │  —  │   —   │  —   │ —  │  —
```
(— → estado trampa qDEAD)

**Interpretación de estados**:
- q0: inicio, nada leído
- q1: leyendo parte del usuario (antes de @)
- q2: se leyó el símbolo '@'
- q3: leyendo el dominio
- q4: se leyó el punto separador dominio.extensión
- q5: leyendo la extensión (ACEPTACIÓN)

**Traza de ejemplo** para `user@test.com`:
```
  Estado inicial: q0
  Paso  1: δ(q0, 'u' [ALPHA]) → q1
  Paso  2: δ(q1, 's' [ALPHA]) → q1
  Paso  3: δ(q1, 'e' [ALPHA]) → q1
  Paso  4: δ(q1, 'r' [ALPHA]) → q1
  Paso  5: δ(q1, '@' [AT])    → q2
  Paso  6: δ(q2, 't' [ALPHA]) → q3
  Paso  7: δ(q3, 'e' [ALPHA]) → q3
  Paso  8: δ(q3, 's' [ALPHA]) → q3
  Paso  9: δ(q3, 't' [ALPHA]) → q3
  Paso 10: δ(q3, '.' [DOT])   → q4
  Paso 11: δ(q4, 'c' [ALPHA]) → q5  ✓ ACEPTA
  Paso 12: δ(q5, 'o' [ALPHA]) → q5  ✓ ACEPTA
  Paso 13: δ(q5, 'm' [ALPHA]) → q5  ✓ ACEPTA
  ACEPTADA
```

### 2.2 AFD Contraseña (Conjunto Potencia)

**Concepto**: Para verificar co-ocurrencia de categorías (mayúscula AND
minúscula AND dígito AND especial), se construye un AFD de **conjunto potencia**
con 2⁴ = 16 estados. Cada estado es una máscara de bits.

```
bit 0 → tiene mayúscula
bit 1 → tiene minúscula
bit 2 → tiene dígito
bit 3 → tiene especial

Estado S0000 → ninguna categoría vista (inicial)
Estado S1111 → todas las categorías vistas (ACEPTACIÓN)

δ(Sxxxx, UPPER)   = S(xxxx | 0001)
δ(Sxxxx, LOWER)   = S(xxxx | 0010)
δ(Sxxxx, DIGIT)   = S(xxxx | 0100)
δ(Sxxxx, SPECIAL) = S(xxxx | 1000)
δ(Sxxxx, OTHER)   = Sxxxx  (sin cambio)
```

Este es un ejemplo del poder de los AFDs para representar propiedades
de co-ocurrencia sin necesitar lookaheads.

### 2.3 AFD Binario Divisible por 3

**Teorema**: El conjunto {w ∈ {0,1}* | valor(w) mod 3 = 0} es regular.

**M_div3 = ({q0,q1,q2}, {0,1}, δ, q0, {q0})**

```
δ(q0, 0) = q0    [0·2 mod 3 = 0]
δ(q0, 1) = q1    [0·2+1 mod 3 = 1]
δ(q1, 0) = q2    [1·2 mod 3 = 2]
δ(q1, 1) = q0    [1·2+1 mod 3 = 0]
δ(q2, 0) = q1    [2·2 mod 3 = 1]
δ(q2, 1) = q2    [2·2+1 mod 3 = 2]
```

Estado qi representa el residuo i al dividir por 3. El estado q0 es
simultáneamente inicial y de aceptación (cadena vacía tiene valor 0).

---

## 3. Análisis Léxico

### 3.1 Arquitectura del Lexer

El analizador léxico implementa el algoritmo de **máximal munch**
(coincidencia más larga):

```
ENTRADA: texto fuente
SALIDA:  lista de tokens

ALGORITMO:
  i ← 0
  mientras i < |texto|:
    si texto[i] es separador:
      i ← i + 1
    sino:
      mejor ← ninguno
      para cada validador v en ORDEN_PRIORIDAD:
        fin ← v.find_longest_match(texto, i)
        si fin > mejor.fin:
          mejor ← (v.tipo, fin)
      si mejor ≠ ninguno:
        emitir Token(mejor.tipo, texto[i:mejor.fin])
        i ← mejor.fin
      sino:
        i ← i + 1   # char no reconocido
```

### 3.2 Orden de Prioridad de Validadores

El lexer usa el siguiente orden para resolver ambigüedades:
1. URL (primero, para evitar que el dominio se confunda con email)
2. EMAIL
3. PHONE
4. DATE
5. PLATE
6. PASSWORD
7. USERNAME

### 3.3 Clasificación de Tokens

```
TokenType.EMAIL    → [EMAIL]
TokenType.PHONE    → [TELÉFONO]
TokenType.DATE     → [FECHA]
TokenType.URL      → [URL]
TokenType.PLATE    → [PLACA]
TokenType.PASSWORD → [CONTRASEÑA]
TokenType.USERNAME → [USUARIO]
```

---

## 4. Análisis Sintáctico

### 4.1 Gramáticas Formales de los Patrones

**EMAIL** (notación BNF):
```
<email>     ::= <usuario> '@' <dominio>
<dominio>   ::= <nombre-dom> '.' <extensión>
<usuario>   ::= <inicio-user> { <cuerpo-user> }
<inicio-user> ::= [a-zA-Z] | [0-9]
<cuerpo-user> ::= [a-zA-Z0-9._-]
<nombre-dom>  ::= [a-zA-Z0-9] { [a-zA-Z0-9-] }
<extensión>   ::= [a-zA-Z]{2,6}
```

**TELÉFONO**:
```
<teléfono> ::= <local> | <internacional>
<local>    ::= '3' <dígito>{9}
<internacional> ::= '+57' <local>
<local-guiones> ::= '3' <d><d> '-' <d>{3} '-' <d>{4}
```

**FECHA**:
```
<fecha> ::= <F1> | <F2>
<F1>    ::= <DD> '/' <MM> '/' <YYYY>
<F2>    ::= <YYYY> '-' <MM> '-' <DD>
<DD>    ::= [0-3][0-9]   (validación de rango en análisis semántico)
<MM>    ::= [0-1][0-9]
<YYYY>  ::= [0-9]{4}
```

### 4.2 Árbol Sintáctico

Para cada token válido se construye un árbol sintáctico simplificado:

```
EMAIL "admin@universidad.edu.co"
├── usuario: "admin"
├── @: "@"
└── dominio
    ├── nombre: "universidad"
    ├── .: "."
    └── extensión: "edu.co"

URL "https://portal.gov.co/tramites"
└── URL
    ├── protocolo: "https"
    ├── host
    │   ├── dominio: "portal"
    │   ├── .: "."
    │   └── extensión: "gov"
    └── ruta: "/tramites"
```

---

## 5. Implementación: Sin librería `re`

Todos los patrones se implementan mediante:

1. **Función clasificadora de caracteres**: mapea `char → clase_símbolo`
2. **Tabla de transiciones**: `dict[estado][clase] → siguiente_estado`
3. **Recorrido carácter a carácter**: bucle `for char in string`
4. **Estado trampa (DEAD)**: destino de todas las transiciones no definidas

Ejemplo de clasificación manual para EMAIL:
```python
def _classify(char: str) -> str:
    if char.isalpha():  return "ALPHA"
    if char.isdigit():  return "DIGIT"
    if char == ".":     return "DOT"
    if char == "_":     return "UNDER"
    if char == "-":     return "DASH"
    if char == "@":     return "AT"
    return "ELSE"
```

Esto sustituye completamente a cualquier llamada a `re.match` o `re.search`.

---

## 6. Módulo Simulador AFD

El simulador permite al usuario:

1. **Seleccionar** un AFD de un catálogo predefinido
2. **Visualizar** el grafo del AFD en canvas (estados, flechas, etiquetas)
3. **Ingresar** una cadena de prueba
4. **Simular** paso a paso con resaltado del estado actual
5. **Leer** la traza completa `δ(qi, char) → qj`

La visualización usa `tkinter.Canvas`:
- Estados: círculos de radio 28px
- Estado inicial: flecha entrante desde la izquierda
- Estados de aceptación: doble círculo
- Estado activo: color naranja
- Transiciones: flechas con etiquetas de clase de símbolo

---

## 7. Validaciones Semánticas Adicionales (Post-AFD)

El AFD verifica la *estructura* del patrón. Sobre los resultados se
aplican reglas semánticas adicionales:

| Patrón | Reglas adicionales |
|--------|-------------------|
| EMAIL | Usuario no empieza/termina con punto; extensión 2-6 chars |
| TELÉFONO | Número limpio de 10 dígitos; empieza con 3 |
| FECHA | Días y meses en rango; validación de años bisiestos |
| URL | Extensión mínima 2 chars; dominio no vacío |
| CONTRASEÑA | Longitud mínima 8; todas las categorías presentes |
| USUARIO | Longitud 3-20; no termina con carácter especial |

---

## 8. Complejidad Computacional

| Operación | Complejidad |
|-----------|-------------|
| `DFA.process(s)` | O(\|s\|) |
| `DFA.find_longest_match(text, i)` | O(\|text\| - i) |
| `Lexer.tokenize(text)` | O(\|text\| · k) donde k = nro. validadores |
| `SyntaxTree.from_dict(d)` | O(\|d\|) |

---

*Documentación generada para el Proyecto Final — Teoría de Lenguajes Formales*
