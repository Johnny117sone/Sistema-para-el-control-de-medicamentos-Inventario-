# Sistema de Inventario de Medicamentos (PLANASSZE)

Sistema de escritorio para el control integral de inventario de medicamentos: catálogo maestro, entradas y salidas por municipio, devoluciones/mermas, generación de reportes en PDF/Excel y estadísticas con gráficas.

Desarrollado en Python con interfaz gráfica (Tkinter) y base de datos local en SQLite.

## Contexto y problemática

Este sistema nace de una necesidad real identificada durante mi servicio social en el área de Control y Trámite del SISS, dentro de PLANASSZE.

Las **Brigadas** son una modalidad de prestación de servicio social de PLANASSZE que opera por temporadas (primavera, verano, invierno). En cada temporada se generan múltiples movimientos de medicamento: entradas al inventario, salidas hacia los municipios donde operan las brigadas, y bajas por caducidad o merma.

Ese proceso se llevaba de forma manual, lo que provocaba **descontrol del inventario** durante las temporadas de brigadas: no existía un mecanismo centralizado para saber con certeza cuánto medicamento había, cuánto entraba y salía, hacia qué municipio y por qué motivo (uso, caducidad o merma).

Este proyecto es el **primer prototipo** desarrollado para atender esa problemática, con el objetivo de darle trazabilidad y optimizar el proceso de control de inventario de medicamentos por temporada.

## Funcionalidades

- **Login con roles** (Administrador / Operador) para controlar el acceso a módulos sensibles.
- **Inventario Maestro:** alta, edición y baja lógica de medicamentos (SKU, laboratorio, presentación, stock mínimo/máximo).
- **Inventario General:** registro de entradas de medicamento al iniciar cada temporada de brigadas (primavera, verano, invierno).
- **Devoluciones y Mermas:** registro de retornos, pérdidas de producto y bajas por caducidad.
- **Municipio / Destino:** control de las salidas de medicamento hacia los municipios donde operan las brigadas.
- **Órdenes de Salida:** generación de comprobantes de salida por municipio en PDF y Excel, para dar trazabilidad a cada envío.
- **Reportes y Estadísticas:** visualización de movimientos por temporada con gráficas (Matplotlib) y exportación a Excel con formato.
- **Gestión de credenciales:** actualización de contraseñas de acceso desde la propia aplicación.

## Tecnologías

| Categoría | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Interfaz gráfica | Tkinter |
| Base de datos | SQLite3 |
| Reportes PDF | ReportLab |
| Reportes Excel | OpenPyXL, Pandas |
| Gráficas | Matplotlib |
| Empaquetado a ejecutable | PyInstaller |

## Estructura del proyecto

```
inventario-planace/
├── src/
│   ├── main.py                      # Punto de entrada: arma Login + MenuPrincipal
│   ├── data/                        # Capa de datos (acceso a SQLite)
│   │   ├── db.py                    # Conexión y creación del esquema
│   │   ├── security.py              # Hashing de contraseñas (PBKDF2 + salt)
│   │   ├── usuarios_repository.py   # SQL de la tabla usuarios
│   │   ├── medicamentos_repository.py
│   │   ├── municipios_repository.py
│   │   └── inventario_db.py         # Fachada de compatibilidad para las ventanas
│   ├── services/                    # Capa de lógica de negocio
│   │   └── auth_service.py          # Reglas de login y cambio de contraseña
│   └── ui/                          # Capa de presentación (ventanas Tkinter)
│       ├── style.py                 # Fuentes y tamaños de ventana estandarizados
│       ├── inventario_maestro.py
│       ├── inventario_general.py
│       ├── devoluciones_mermas.py
│       ├── municipios.py
│       ├── municipio_destino.py
│       ├── ordenes_salida.py
│       └── reportes_estadisticos.py
├── docs/                            # Capturas de pantalla y documentación adicional
├── main.spec                        # Configuración de empaquetado con PyInstaller
├── requirements.txt
└── .gitignore
```

**Sobre la arquitectura:** el proyecto sigue una separación por capas (patrón similar a MVC/Service Layer):
- **`data/`** — todo el SQL vive aquí, organizado en repositorios por entidad.
- **`services/`** — reglas de negocio (ej. longitud mínima de contraseña, validación cruzada de credenciales), sin saber nada de Tkinter ni de SQL.
- **`ui/`** — solo ventanas y widgets; delegan la lógica a los servicios/repositorios.

> **Nota de transparencia:** las ventanas de `ui/` (reportes, órdenes de salida, devoluciones) todavía abren conexión directa a SQLite para algunas consultas específicas de generación de reportes — es una decisión consciente para no reescribir de golpe ~3,500 líneas de código funcional sin poder probarlas. La capa de autenticación (`services/auth_service.py` + `data/usuarios_repository.py`) sí está 100% separada y con pruebas. Migrar el resto de las consultas a repositorios propios (ej. `HistorialRepository`) es el siguiente paso natural.

## Instalación y ejecución

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Johnny117sone/inventario-planace.git
   cd inventario-planace
   ```

2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # En Windows
   source venv/bin/activate   # En Linux/Mac
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:
   ```bash
   python src/main.py
   ```

   Al iniciar por primera vez, el sistema crea automáticamente la base de datos SQLite (`sistema_salud.db`) con dos cuentas de acceso por defecto (ver nota de seguridad abajo).

> **Nota:** el módulo de notificaciones sonoras usa `winsound`, disponible solo en Windows. En Linux/Mac esa función específica no estará disponible.

## Nota de seguridad y mejoras futuras

Este proyecto fue desarrollado como una primera versión funcional y luego refactorizado hacia una arquitectura en capas. Mejoras ya aplicadas y pendientes:

- [x] **Hash de contraseñas** (`data/security.py`): las contraseñas se guardan con PBKDF2-HMAC-SHA256 + salt aleatorio por usuario, en lugar de texto plano. Compatible hacia atrás si se migra una base de datos antigua.
- [x] **Interfaz estandarizada** (`ui/style.py`): fuentes y tamaños de ventana unificados en toda la aplicación (antes variaban sin criterio entre módulos).
- [ ] Mover las credenciales por defecto a variables de entorno en lugar de tenerlas en el código.
- [ ] Migrar las consultas SQL restantes dentro de `ui/` (reportes, órdenes de salida, devoluciones) a repositorios dedicados en `data/`.
- [ ] Agregar pruebas unitarias automatizadas para `services/` y `data/` (por ahora se probaron manualmente).
- [ ] Migrar la interfaz a un framework más moderno (por ejemplo, CustomTkinter).

## Estado del proyecto

Este sistema fue probado y utilizado durante la brigada de marzo-abril de 2026, apoyando el control real de entradas, salidas y devoluciones de medicamento de esa temporada.

## Autor

Desarrollado por Johnny Hernández Torres, como primer prototipo funcional durante mi servicio social en el área de Control y Trámite del SISS (PLANASSZE), y posteriormente refactorizado como proyecto de portafolio.

GitHub: [@Johnny117sone](https://github.com/Johnny117sone)