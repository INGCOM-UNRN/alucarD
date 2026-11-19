// Carátula OMR (OMR_SPEC.md §4.1 y §7). Las coordenadas salen del manifiesto `omr-layout/2`, que se
// lee con json(): este módulo no escribe ninguna. Python le pasa sólo dónde queda el marco en la hoja
// (`ox`, `oy`) y dónde va el QR de la carátula, que el manifiesto no describe.

// DICT_4X4_50, ids 0 a 3: la matriz interior 4×4 por filas, "1" = blanco y "0" = negro.
#let omr-aruco = (
  "0": ("1011", "0101", "0011", "0010"),
  "1": ("0000", "1111", "1001", "1010"),
  "2": ("0011", "0011", "0001", "1000"),
  "3": ("1001", "1001", "0100", "0111"),
)
#let omr-negro = rgb("#000000")
#let omr-contorno = 0.5pt + rgb("#999999")
#let omr-gris = rgb("#666666")

// Un marcador de 6×6 celdas: borde negro y la matriz del id adentro, como rectángulos vectoriales.
#let omr-marcador(id, lado) = {
  let celda = lado / 6
  let filas = omr-aruco.at(str(id))
  box(width: lado, height: lado, {
    for f in range(6) {
      for c in range(6) {
        let negro = f == 0 or f == 5 or c == 0 or c == 5 or filas.at(f - 1).at(c - 1) == "0"
        if negro {
          // Un pelo más grande, para que dos celdas vecinas no dejen una línea blanca entre ellas.
          place(dx: c * celda, dy: f * celda,
                rect(width: celda + 0.02mm, height: celda + 0.02mm, fill: omr-negro, stroke: none))
        }
      }
    }
  })
}

// Una burbuja centrada en (x, y), con su valor arriba del borde superior. `relleno`: la fracción del
// disco que mide la app (0,7 r) pintada de negro, para la hoja de calibración; 1 la pinta entera.
#let omr-burbuja(x, y, d, etiqueta, relleno: none) = {
  let r = d / 2
  place(dx: x - r, dy: y - r, circle(radius: r, stroke: omr-contorno))
  if relleno != none and relleno > 0 {
    let rr = if relleno >= 1 { r } else { 0.7 * r * calc.sqrt(relleno) }
    place(dx: x - rr, dy: y - rr, circle(radius: rr, fill: omr-negro, stroke: none))
  }
  if etiqueta != none {
    place(dx: x - 6mm, dy: y - r - 3.1mm,
          box(width: 12mm, height: 2.8mm, align(center + bottom, text(size: 7pt, fill: omr-negro, etiqueta))))
  }
}

#let omr-coma(x) = {
  let t = str(x)
  if t.ends-with(".0") { t = t.slice(0, -2) }
  t.replace(".", ",")
}

#let omr-nombre-fila(fila) = {
  if "values" in fila {
    if fila.values == (0, 5) { "medio punto" } else { "cuartos" }
  } else if fila.place == 1.0 { "Nota" } else if fila.place == 0.1 { "décimas" } else { "centésimas" }
}

// Etiqueta de fila, a la izquierda del área de burbujas (x < 28 mm del marco).
#let omr-fila(ox, oy, y, texto) = place(dx: ox + 9mm, dy: oy + y - 2mm,
  box(width: 18mm, height: 4mm, align(right + horizon, text(size: 7.5pt, fill: omr-negro, texto))))

// La franja de cabecera: fiduciales, burbujas, etiquetas, el QR del estudiante y su respaldo
// legible, la leyenda y la línea divisoria. Se dibuja en el fondo de la página 1, desde su origen.
//
// - `rellenos`: {"<campo>=<valor>": fracción}, para la hoja de calibración.
// - `qr`: (svg: …, x: …, y: …, lado: …) en mm del marco, o none.
// - `respaldo`: líneas de texto legible debajo del QR (nombre y STUDENT_ID).
#let omr-franja(m, ox: 15mm, oy: 15mm, qr: none, respaldo: (), texto: (x: 103, y: 30, ancho: 37),
                rellenos: (:), divisoria: 9mm) = {
  let w = m.frame_mm.w * 1mm
  let h = m.frame_mm.h * 1mm
  let lado = m.marker_mm * 1mm
  let d = m.bubble_diameter_mm * 1mm
  let esquinas = ((0, 0mm, 0mm), (1, w, 0mm), (2, w, h), (3, 0mm, h))
  for (id, cx, cy) in esquinas {
    place(dx: ox + cx - lado / 2, dy: oy + cy - lado / 2, omr-marcador(id, lado))
  }
  let n = 0
  for campo in m.fields {
    if campo.type == "single_choice" {
      n += 1
      let y = campo.options.first().y_mm * 1mm
      omr-fila(ox, oy, y, [Ej. #n (#omr-coma(campo.max_points))])
      for o in campo.options {
        omr-burbuja(ox + o.x_mm * 1mm, oy + o.y_mm * 1mm, d, o.label,
                    relleno: rellenos.at(campo.id + "=" + str(o.step), default: none))
      }
    } else if campo.type == "decimal_digits" {
      for fila in campo.digits {
        let valores = fila.at("values", default: range(fila.start, fila.start + fila.count))
        let y0 = fila.y0_mm * 1mm
        omr-fila(ox, oy, y0, omr-nombre-fila(fila))
        for (i, valor) in valores.enumerate() {
          let x = fila.x0_mm * 1mm + if fila.axis == "x" { i * fila.step_mm * 1mm } else { 0mm }
          let y = y0 + if fila.axis == "y" { i * fila.step_mm * 1mm } else { 0mm }
          omr-burbuja(ox + x, oy + y, d, str(valor),
                      relleno: rellenos.at(campo.id + "@" + str(fila.place) + "=" + str(valor), default: none))
        }
      }
    } else if campo.type == "flag" {
      omr-burbuja(ox + campo.x_mm * 1mm, oy + campo.y_mm * 1mm, d, campo.label,
                  relleno: rellenos.at(campo.id + "=1", default: none))
    }
  }
  if qr != none {
    place(dx: ox + qr.x * 1mm, dy: oy + qr.y * 1mm,
          image(bytes(qr.svg), format: "svg", width: qr.lado * 1mm, height: qr.lado * 1mm))
  }
  if respaldo.len() > 0 {
    place(dx: ox + texto.x * 1mm, dy: oy + texto.y * 1mm, box(width: texto.ancho * 1mm,
          align(center, text(size: 8pt, fill: omr-negro, respaldo.join(linebreak())))))
  }
  place(dx: ox, dy: oy + h + lado / 2 + 1mm, box(width: w, align(center, text(size: 7pt, fill: omr-gris)[
    Zona reservada para el docente — no escribir · Rellenar el círculo con lapicera, no tildar ni cruzar
  ])))
  place(dx: ox - 5mm, dy: oy + h + divisoria, line(length: w + 10mm, stroke: 0.5pt + omr-gris))
}
