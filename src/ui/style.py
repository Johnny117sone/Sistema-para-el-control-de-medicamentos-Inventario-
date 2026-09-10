"""
Estilo centralizado de la interfaz.

Este módulo NO define colores (las paletas de cada ventana se dejaron
exactamente como estaban). Solo estandariza dos cosas que antes eran
inconsistentes entre ventanas:

1. Fuentes: antes se mezclaban "Arial" y "Helvetica" con tamaños sueltos
   (8, 9, 10, 11, 12, 14, 16, 18) sin un criterio claro de para qué se
   usaba cada uno. Aquí se define un tamaño mínimo legible (9pt) y un
   nombre por rol (título, subtítulo, etiqueta, botón, etc.) para que
   el mismo tipo de texto se vea igual en toda la aplicación.

2. Tamaños de ventana: las 7 ventanas principales de módulo tenían
   tamaños distintos sin razón funcional (de 850x650 a 1350x850).
   Ahora todas abren del mismo tamaño y centradas en pantalla.
"""

FONT_FAMILY = "Segoe UI"  # más legible que Arial en pantalla; en Linux/Mac cae al font por defecto del sistema

# --- Fuentes por rol (mismo criterio en toda la app) ---
FONT_TITLE = (FONT_FAMILY, 16, "bold")          # título principal de una ventana
FONT_TITLE_REGULAR = (FONT_FAMILY, 18)          # título grande sin negrita (encabezados de reporte)
FONT_HEADER = (FONT_FAMILY, 14, "bold")         # encabezado de sección
FONT_HEADER_REGULAR = (FONT_FAMILY, 14)
FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
FONT_SUBTITLE_REGULAR = (FONT_FAMILY, 12)
FONT_ENTRY = (FONT_FAMILY, 11)                  # texto dentro de campos de captura
FONT_BUTTON_LARGE = (FONT_FAMILY, 11, "bold")
FONT_BUTTON = (FONT_FAMILY, 10, "bold")         # botones estándar
FONT_LABEL = (FONT_FAMILY, 10)                  # texto normal / etiquetas
FONT_LABEL_BOLD = (FONT_FAMILY, 10, "bold")     # etiquetas destacadas (antes eran 9pt, se subió a 10pt por legibilidad)
FONT_SMALL = (FONT_FAMILY, 9)                   # notas y textos secundarios (antes 8pt, poco legible)
FONT_SMALL_BOLD = (FONT_FAMILY, 9, "bold")
FONT_SMALL_ITALIC = (FONT_FAMILY, 9, "italic")

# --- Tamaños de ventana estandarizados ---
MODULE_WINDOW_SIZE = (1200, 800)   # las 7 ventanas principales de módulo (antes variaban de 850x650 a 1350x850)
EDIT_DIALOG_SIZE = (650, 520)      # ventanas emergentes de edición (alta/edición de un registro)
DIALOG_SIZE_SMALL = (340, 230)     # diálogos cortos (ej. pedir una clave)
DIALOG_SIZE_MEDIUM = (480, 620)    # diálogos con formulario (ej. configuración de contraseñas)
LOGIN_WINDOW_SIZE = (420, 380)
MENU_WINDOW_SIZE = (500, 700)      # se deja igual: es un menú angosto por diseño, no un módulo de trabajo


def center_window(win, width: int, height: int) -> None:
    """Centra cualquier ventana (Tk o Toplevel) en la pantalla con el tamaño dado.

    Oculta la ventana mientras se calcula la posición y solo la muestra ya
    lista, para evitar el "flash" de una ventana pequeña en su tamaño por
    defecto antes de aplicarle el tamaño final.
    """
    win.withdraw()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = int((sw - width) / 2)
    y = int((sh - height) / 2)
    win.geometry(f"{width}x{height}+{x}+{y}")
    win.deiconify()
