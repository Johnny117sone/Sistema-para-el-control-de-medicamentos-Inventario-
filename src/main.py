"""
Punto de entrada de la aplicación.

Este archivo solo arma las piezas (login y menú principal). La lógica de
autenticación vive en services/auth_service.py, y el acceso a datos en
data/. Las ventanas de cada módulo viven en ui/.
"""
import tkinter as tk
from tkinter import messagebox

from data.usuarios_repository import UsuariosRepository
from data.db import init_schema
from services.auth_service import AuthService
from ui.style import *

from ui.inventario_maestro import VentanaMaestro
from ui.inventario_general import VentanaGeneral
from ui.devoluciones_mermas import VentanaDevoluciones
from ui.municipio_destino import VentanaDestino
from ui.ordenes_salida import VentanaOrdenes
from ui.reportes_estadisticos import VentanaReportes


# --- CLASE LOGIN ---
class Login:
    def __init__(self, root, auth_service: AuthService):
        self.root = root
        self.auth_service = auth_service
        self.root.title("SISTEMA PLANASSZE IPN - ACCESO")
        self.root.configure(bg="#641e16")
        self.root.resizable(False, False)

        center_window(self.root, *LOGIN_WINDOW_SIZE)

        frame = tk.Frame(root, bg="white", padx=30, pady=30, bd=2, relief="ridge")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="INICIAR SESIÓN", font=FONT_HEADER, bg="white").pack(pady=10)

        tk.Label(frame, text="Usuario:", bg="white").pack(anchor="w")
        self.ent_user = tk.Entry(frame, font=FONT_ENTRY, bd=2)
        self.ent_user.pack(fill="x", pady=5)

        tk.Label(frame, text="Contraseña:", bg="white").pack(anchor="w")
        self.ent_pass = tk.Entry(frame, font=FONT_ENTRY, show="*", bd=2)
        self.ent_pass.pack(fill="x", pady=5)

        tk.Button(frame, text="INGRESAR AL SISTEMA", bg="#27ae60", fg="white",
                  font=FONT_BUTTON, pady=10, command=self.validar_acceso).pack(fill="x", pady=20)

    def validar_acceso(self):
        user = self.ent_user.get()
        password = self.ent_pass.get()

        rol = self.auth_service.iniciar_sesion(user, password)

        if rol:
            self.root.destroy()
            root_menu = tk.Tk()
            MenuPrincipal(root_menu, rol, self.auth_service)
            root_menu.mainloop()
        else:
            messagebox.showerror("Acceso Denegado", "Usuario o contraseña incorrectos.")


# --- CLASE MENÚ PRINCIPAL ---
class MenuPrincipal:
    def __init__(self, root, rol, auth_service: AuthService):
        self.root = root
        self.rol = rol
        self.auth_service = auth_service
        self.root.title(f"PLANASSZE IPN - MENÚ ({self.rol})")
        center_window(self.root, *MENU_WINDOW_SIZE)
        self.root.configure(bg="#f0f0f0")

        self.header = tk.Frame(root, bg="#641e16", height=80)
        self.header.pack(fill="x")
        tk.Label(self.header, text="CONTROL INTEGRAL DE MEDICAMENTOS",
                 fg="white", bg="#641e16", font=FONT_HEADER, pady=20).pack()

        self.menu_frame = tk.Frame(root, bg="#f0f0f0", pady=20)
        self.menu_frame.pack(expand=True)

        opciones = [
            ("📦 INVENTARIO MAESTRO", self.verificar_acceso_maestro, "#2c3e50"),
            ("📊 INVENTARIO GENERAL", self.abrir_general, "#2980b9"),
            ("🔄 DEVOLUCIONES Y MERMAS", self.abrir_devoluciones, "#8e44ad"),
            ("📍 MUNICIPIO / DESTINO", self.abrir_destino, "#e74c3c"),
            ("📄 ÓRDENES DE SALIDA (PDF/EXCEL)", self.abrir_ordenes, "#27ae60"),
            ("📊 REPORTES Y ESTADÍSTICAS", self.abrir_reportes, "#16a085"),
            ("⚙️ CONFIGURAR CONTRASEÑAS", self.abrir_configuracion, "#7f8c8d"),
            ("❌ SALIR", root.quit, "#34495e")
        ]

        for texto, comando, color in opciones:
            btn = tk.Button(self.menu_frame, text=texto, command=comando,
                            bg=color, fg="white", font=FONT_BUTTON_LARGE,
                            width=35, height=2, bd=3, relief="raised", cursor="hand2")
            btn.pack(pady=8)

    def verificar_acceso_maestro(self):
        """Pide la clave del usuario 'master' para entrar al Catálogo Maestro."""
        ventana_clave = tk.Toplevel(self.root)
        ventana_clave.title("AUTENTICACIÓN REQUERIDA")
        center_window(ventana_clave, *DIALOG_SIZE_SMALL)
        ventana_clave.grab_set()

        tk.Label(ventana_clave, text="Ingrese Clave Maestra:", pady=10, font=FONT_BUTTON).pack()
        ent_clave = tk.Entry(ventana_clave, show="*", font=FONT_SUBTITLE_REGULAR, justify="center")
        ent_clave.pack(pady=5)

        def validar():
            res = self.auth_service.iniciar_sesion("master", ent_clave.get())
            if res == "ADMIN":
                ventana_clave.destroy()
                self.abrir_maestro()
            else:
                messagebox.showerror("Error", "Clave Maestra Incorrecta.")
                ent_clave.delete(0, tk.END)

        tk.Button(ventana_clave, text="ENTRAR", command=validar, bg="#2c3e50", fg="white", width=15).pack(pady=20)

    def abrir_configuracion(self):
        """Ventana de gestión de credenciales. Toda la validación de negocio
        ahora vive en AuthService.cambiar_password(); aquí solo se recogen
        los datos del formulario y se muestra el resultado."""
        ventana_config = tk.Toplevel(self.root)
        ventana_config.title("CONFIGURACIÓN DE SEGURIDAD")
        center_window(ventana_config, *DIALOG_SIZE_MEDIUM)
        ventana_config.configure(bg="#f4f6f7")
        ventana_config.grab_set()

        frame = tk.Frame(ventana_config, padx=30, pady=20, bg="white", bd=1, relief="solid")
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        tk.Label(frame, text="⚙️ ACTUALIZAR CREDENCIALES", font=FONT_SUBTITLE, bg="white").pack(pady=10)

        tk.Label(frame, text="Seleccione la cuenta a modificar:", bg="white", font=FONT_LABEL_BOLD).pack(anchor="w")
        self.var_objetivo = tk.StringVar(value="admin")
        opciones_frame = tk.Frame(frame, bg="white")
        opciones_frame.pack(fill="x", pady=5)

        tk.Radiobutton(opciones_frame, text="Login (Admin)", variable=self.var_objetivo,
                       value="admin", bg="white", command=lambda: self.lbl_actual.config(text="Contraseña ACTUAL del Admin:")).pack(side="left")
        tk.Radiobutton(opciones_frame, text="Catálogo (Maestro)", variable=self.var_objetivo,
                       value="master", bg="white", command=lambda: self.lbl_actual.config(text="Contraseña ACTUAL del Maestro:")).pack(side="left", padx=10)

        tk.Canvas(frame, height=2, bg="#ecf0f1", highlightthickness=0).pack(fill="x", pady=15)

        self.lbl_actual = tk.Label(frame, text="Contraseña ACTUAL del Admin:", bg="white", fg="#c0392b", font=FONT_SMALL_BOLD)
        self.lbl_actual.pack(anchor="w")
        self.ent_actual = tk.Entry(frame, show="*", font=FONT_ENTRY)
        self.ent_actual.pack(fill="x", pady=5)

        tk.Label(frame, text="Nueva Contraseña (mín. 6 caracteres):", bg="white").pack(anchor="w", pady=(15, 0))
        self.ent_nueva = tk.Entry(frame, show="*", font=FONT_ENTRY)
        self.ent_nueva.pack(fill="x", pady=5)

        tk.Label(frame, text="Confirmar Nueva Contraseña:", bg="white").pack(anchor="w")
        self.ent_confirmar = tk.Entry(frame, show="*", font=FONT_ENTRY)
        self.ent_confirmar.pack(fill="x", pady=5)

        self.mostrando = False

        def alternar_vista():
            self.mostrando = not self.mostrando
            char = "" if self.mostrando else "*"
            self.ent_actual.config(show=char)
            self.ent_nueva.config(show=char)
            self.ent_confirmar.config(show=char)
            btn_ojo.config(text="👁️ Ocultar" if self.mostrando else "👁️ Ver")

        btn_ojo = tk.Button(frame, text="👁️ Ver", font=FONT_SMALL, command=alternar_vista)
        btn_ojo.pack(anchor="e")

        def ejecutar_cambio():
            user_objetivo = self.var_objetivo.get()
            actual = self.ent_actual.get()
            nueva = self.ent_nueva.get()
            conf = self.ent_confirmar.get()

            exito, mensaje = self.auth_service.cambiar_password(user_objetivo, actual, nueva, conf)

            if exito:
                messagebox.showinfo("Éxito", mensaje)
                ventana_config.destroy()
            else:
                messagebox.showerror("Error", mensaje)

        tk.Button(frame, text="✅ APLICAR CAMBIOS", bg="#27ae60", fg="white",
                  font=FONT_BUTTON, height=2, command=ejecutar_cambio).pack(fill="x", pady=25)

    def abrir_maestro(self):
        self.root.withdraw()
        VentanaMaestro(tk.Toplevel(self.root), self.root)

    def abrir_general(self):
        self.root.withdraw()
        VentanaGeneral(tk.Toplevel(self.root), self.root)

    def abrir_devoluciones(self):
        self.root.withdraw()
        VentanaDevoluciones(tk.Toplevel(self.root), self.root)

    def abrir_destino(self):
        self.root.withdraw()
        VentanaDestino(tk.Toplevel(self.root), self.root)

    def abrir_ordenes(self):
        self.root.withdraw()
        VentanaOrdenes(tk.Toplevel(self.root), self.root)

    def abrir_reportes(self):
        self.root.withdraw()
        VentanaReportes(tk.Toplevel(self.root), self.root)


if __name__ == "__main__":
    init_schema()  # crea las tablas y usuarios por defecto si no existen
    auth_service = AuthService(UsuariosRepository())

    main_root = tk.Tk()
    Login(main_root, auth_service)
    main_root.mainloop()
