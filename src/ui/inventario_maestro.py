import tkinter as tk
from ui.style import *
from tkinter import ttk, messagebox
import sqlite3
from data.inventario_db import InventarioDB

class VentanaMaestro:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window 
        self.root.title("SISTEMA PLANACE - INVENTARIO MAESTRO")
        center_window(self.root, *MODULE_WINDOW_SIZE)
        
        # Variables de Paginación y DB
        self.pagina_actual = 0
        self.registros_por_pagina = 50
        self.db = InventarioDB()
        
        self.root.protocol("WM_DELETE_WINDOW", self.regresar)
        
        # --- BARRA DE NAVEGACIÓN SUPERIOR ---
        nav_bar = tk.Frame(root, bg="#2c3e50", pady=10)
        nav_bar.pack(fill="x")
        tk.Button(nav_bar, text="⬅ REGRESAR AL MENÚ", bg="#95a5a6", fg="white", 
                  font=FONT_BUTTON, command=self.regresar).pack(side="left", padx=20)
        tk.Label(nav_bar, text="CATÁLOGO MAESTRO DE MEDICAMENTOS", bg="#2c3e50", 
                 fg="white", font=FONT_HEADER).pack(side="left", padx=50)

        # --- PANEL SUPERIOR: REGISTRO (PARA INGRESOS NUEVOS) ---
        self.frame_registro = tk.LabelFrame(root, text=" REGISTRO DE NUEVO INGRESO ", font=FONT_BUTTON, padx=10, pady=10)
        self.frame_registro.pack(fill="x", padx=20, pady=10)

        self.inputs = {}
        campos = [
            ("SKU/CÓDIGO:", "sku", 0, 0), ("Nombre:", "nombre", 0, 2),
            ("Gramaje:", "gramaje", 0, 4), ("Presentación:", "presentacion", 1, 0),
            ("Laboratorio:", "laboratorio", 1, 2), ("Grupo:", "grupo", 1, 4),
            ("Tipo:", "tipo", 2, 0), ("Stock Mínimo:", "s_min", 2, 2),
            ("Stock Máximo:", "s_max", 2, 4), ("Cantidad Ingreso:", "cantidad", 3, 0)
        ]

        for label_text, key, r, c in campos:
            tk.Label(self.frame_registro, text=label_text).grid(row=r, column=c, sticky="w", padx=5)
            ent = ttk.Entry(self.frame_registro)
            ent.grid(row=r, column=c+1, padx=5, pady=5, sticky="ew")
            self.inputs[key] = ent

        tk.Button(self.frame_registro, text="💾 GUARDAR REGISTRO", bg="#27ae60", fg="white",
                  font=FONT_BUTTON, command=self.guardar_datos).grid(row=3, column=4, columnspan=2, sticky="ew", padx=5)

        # --- PANEL INTERMEDIO: CONSULTA ---
        self.frame_lista = tk.LabelFrame(root, text=" CONSULTA DE INVENTARIO ", font=FONT_BUTTON, padx=10, pady=10)
        self.frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

        top_lista = tk.Frame(self.frame_lista)
        top_lista.pack(fill="x")

        self.entry_busqueda = ttk.Entry(top_lista)
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.entry_busqueda.insert(0, "Buscar por nombre...")
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.reset_y_filtrar())
        self.entry_busqueda.bind("<FocusIn>", lambda e: self.entry_busqueda.delete(0, tk.END) if self.entry_busqueda.get() == "Buscar por nombre..." else None)
        self.entry_busqueda.bind("<FocusOut>", lambda e: self.entry_busqueda.insert(0, "Buscar por nombre...") if not self.entry_busqueda.get() else None)
        
        # --- NUEVO: Checkbox para ver inactivos ---
        self.var_ver_inactivos = tk.IntVar()
        self.chk_inactivos = tk.Checkbutton(top_lista, text="Ver Inactivos (Bajas)", variable=self.var_ver_inactivos, command=self.reset_y_filtrar)
        self.chk_inactivos.pack(side="left", padx=10)
        
        tk.Button(top_lista, text="✏️ EDITAR / CORREGIR", bg="#3498db", fg="white", command=self.abrir_ventana_edicion).pack(side="left", padx=2)
        tk.Button(top_lista, text="🗑 DAR DE BAJA", bg="#e74c3c", fg="white", command=self.eliminar_datos).pack(side="left", padx=2)

        
        # --- NUEVO FILTRO: COMBOBOX POR TIPO ---
        tk.Label(top_lista, text="Filtrar Tipo:").pack(side="left", padx=(10, 2))
        self.combo_tipo = ttk.Combobox(top_lista, state="readonly", width=15)
        self.combo_tipo.pack(side="left", padx=5)
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda e: self.reset_y_filtrar())
        
        # Llenar el Combobox con los tipos de la base de datos
        self.cargar_tipos()
        # --- NUEVO: Botón para Reactivar ---
        tk.Button(top_lista, text="✅ REACTIVAR", bg="#27ae60", fg="white", command=self.reactivar_datos).pack(side="left", padx=2)
        
        # --- TABLA ---
        columnas = ("SKU", "NOMBRE", "GRAMAJE", "PRESENTACION", "LABORATORIO", "GRUPO", "TIPO", "STOCK", "MIN", "MAX")
        self.tabla = ttk.Treeview(self.frame_lista, columns=columnas, show="headings")
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center", width=100)
        self.tabla.pack(fill="both", expand=True)

        # --- PAGINACIÓN ---
        self.frame_paginacion = tk.Frame(self.frame_lista)
        self.frame_paginacion.pack(fill="x", pady=5)
        self.btn_anterior = tk.Button(self.frame_paginacion, text="◀ Anterior", command=self.pagina_anterior)
        self.btn_anterior.pack(side="left", padx=20)
        self.lbl_pagina = tk.Label(self.frame_paginacion, text="Página 1", font=FONT_BUTTON)
        self.lbl_pagina.pack(side="left", expand=True)
        self.btn_siguiente = tk.Button(self.frame_paginacion, text="Siguiente ▶", command=self.pagina_siguiente)
        self.btn_siguiente.pack(side="right", padx=20)

        self.actualizar_tabla()

    def guardar_datos(self):
        """Valida campos y bloquea el registro si el SKU ya existe o los límites son ilógicos"""
        sku = self.inputs['sku'].get().strip().upper()
        nombre = self.inputs['nombre'].get().strip().upper()
        
        errores = []
        if not sku: errores.append("- El SKU/CÓDIGO es obligatorio.")
        if not nombre: errores.append("- El NOMBRE es obligatorio.")

        def get_int(key, label):
            try:
                val = self.inputs[key].get().strip()
                return int(val) if val else 0
            except ValueError:
                errores.append(f"- El campo '{label}' debe ser un número entero.")
                return None

        mi = get_int('s_min', "Stock Mínimo")
        ma = get_int('s_max', "Stock Máximo")
        cant = get_int('cantidad', "Cantidad Ingreso")

        if mi is not None and ma is not None:
            if mi > ma:
                errores.append("- El Stock Mínimo no puede ser mayor al Stock Máximo.")

        if errores:
            messagebox.showerror("Error de Validación", "\n".join(errores))
            return

        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM medicamentos WHERE sku = ?", (sku,))
            registro_existente = cursor.fetchone()
            conn.close()

            if registro_existente:
                messagebox.showerror("SKU DUPLICADO", 
                    f"ERROR: El SKU '{sku}' ya está registrado.\n"
                    f"Pertenece a: {registro_existente[0]}\n\n"
                    "Si desea cambiar sus datos, use el botón 'EDITAR / CORREGIR'.")
                self.inputs['sku'].focus()
                return 

            datos = (
                sku, nombre, 
                self.inputs['gramaje'].get().upper(),
                self.inputs['presentacion'].get().upper(), 
                self.inputs['laboratorio'].get().upper(),
                self.inputs['grupo'].get().upper(), 
                self.inputs['tipo'].get().upper(),
                cant, mi, ma
            )
            
            self.db.registrar_o_actualizar(datos, es_edicion=False)
            self.limpiar_formulario()
            self.actualizar_tabla()
            messagebox.showinfo("Éxito", f"Producto {sku} registrado correctamente.")

        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudo completar el registro: {e}")

    def abrir_ventana_edicion(self):
        """Ventana de corrección directa: SOBREESCRIBE los valores"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Por favor, seleccione un producto de la tabla para corregir.")
            return

        datos_fila = self.tabla.item(seleccion)['values']
        ventana_ed = tk.Toplevel(self.root)
        ventana_ed.title("CORRECCIÓN MANUAL DE INVENTARIO")
        center_window(ventana_ed, *EDIT_DIALOG_SIZE)
        ventana_ed.grab_set()
        
        main_frame = tk.Frame(ventana_ed, padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="EDICIÓN DIRECTA (REEMPLAZAR DATOS)", 
                 font=FONT_SUBTITLE, fg="#c0392b").grid(row=0, column=0, columnspan=4, pady=(0, 20))

        entradas_ed = {}
        config_campos = [
            ("sku", "SKU (ID):", 0), ("nombre", "Nombre:", 1), ("gramaje", "Gramaje:", 2),
            ("presentacion", "Presentación:", 3), ("laboratorio", "Laboratorio:", 4),
            ("grupo", "Grupo:", 5), ("tipo", "Tipo:", 6), ("stock_real", "Stock Real Actual:", 7),
            ("s_min", "Mínimo:", 8), ("s_max", "Máximo:", 9)
        ]

        for i, (clave, etiqueta, idx) in enumerate(config_campos):
            fila, columna = (i // 2) + 1, (i % 2) * 2
            tk.Label(main_frame, text=etiqueta, font=FONT_LABEL_BOLD).grid(row=fila, column=columna, sticky="w", pady=10)
            en = ttk.Entry(main_frame, width=25)
            en.grid(row=fila, column=columna + 1, padx=10, pady=10)
            entradas_ed[clave] = en
            en.insert(0, datos_fila[idx])
            if clave == "sku": en.config(state="disabled")

        def save_edit():
            try:
                mi, ma = int(entradas_ed['s_min'].get()), int(entradas_ed['s_max'].get())
                if mi > ma:
                    messagebox.showerror("Error", "El límite Mínimo no puede ser mayor al Máximo.")
                    return

                d = (
                    entradas_ed['sku'].get(),
                    entradas_ed['nombre'].get().upper(),
                    entradas_ed['gramaje'].get().upper(),
                    entradas_ed['presentacion'].get().upper(),
                    entradas_ed['laboratorio'].get().upper(),
                    entradas_ed['grupo'].get().upper(),
                    entradas_ed['tipo'].get().upper(),
                    int(entradas_ed['stock_real'].get()), 
                    mi, ma
                )
                
                self.db.registrar_o_actualizar(d, es_edicion=True)
                self.actualizar_tabla()
                ventana_ed.destroy()
                messagebox.showinfo("Éxito", "Los datos han sido corregidos correctamente.")
            except ValueError:
                messagebox.showerror("Error", "Verifique que el Stock y los Límites sean números.")

        tk.Button(main_frame, text="💾 APLICAR CORRECCIÓN", command=save_edit, bg="#2980b9", fg="white", 
                  font=FONT_BUTTON, height=2).grid(row=7, column=0, columnspan=4, sticky="ew", pady=30)

    def actualizar_tabla(self):
        for item in self.tabla.get_children(): 
            self.tabla.delete(item)
            
        offset = self.pagina_actual * self.registros_por_pagina
        busqueda = self.entry_busqueda.get().strip()
        
        if busqueda == "Buscar por nombre...":
            busqueda = ""

        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        
        # Filtro de estatus dependiente de la casilla (Checkbox)
        if self.var_ver_inactivos.get() == 1:
            filtro_estatus = "estatus = 'INACTIVO'"
        else:
            filtro_estatus = "(estatus = 'ACTIVO' OR estatus IS NULL)"
            
        query = f"SELECT sku, nombre, gramaje, presentacion, laboratorio, grupo, tipo, stock_actual, stock_min, stock_max FROM medicamentos WHERE {filtro_estatus}"
        parametros = []
        
        # --- FILTRO POR NOMBRE ---
        if busqueda:
            query += " AND nombre LIKE ?"
            parametros.append(f"%{busqueda.upper()}%")
            
        # --- NUEVO FILTRO POR TIPO ---
        tipo_seleccionado = self.combo_tipo.get()
        if tipo_seleccionado and tipo_seleccionado != "Todos los Tipos":
            query += " AND tipo = ?"
            parametros.append(tipo_seleccionado)
            
        # Paginación y ordenamiento
        query += " ORDER BY nombre ASC LIMIT ? OFFSET ?"
        parametros.extend([self.registros_por_pagina, offset])
        
        cursor.execute(query, tuple(parametros))
        filas = cursor.fetchall()
        
        for fila in filas: 
            self.tabla.insert("", "end", values=fila)
            
        self.btn_anterior.config(state="normal" if self.pagina_actual > 0 else "disabled")
        self.btn_siguiente.config(state="normal" if len(filas) == self.registros_por_pagina else "disabled")
        self.lbl_pagina.config(text=f"Página {self.pagina_actual + 1}")
        conn.close()

    def reactivar_datos(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Por favor, seleccione un producto de la tabla para reactivar.")
            return
            
        sku = self.tabla.item(seleccion)['values'][0]
        
        if self.var_ver_inactivos.get() == 0:
            messagebox.showinfo("Aviso", "Este producto ya está activo. Debe buscar en 'Ver Inactivos' para reactivar productos dados de baja.")
            return

        if messagebox.askyesno("Confirmar", f"¿Desea volver a activar el SKU {sku}?"):
            conn = sqlite3.connect(self.db.db_name)
            conn.execute("UPDATE medicamentos SET estatus = 'ACTIVO' WHERE sku = ?", (sku,))
            conn.commit()
            conn.close()
            self.actualizar_tabla()
            messagebox.showinfo("Éxito", f"El producto {sku} ha sido reactivado y vuelve a aparecer en el catálogo.")

    def eliminar_datos(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Por favor, seleccione un producto de la tabla para dar de baja.")
            return
            
        sku = self.tabla.item(seleccion)['values'][0]
        
        if self.var_ver_inactivos.get() == 1:
            messagebox.showinfo("Aviso", "Este producto ya está dado de baja.")
            return

        if messagebox.askyesno("Confirmar", f"¿Desea dar de baja el SKU {sku}?\n\n(Se ocultará del catálogo, pero mantendrá su historial de movimientos)"):
            conn = sqlite3.connect(self.db.db_name)
            conn.execute("UPDATE medicamentos SET estatus = 'INACTIVO' WHERE sku = ?", (sku,))
            conn.commit()
            conn.close()
            self.actualizar_tabla()
    def cargar_tipos(self):
        """Obtiene los tipos únicos de la base de datos para llenar el Combobox"""
        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            # Seleccionar los tipos únicos que no estén vacíos
            cursor.execute("SELECT DISTINCT tipo FROM medicamentos WHERE tipo IS NOT NULL AND tipo != '' ORDER BY tipo ASC")
            tipos = [fila[0] for fila in cursor.fetchall()]
            conn.close()
            
            # Insertar la opción por defecto al inicio de la lista
            tipos.insert(0, "Todos los Tipos")
            
            # Asignar los valores al Combobox y seleccionar el primero por defecto
            self.combo_tipo['values'] = tipos
            self.combo_tipo.current(0)
            
        except Exception as e:
            # En caso de error, dejamos solo la opción por defecto
            self.combo_tipo['values'] = ["Todos los Tipos"]
            self.combo_tipo.current(0)

    def reset_y_filtrar(self): 
        self.pagina_actual = 0
        self.actualizar_tabla()

    def pagina_siguiente(self): 
        self.pagina_actual += 1
        self.actualizar_tabla()

    def pagina_anterior(self): 
        self.pagina_actual -= 1
        self.actualizar_tabla()

    def regresar(self): 
        self.root.destroy()
        self.main_window.deiconify()

    def limpiar_formulario(self):
        for ent in self.inputs.values(): 
            ent.delete(0, tk.END)
        self.inputs['sku'].focus()