import tkinter as tk
from ui.style import *
from tkinter import ttk, messagebox
import sqlite3

class VentanaMunicipios:
    def __init__(self, root, parent_window=None):
        self.root = root
        self.parent_window = parent_window  # Recibe la instancia de VentanaDestino
        self.root.title("CATÁLOGO DE DESTINOS REGIONALES")
        center_window(self.root, *MODULE_WINDOW_SIZE)
        self.root.configure(bg="#f4f6f7")
        self.db_name = "sistema_salud.db"
        
        # Al cerrar con la "X", regresa a SALIDAS
        self.root.protocol("WM_DELETE_WINDOW", self.regresar_a_salidas)
        
        self.lista_estados = [
            "AGUASCALIENTES", "BAJA CALIFORNIA", "BAJA CALIFORNIA SUR", "CAMPECHE", "CHIAPAS", 
            "CHIHUAHUA", "CIUDAD DE MÉXICO", "COAHUILA", "COLIMA", "DURANGO", "ESTADO DE MÉXICO", 
            "GUANAJUATO", "GUERRERO", "HIDALGO", "JALISCO", "MICHOACÁN", "MORELOS", "NAYARIT", 
            "NUEVO LEÓN", "OAXACA", "PUEBLA", "QUERÉTARO", "QUINTANA ROO", "SAN LUIS POTOSÍ", 
            "SINALOA", "SONORA", "TABASCO", "TAMAULIPAS", "TLAXCALA", "VERACRUZ", "YUCATÁN", "ZACATECAS"
        ]

        # --- TÍTULO ---
        header = tk.Frame(root, bg="#2c3e50", pady=15)
        header.pack(fill="x")
        
        tk.Button(header, text="⬅ VOLVER A DESPACHO", bg="#34495e", fg="white", 
                  font=FONT_SMALL_BOLD, command=self.regresar_a_salidas).pack(side="left", padx=10)
        
        tk.Label(header, text="DIRECTORIO DE MUNICIPIOS Y ENTIDADES", fg="white", 
                 bg="#2c3e50", font=FONT_SUBTITLE).pack(expand=True)

        # --- FORMULARIO ---
        frame_form = tk.LabelFrame(root, text=" Registrar Nuevo Destino ", font=FONT_BUTTON, padx=15, pady=15)
        frame_form.pack(fill="x", padx=20, pady=15)

        tk.Label(frame_form, text="MUNICIPIO:").grid(row=0, column=0, sticky="w")
        self.ent_nombre = ttk.Entry(frame_form, width=25, font=FONT_LABEL)
        self.ent_nombre.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="ESTADO:").grid(row=0, column=2, sticky="w", padx=(15,0))
        self.combo_estado_rep = ttk.Combobox(frame_form, values=self.lista_estados, state="readonly", width=25)
        self.combo_estado_rep.set("ESTADO DE MÉXICO")
        self.combo_estado_rep.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(frame_form, text="➕ GUARDAR DESTINO", bg="#27ae60", fg="white", 
                  font=FONT_LABEL_BOLD, command=self.agregar).grid(row=0, column=4, padx=15)

        # --- ACCIONES ---
        frame_acciones = tk.Frame(root, bg="#f4f6f7")
        frame_acciones.pack(fill="x", padx=20)
        
        tk.Button(frame_acciones, text="✏️ EDITAR SELECCIONADO", bg="#2980b9", fg="white", 
                  command=self.abrir_ventana_edicion).pack(side="left", padx=5)
        tk.Button(frame_acciones, text="🗑 ELIMINAR", bg="#e74c3c", fg="white", 
                  command=self.eliminar).pack(side="left", padx=5)

        # --- TABLA ---
        columnas = ("ID", "MUNICIPIO", "ENTIDAD", "ESTATUS")
        self.tabla = ttk.Treeview(root, columns=columnas, show="headings")
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center")
        
        self.tabla.column("MUNICIPIO", width=250, anchor="w")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabla.tag_configure('inactivo', background='#fadbd8')

        self.listar()

    def regresar_a_salidas(self):
        """Cierra esta ventana y vuelve a mostrar la ventana de Salidas"""
        self.root.destroy()
        if self.parent_window:
            # CORRECCIÓN: Accedemos al atributo .root de la ventana padre
            self.parent_window.root.deiconify() 
            
            # Refrescamos los datos en la ventana de salidas si el método existe
            if hasattr(self.parent_window, 'actualizar_combobox_municipios'):
                self.parent_window.actualizar_combobox_municipios()

    def listar(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, estado_republica, estatus FROM municipios ORDER BY nombre ASC")
        for fila in cursor.fetchall():
            tag = 'inactivo' if fila[3] == 'INACTIVO' else ''
            self.tabla.insert("", "end", values=fila, tags=(tag,))
        conn.close()

    def agregar(self):
        mun = self.ent_nombre.get().strip().upper()
        est_rep = self.combo_estado_rep.get()
        if not mun:
            messagebox.showwarning("Faltan datos", "El nombre del municipio es obligatorio.")
            return
        try:
            conn = sqlite3.connect(self.db_name)
            conn.execute("INSERT INTO municipios (nombre, estado_republica, estatus) VALUES (?, ?, 'ACTIVO')", 
                         (mun, est_rep))
            conn.commit(); conn.close()
            self.ent_nombre.delete(0, tk.END)
            self.listar()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Este destino ya existe.")

    def abrir_ventana_edicion(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione un registro para editar.")
            return

        valores = self.tabla.item(sel)['values']
        id_mun, nombre_actual, estado_actual, estatus_actual = valores

        win_ed = tk.Toplevel(self.root)
        win_ed.title(f"Editando: {nombre_actual}")
        center_window(win_ed, *EDIT_DIALOG_SIZE)
        win_ed.grab_set()

        tk.Label(win_ed, text="MODIFICAR DESTINO", font=FONT_BUTTON_LARGE, pady=15).pack()

        tk.Label(win_ed, text="Nombre:").pack()
        ent_ed_nom = ttk.Entry(win_ed, width=35)
        ent_ed_nom.insert(0, nombre_actual)
        ent_ed_nom.pack(pady=5)

        tk.Label(win_ed, text="Estado:").pack()
        comb_ed_est = ttk.Combobox(win_ed, values=self.lista_estados, state="readonly", width=32)
        comb_ed_est.set(estado_actual)
        comb_ed_est.pack(pady=5)

        tk.Label(win_ed, text="Estatus:").pack()
        comb_ed_stat = ttk.Combobox(win_ed, values=["ACTIVO", "INACTIVO"], state="readonly", width=32)
        comb_ed_stat.set(estatus_actual)
        comb_ed_stat.pack(pady=5)

        def guardar_cambios():
            n_nom = ent_ed_nom.get().strip().upper()
            n_est = comb_ed_est.get()
            n_sta = comb_ed_stat.get()
            if not n_nom: return
            conn = sqlite3.connect(self.db_name)
            conn.execute("UPDATE municipios SET nombre=?, estado_republica=?, estatus=? WHERE id=?", 
                         (n_nom, n_est, n_sta, id_mun))
            conn.commit(); conn.close()
            self.listar()
            win_ed.destroy()
            messagebox.showinfo("Éxito", "Cambios guardados.")

        tk.Button(win_ed, text="💾 GUARDAR", bg="#2980b9", fg="white", 
                  command=guardar_cambios).pack(pady=20)

    def eliminar(self):
        sel = self.tabla.selection()
        if not sel: return
        id_mun = self.tabla.item(sel)['values'][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar registro?"):
            conn = sqlite3.connect(self.db_name)
            conn.execute("DELETE FROM municipios WHERE id=?", (id_mun,))
            conn.commit(); conn.close()
            self.listar()