import tkinter as tk
from ui.style import *
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import winsound

class VentanaGeneral:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.root.title("INVENTARIO GENERAL - CONTROL OPERATIVO")
        center_window(self.root, *MODULE_WINDOW_SIZE)
        self.root.configure(bg="#f4f6f7")
        
        # --- VARIABLES DE CONTROL ---
        self.pagina_actual = 0
        self.registros_por_pagina = 50
        self.filtro_estado = tk.StringVar(value="TODOS")
        
        # Buffer de seguridad (Para conteo previo)
        self.sku_en_proceso = None
        self.nombre_en_proceso = ""
        self.conteo_actual = 0
        
        self.root.protocol("WM_DELETE_WINDOW", self.regresar)

        # --- 1. HEADER ---
        nav = tk.Frame(root, bg="#2980b9", pady=10)
        nav.pack(side="top", fill="x")
        tk.Button(nav, text="⬅ REGRESAR AL MENÚ", command=self.regresar, 
                  bg="#34495e", fg="white", font=FONT_LABEL_BOLD).pack(side="left", padx=20)
        tk.Label(nav, text="SISTEMA DE ENTRADAS CONTROLADAS POR BUFFER", bg="#2980b9", 
                 fg="white", font=FONT_HEADER).pack()

        # --- 2. PANEL DE FILTROS ---
        self.frame_filtros = tk.Frame(root, bg="#ecf0f1", pady=10)
        self.frame_filtros.pack(side="top", fill="x")

        tk.Label(self.frame_filtros, text="🔍 BUSCAR PRODUCTO:", bg="#ecf0f1", font=FONT_BUTTON).pack(side="left", padx=(20, 5))
        self.entry_busqueda = ttk.Entry(self.frame_filtros, font=FONT_ENTRY)
        self.entry_busqueda.pack(side="left", padx=5)
        self.entry_busqueda.bind("<KeyRelease>", self.reset_y_actualizar)

        tk.Label(self.frame_filtros, text="FILTRO STOCK:", bg="#ecf0f1", font=FONT_BUTTON).pack(side="left", padx=(20, 5))
        self.combo_filtro = ttk.Combobox(self.frame_filtros, textvariable=self.filtro_estado, state="readonly", width=15)
        self.combo_filtro['values'] = ("TODOS", "BAJO MÍNIMO", "NORMAL", "SOBRE MÁXIMO")
        self.combo_filtro.pack(side="left", padx=5)
        self.combo_filtro.bind("<<ComboboxSelected>>", self.reset_y_actualizar)
        
                # --- 3. PANEL DE OPERACIÓN (CORREGIDO) ---
        # --- 3. PANEL DE OPERACIÓN (SIEMPRE EDITABLE) ---
        self.frame_movimientos = tk.LabelFrame(root, text=" ÁREA DE CONTEO PREVIO ", 
                                            font=FONT_BUTTON, padx=15, pady=15, fg="#2980b9", bg="white")
        self.frame_movimientos.pack(side="top", fill="x", padx=20, pady=5)

        tk.Label(self.frame_movimientos, text="CANT:", font=FONT_BUTTON_LARGE, bg="white").grid(row=0, column=0, padx=5)
        self.ent_cantidad = ttk.Entry(self.frame_movimientos, width=7, font=FONT_HEADER_REGULAR)
        self.ent_cantidad.insert(0, "1") 
        self.ent_cantidad.grid(row=0, column=1, padx=5)

        tk.Label(self.frame_movimientos, text="SKU:", font=FONT_BUTTON_LARGE, bg="white").grid(row=0, column=2, padx=5)
        self.ent_sku_sel = ttk.Entry(self.frame_movimientos, width=20, font=FONT_HEADER_REGULAR)
        self.ent_sku_sel.grid(row=0, column=3, padx=10)
        self.ent_sku_sel.bind("<Return>", self.gestionar_escaneo)
        # Columna 4: Indicador de Buffer (Aumentamos la columna para no chocar)
        self.lbl_conteo_status = tk.Label(self.frame_movimientos, text="ESPERANDO ESCANEO...", 
                                        font=FONT_SUBTITLE, fg="#7f8c8d", bg="#f8f9f9", width=40, relief="sunken", pady=5)
        self.lbl_conteo_status.grid(row=0, column=4, padx=20)

        # Columna 5 y 6: Botones
        self.btn_registrar = tk.Button(self.frame_movimientos, text="✅ REGISTRAR", command=self.confirmar_registro_final, 
                                    bg="#27ae60", fg="white", font=FONT_BUTTON, state="disabled", width=12, pady=5)
        self.btn_registrar.grid(row=0, column=5, padx=5)

        self.btn_cancelar = tk.Button(self.frame_movimientos, text="❌ CANCELAR", command=self.reset_buffer, 
                                    bg="#c0392b", fg="white", font=FONT_BUTTON, state="disabled", width=12, pady=5)
        self.btn_cancelar.grid(row=0, column=6, padx=5)

                
        # --- 4. BANNER DE ALERTA ---
        self.frame_alerta = tk.Frame(root, bg="#e74c3c")
        self.lbl_alerta = tk.Label(self.frame_alerta, text="", fg="white", bg="#e74c3c", font=FONT_BUTTON)
        self.lbl_alerta.pack(pady=2)

        # --- 5. TABLA CENTRAL ---
        self.frame_contenedor_tabla = tk.Frame(root, padx=20, pady=5)
        self.frame_contenedor_tabla.pack(side="top", fill="both", expand=True)

        columnas = ("SKU", "DESCRIPCIÓN", "E. REGISTRO", "E. DEVOLUCIÓN", 
                    "S. MUNICIPIO", "S. MERMA", "STOCK ACTUAL", "ESTADO")
        
        self.tabla = ttk.Treeview(self.frame_contenedor_tabla, columns=columnas, show="headings")
        scroll_y = ttk.Scrollbar(self.frame_contenedor_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        
        scroll_y.pack(side="right", fill="y")
        self.tabla.pack(side="left", fill="both", expand=True)

        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center", width=115)
        self.tabla.column("DESCRIPCIÓN", width=380, anchor="w")

        self.tabla.tag_configure('stock_bajo', background='#fadbd8')
        self.tabla.tag_configure('stock_sobre', background='#fdebd0')

        # --- 6. PAGINACIÓN ---
        self.frame_paginacion = tk.Frame(root, pady=10)
        self.frame_paginacion.pack(side="bottom", fill="x")
        
        self.btn_anterior = tk.Button(self.frame_paginacion, text="◀ Anterior", command=self.pagina_anterior, width=15)
        self.btn_anterior.pack(side="left", padx=50)
        
        self.lbl_pagina = tk.Label(self.frame_paginacion, text="Página 1", font=FONT_BUTTON)
        self.lbl_pagina.pack(side="left", expand=True)
        
        self.btn_siguiente = tk.Button(self.frame_paginacion, text="Siguiente ▶", command=self.pagina_siguiente, width=15)
        self.btn_siguiente.pack(side="right", padx=50)

        self.actualizar_tabla()

    # --- LÓGICA DE BUFFER Y SEGURIDAD ---

    def gestionar_escaneo(self, event=None):
        sku = self.ent_sku_sel.get().strip().upper()
        if not sku: return

        # LEER CANTIDAD: Siempre disponible para el usuario
        try:
            unidades = int(self.ent_cantidad.get().strip())
            if unidades <= 0: unidades = 1
        except:
            unidades = 1

        # VALIDACIÓN DE SKU: Solo bloqueamos si intenta escanear UN PRODUCTO DIFERENTE
        if self.sku_en_proceso and self.sku_en_proceso != sku:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            messagebox.showwarning("Pendiente", 
                                f"Estás contando '{self.nombre_en_proceso}'.\n"
                                f"Regístralo antes de cambiar a otro SKU.")
            self.ent_sku_sel.delete(0, tk.END)
            return

        # Consulta a Base de Datos
        conn = sqlite3.connect("sistema_salud.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, estatus FROM medicamentos WHERE sku = ?", (sku,))
        res = cursor.fetchone()
        conn.close()

        if res:
            nombre, estatus = res
            if estatus == 'INACTIVO':
                winsound.MessageBeep(winsound.MB_ICONERROR)
                messagebox.showerror("Error", "Producto inactivo.")
                return

            # Si es el primer escaneo del bloque, guardamos el nombre
            if not self.sku_en_proceso:
                self.sku_en_proceso = sku
                self.nombre_en_proceso = nombre
                self.btn_registrar.config(state="normal")
                self.btn_cancelar.config(state="normal")

            # SUMAR AL CONTEO: Usa el valor actual que esté en el cuadrito de CANT
            self.conteo_actual += unidades
            
            # Bip de éxito
            winsound.Beep(2000, 150)

            # Actualizar etiqueta visual
            self.lbl_conteo_status.config(
                text=f"BUFFER: {self.conteo_actual} UNIDADES DE {self.nombre_en_proceso}", 
                fg="#d35400", bg="#fff3e0"
            )
            
            # Limpiar SKU para el siguiente escaneo, pero NO limpiar la cantidad 
            # (por si el usuario quiere seguir escaneando de 10 en 10, por ejemplo)
            self.ent_sku_sel.delete(0, tk.END)
            self.ent_sku_sel.focus()
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            messagebox.showerror("No Encontrado", f"El SKU '{sku}' no existe.")
        
    def confirmar_registro_final(self):
        if not self.sku_en_proceso: return

        if not messagebox.askyesno("Confirmar", f"¿Registrar {self.conteo_actual} pzs de {self.nombre_en_proceso}?"):
            return

        try:
            conn = sqlite3.connect("sistema_salud.db")
            cursor = conn.cursor()
            ahora = datetime.now()
            periodo = "PRIMAVERA" if ahora.month <= 4 else ("VERANO" if ahora.month <= 8 else "OTOÑO")

            # Actualizar Stocks
            cursor.execute("UPDATE medicamentos SET entradas_registro = entradas_registro + ?, stock_actual = stock_actual + ? WHERE sku = ?", 
                           (self.conteo_actual, self.conteo_actual, self.sku_en_proceso))

            # Historial
            cursor.execute("""INSERT INTO historial_retornos (municipio, sku, tipo_movimiento, cantidad, fecha, periodo, anio) 
                              VALUES ('ALMACÉN CENTRAL', ?, 'COMPRA', ?, ?, ?, ?)
                              ON CONFLICT(municipio, sku, periodo, anio, tipo_movimiento) DO UPDATE SET
                              cantidad = cantidad + excluded.cantidad, fecha = excluded.fecha""", 
                           (self.sku_en_proceso, self.conteo_actual, ahora.strftime("%Y-%m-%d %H:%M:%S"), periodo, str(ahora.year)))

            conn.commit()
            conn.close()

            # Sonido de éxito final
            winsound.Beep(1500, 100); winsound.Beep(2200, 200)
            
            self.reset_buffer()
            self.actualizar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def reset_buffer(self):
        self.sku_en_proceso = None
        self.nombre_en_proceso = ""
        self.conteo_actual = 0
        self.lbl_conteo_status.config(text="ESPERANDO ESCANEO...", fg="#7f8c8d", bg="#f8f9f9")
        self.btn_registrar.config(state="disabled")
        self.btn_cancelar.config(state="disabled")
        self.ent_cantidad.config(state="normal")
        self.ent_cantidad.delete(0, tk.END)
        self.ent_cantidad.insert(0, "1")
        self.ent_sku_sel.delete(0, tk.END)
        self.ent_sku_sel.focus()

    # --- MÉTODOS DE TABLA Y FILTROS ---

    def actualizar_tabla(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        offset = self.pagina_actual * self.registros_por_pagina
        
        conn = sqlite3.connect("sistema_salud.db")
        cursor = conn.cursor()
        busqueda = f"%{self.entry_busqueda.get().strip()}%"
        filtro_sel = self.filtro_estado.get()

        query = """SELECT sku, nombre, gramaje, presentacion, entradas_registro, 
                          entradas_devolucion, salidas_municipio, salidas_merma, 
                          stock_actual, stock_min, stock_max 
                   FROM medicamentos 
                   WHERE (nombre LIKE ? OR sku LIKE ?) 
                   AND (estatus = 'ACTIVO' OR estatus IS NULL)
                   ORDER BY nombre ASC LIMIT ? OFFSET ?"""
        
        cursor.execute(query, (busqueda, busqueda, self.registros_por_pagina, offset))
        rows = cursor.fetchall()
        
        bajo_minimo = 0
        for r in rows:
            sku, nom, gra, pre, e_reg, e_dev, s_mun, s_mer, stock, s_min, s_max = r
            desc = f"{nom} {gra} - {pre}"
            estado = "ÓPTIMO"; tag = ""
            
            if stock <= s_min:
                estado = "⚠️ REABASTECER"; tag = "stock_bajo"; bajo_minimo += 1
            elif stock > s_max:
                estado = "❗ EXCESO"; tag = "stock_sobre"

            # Aplicar filtro de vista
            mostrar = (filtro_sel == "TODOS") or \
                      (filtro_sel == "BAJO MÍNIMO" and stock <= s_min) or \
                      (filtro_sel == "NORMAL" and s_min < stock <= s_max) or \
                      (filtro_sel == "SOBRE MÁXIMO" and stock > s_max)

            if mostrar:
                self.tabla.insert("", "end", values=(sku, desc, e_reg, e_dev, s_mun, s_mer, stock, estado), tags=(tag,))

        self.btn_anterior.config(state="normal" if self.pagina_actual > 0 else "disabled")
        self.btn_siguiente.config(state="normal" if len(rows) == self.registros_por_pagina else "disabled")
        self.lbl_pagina.config(text=f"Página {self.pagina_actual + 1}")

        if bajo_minimo > 0 and filtro_sel == "TODOS":
            self.frame_alerta.pack(fill="x", after=self.frame_movimientos)
            self.lbl_alerta.config(text=f"ATENCIÓN: {bajo_minimo} PRODUCTOS CON STOCK CRÍTICO")
        else:
            self.frame_alerta.pack_forget()
        
        conn.close()

    def reset_y_actualizar(self, e=None): 
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