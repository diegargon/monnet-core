"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
def pprint_table(rows, header_interval=50):
    """ Format and print a table with headers and rows."""
    if not rows:
        print("No data to display.")
        return

    # Detect if rows contain dicts or tuples/lists
    if isinstance(rows[0], dict):
        headers = list(rows[0].keys())  # Usar claves como encabezados
        rows = [list(row.values()) for row in rows]
    else:
        headers = [f"Col {i}" for i in range(len(rows[0]))]  # Columnas numeradas

    # Determine column widths dynamically
    col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]

    def print_header():
        print("  ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))))
        print("-" * (sum(col_widths) + (len(headers) - 1)))  # Línea separadora

    print_header()

    # Print rows with headers intercalados cada `header_interval` filas
    for i, row in enumerate(rows, start=1):
        print("  ".join(str(value).ljust(col_widths[i]) for i, value in enumerate(row)))
        if i % header_interval == 0 and i < len(rows):  # Intercalar encabezado
            print()
            print_header()