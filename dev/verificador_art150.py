texto_completo = """Art. 150. Disposiciones generales.
Se estará a lo establecido en la Ley General de Telecomunicaciones, 11/2022, o ley que la
sustituya."""

titulo = "Art. 150. Disposiciones generales."
contenido = texto_completo.replace(titulo, "").strip()

print(f"Longitud título: {len(titulo)}")
print(f"Longitud contenido (sin título): {len(contenido)}")
print(f"¿Pasa filtro >100?: {len(contenido) > 100}")
print(f"\nContenido:\n'{contenido}'")