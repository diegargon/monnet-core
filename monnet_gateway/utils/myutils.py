"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
def pprint_table(rows, header_interval=50):
    """Format and print a table with headers and rows, handling missing keys."""
    if not rows:
        print("No data to display.")
        return

    # Obtener todas las claves únicas en orden de aparición
    headers = []
    seen = set()
    for row in rows:
        if isinstance(row, dict):
            for key in row.keys():
                if key not in seen:
                    headers.append(key)
                    seen.add(key)
        else:
            headers = [f"Col {i}" for i in range(len(row))]
            break  # no seguir si es una lista/tupla

    # Convertir filas dict a listas ordenadas según headers
    if isinstance(rows[0], dict):
        rows = [[str(row.get(h, "")) for h in headers] for row in rows]
    else:
        rows = [list(row) for row in rows]

    # Calcular ancho de columnas
    col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]

    def print_header():
        print("  ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))))
        print("-" * (sum(col_widths) + (len(headers) - 1)))

    print_header()

    for i, row in enumerate(rows, start=1):
        row = row[:len(headers)] + [""] * (len(headers) - len(row))
        print("  ".join(str(value).ljust(col_widths[i]) for i, value in enumerate(row)))
        if i % header_interval == 0 and i < len(rows):
            print()
            print_header()
