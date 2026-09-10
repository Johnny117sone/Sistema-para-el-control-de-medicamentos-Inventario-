import tkinter as tk
from ui.style import *
from tkinter import ttk, messagebox
import sqlite3
import winsound  # <--- Librería para los sonidos
from datetime import datetime
from data.inventario_db import InventarioDB

class VentanaDevoluciones:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.db = InventarioDB()
        
        # --- VARIABLES DE CONTROL (BUFFER Y PAGINACIÓN) ---
        self.sku_en_proceso = None
        self.nombre_en_proceso = ""
        self.conteo_actual = 0
        self.pagina_actual = 0
        self.registros_por_pagina = 50

        self.root.title("AUDITORÍA DE RETORNOS Y MERMAS")
        center_window(self.root, *MODULE_WINDOW_SIZE)
        self.root.configure(bg="#f4f6f7")
        self.root.protocol("WM_DELETE_WINDOW", self.regresar)

        # --- ENCABEZADO ---
        header = tk.Frame(root, bg="#8e44ad", pady=15)
        header.pack(fill="x")
        
        tk.Button(header, text="⬅ MENÚ", command=self.regresar, bg="#4a235a", fg="white", 
                  font=FONT_LABEL_BOLD, width=10).pack(side="left", padx=20)
        
        tk.Label(header, text="CONTROL DE SALDOS TERRITORIALES", bg="#8e44ad", 
                 fg="white", font=FONT_HEADER).pack(side="left", padx=30)

        # --- ZONA DE OPERACIÓN (BUFFER) ---
        frame_op = tk.LabelFrame(root, text=" REGISTRO RÁPIDO POR ESCÁNER (BUFFER) ", padx=20, pady=20, bg="white", font=FONT_BUTTON)
        frame_op.pack(fill="x", padx=30, pady=20)

        # 1. Municipio y Periodo
        tk.Label(frame_op, text="MUNICIPIO:", font=FONT_LABEL_BOLD, bg="white").grid(row=0, column=0, sticky="w")
        self.combo_municipio = ttk.Combobox(frame_op, state="readonly", font=FONT_ENTRY, width=35)
        self.combo_municipio.grid(row=0, column=1, padx=10, pady=10)
        self.actualizar_municipios()

        tk.Label(frame_op, text="PERIODO:", font=FONT_LABEL_BOLD, bg="white").grid(row=0, column=2, sticky="w", padx=20)
        self.combo_periodo = ttk.Combobox(frame_op, values=("PRIMAVERA", "VERANO", "OTOÑO"), state="readonly", width=15)
        self.combo_periodo.set("PRIMAVERA")
        self.combo_periodo.grid(row=0, column=3, padx=10, pady=10)

        # 2. Selector de Modo de Escaneo
        tk.Label(frame_op, text="MODO DE ESCANEO:", font=FONT_LABEL_BOLD, bg="white").grid(row=1, column=0, sticky="w", pady=10)
        
        self.tipo_ajuste = tk.StringVar(value="REGRESO")
        frame_toggle = tk.Frame(frame_op, bg="white")
        frame_toggle.grid(row=1, column=1, columnspan=3, sticky="w", pady=5)
        
        self.btn_modo_regreso = tk.Button(frame_toggle, text="🔄 REINGRESO (+1)", font=FONT_BUTTON, 
                                          bg="#27ae60", fg="white", relief="sunken", width=22, pady=5,
                                          command=lambda: self.cambiar_modo("REGRESO"))
        self.btn_modo_regreso.pack(side="left", padx=(0, 10))
        
        self.btn_modo_merma = tk.Button(frame_toggle, text="⚠️ MERMA (-1)", font=FONT_BUTTON, 
                                        bg="#ecf0f1", fg="gray", relief="raised", width=22, pady=5,
                                        command=lambda: self.cambiar_modo("MERMA"))
        self.btn_modo_merma.pack(side="left")

        # 3. SKU y Cantidad
        tk.Label(frame_op, text="SKU PRODUCTO:", font=FONT_LABEL_BOLD, bg="white").grid(row=2, column=0, sticky="w")
        self.ent_sku = ttk.Entry(frame_op, font=FONT_HEADER_REGULAR, width=20)
        self.ent_sku.grid(row=2, column=1, sticky="w", padx=10, pady=10)
        self.ent_sku.bind("<Return>", self.gestionar_buffer_devolucion)

        tk.Label(frame_op, text="CANTIDAD PIEZAS:", font=FONT_LABEL_BOLD, bg="white").grid(row=2, column=2, sticky="w", padx=20)
        self.ent_cant = ttk.Entry(frame_op, width=15, font=FONT_HEADER_REGULAR)
        self.ent_cant.insert(0, "1") 
        self.ent_cant.grid(row=2, column=3, sticky="w", padx=10, pady=10)

        # 4. Mensaje de Estado / Buffer
        self.lbl_status = tk.Label(frame_op, text="Esperando escaneo...", font=FONT_BUTTON_LARGE, bg="white", fg="gray")
        self.lbl_status.grid(row=4, column=0, columnspan=2, pady=10)

        # 5. Botones de Acción Final (Ubicados en la parte superior)
        self.btn_registrar = tk.Button(frame_op, text="✅ REGISTRAR", command=self.confirmar_ajuste_final, 
                                      bg="#27ae60", fg="white", font=FONT_BUTTON, state="disabled", 
                                      relief="raised", bd=4, width=15, pady=5)
        self.btn_registrar.grid(row=4, column=2, padx=5, pady=10)

        self.btn_cancelar = tk.Button(frame_op, text="❌ CANCELAR", command=self.reset_buffer, 
                                      bg="#c0392b", fg="white", font=FONT_BUTTON, state="disabled", 
                                      relief="raised", bd=4, width=15, pady=5)
        self.btn_cancelar.grid(row=4, column=3, padx=5, pady=10)

        # --- BOTÓN REVERTIR (Ahora en la parte superior derecha) ---
        self.btn_revertir_ajuste = tk.Button(frame_op, text="🔄 REVERTIR TABLA", 
                                             command=self.revertir_ajuste_error, 
                                             bg="#5d6d7e", fg="white", font=FONT_BUTTON,
                                             relief="raised", bd=4, width=18, pady=5)
        self.btn_revertir_ajuste.grid(row=4, column=4, padx=15, pady=10)

        # --- TABLA Y PAGINACIÓN (Se omite el diseño por brevedad, se mantiene igual) ---
        # ... [El resto del código UI se mantiene igual] ...
        
        # --- TABLA DE HISTORIAL CON BUSCADOR ---
        frame_tabla = tk.LabelFrame(root, text=" HISTORIAL DE AJUSTES ", bg="white", font=FONT_LABEL_BOLD)
        frame_tabla.pack(fill="both", expand=True, padx=30, pady=(10, 5))

        frame_buscador = tk.Frame(frame_tabla, bg="white")
        frame_buscador.pack(fill="x", pady=(5, 10), padx=5)
        
        tk.Label(frame_buscador, text="🔍 MUNICIPIO:", font=FONT_LABEL_BOLD, bg="white").pack(side="left")
        self.ent_busqueda_mun = ttk.Entry(frame_buscador, width=20, font=FONT_LABEL)
        self.ent_busqueda_mun.pack(side="left", padx=5)
        self.ent_busqueda_mun.bind("<KeyRelease>", self.reset_y_buscar)

        tk.Label(frame_buscador, text="PERIODO:", font=FONT_LABEL_BOLD, bg="white").pack(side="left", padx=(10, 2))
        self.combo_busqueda_per = ttk.Combobox(frame_buscador, values=("TODOS", "PRIMAVERA", "VERANO", "OTOÑO"), state="readonly", width=12)
        self.combo_busqueda_per.set("TODOS")
        self.combo_busqueda_per.pack(side="left", padx=2)
        self.combo_busqueda_per.bind("<<ComboboxSelected>>", self.reset_y_buscar)

        tk.Label(frame_buscador, text="AÑO:", font=FONT_LABEL_BOLD, bg="white").pack(side="left", padx=(10, 2))
        self.combo_busqueda_anio = ttk.Combobox(frame_buscador, values=["TODOS"] + [str(a) for a in range(2024, 2035)], state="readonly", width=8)
        self.combo_busqueda_anio.set("TODOS")
        self.combo_busqueda_anio.pack(side="left", padx=2)
        self.combo_busqueda_anio.bind("<<ComboboxSelected>>", self.reset_y_buscar)

        tk.Label(frame_buscador, text="TIPO:", font=FONT_LABEL_BOLD, bg="white").pack(side="left", padx=(10, 2))
        self.combo_busqueda_tipo = ttk.Combobox(frame_buscador, values=("TODOS", "REGRESO", "MERMA"), state="readonly", width=10)
        self.combo_busqueda_tipo.set("TODOS")
        self.combo_busqueda_tipo.pack(side="left", padx=2)
        self.combo_busqueda_tipo.bind("<<ComboboxSelected>>", self.reset_y_buscar)

        columnas = ("FECHA", "MUNICIPIO", "SKU", "TIPO", "CANT", "PERIODO")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center", width=120)
        
        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")
        self.tabla.pack(fill="both", expand=True, padx=5, pady=5)
        self.tabla.tag_configure('inactivo', foreground='#c0392b')

        # --- CONTROLES DE PAGINACIÓN ---
        self.frame_paginacion = tk.Frame(root, bg="#f4f6f7")
        self.frame_paginacion.pack(fill="x", pady=10)
        self.btn_anterior = tk.Button(self.frame_paginacion, text="◀ Anterior", command=self.pagina_anterior, width=15)
        self.btn_anterior.pack(side="left", padx=30)
        self.lbl_pagina = tk.Label(self.frame_paginacion, text="Página 1", font=FONT_BUTTON, bg="#f4f6f7")
        self.lbl_pagina.pack(side="left", expand=True)
        self.btn_siguiente = tk.Button(self.frame_paginacion, text="Siguiente ▶", command=self.pagina_siguiente, width=15)
        self.btn_siguiente.pack(side="right", padx=30)

        # --- NUEVO BOTÓN PARA REVERTIR AJUSTE ---
        
        self.listar_historial()
        self.ent_sku.focus()

    # --- LÓGICA DE BUFFER (PITIDO AÑADIDO) ---
    def gestionar_buffer_devolucion(self, event=None):
        sku = self.ent_sku.get().strip().upper()
        mun = self.combo_municipio.get()
        tipo = self.tipo_ajuste.get()
        per = self.combo_periodo.get()
        anio = str(datetime.now().year)

        try:
            cant_a_sumar = int(self.ent_cant.get().strip())
        except:
            cant_a_sumar = 1

        if not mun or "---" in mun:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            messagebox.showwarning("Atención", "Seleccione un municipio de origen.")
            return

        if self.sku_en_proceso and self.sku_en_proceso != sku:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            messagebox.showwarning("Pendiente", f"Primero registre '{self.nombre_en_proceso}'.")
            return

        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, estatus FROM medicamentos WHERE sku = ?", (sku,))
        res = cursor.fetchone()

        if res:
            nombre, estatus = res
            if estatus == 'INACTIVO':
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                confirmar = messagebox.askyesno("Producto Inactivo", f"El producto '{nombre}' está INACTIVO. ¿Desea continuar?")
                if not confirmar: 
                    self.ent_sku.delete(0, tk.END)
                    conn.close()
                    return

            # VALIDACIÓN DE SALDO ACTUALIZADA
            saldo_en_municipio = self.obtener_saldo_en_municipio(cursor, mun, sku, per, anio)
            
            # Verificamos si lo que ya está en buffer + lo nuevo supera lo que el municipio tiene
            if (self.conteo_actual + cant_a_sumar) > saldo_en_municipio:
                winsound.MessageBeep(winsound.MB_ICONHAND) # Sonido de error
                messagebox.showerror("Error de Saldo", 
                                     f"No puedes procesar {cant_a_sumar} pzs.\n"
                                     f"Saldo en {mun}: {saldo_en_municipio}\n"
                                     f"En buffer actualmente: {self.conteo_actual}")
                self.ent_sku.delete(0, tk.END)
                conn.close()
                return # Salimos para que no marque nada

            # SI PASA LA VALIDACIÓN, PROCEDEMOS CON EL MARCADO
            winsound.Beep(2500, 150) # Pitido de éxito
            
            if not self.sku_en_proceso:
                self.sku_en_proceso, self.nombre_en_proceso = sku, nombre
                self.btn_registrar.config(state="normal")
                self.btn_cancelar.config(state="normal")
                self.combo_municipio.config(state="disabled")
                self.combo_periodo.config(state="disabled")
                self.btn_modo_regreso.config(state="disabled")
                self.btn_modo_merma.config(state="disabled")

            self.conteo_actual += cant_a_sumar
            color = "#27ae60" if tipo == "REGRESO" else "#d35400"
            self.lbl_status.config(text=f"BUFFER ({tipo}): {self.conteo_actual} x {self.nombre_en_proceso}", fg=color)
            
        else:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            messagebox.showerror("Error", "SKU no encontrado.")
        
        self.ent_sku.delete(0, tk.END)
        conn.close()


    def confirmar_ajuste_final(self):
        tipo = self.tipo_ajuste.get()
        mun = self.combo_municipio.get()
        per = self.combo_periodo.get()
        anio = str(datetime.now().year)
        fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not messagebox.askyesno("Confirmar", f"¿Registrar {self.conteo_actual} pzs como {tipo} desde {mun}?"): return

        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()

            if tipo == "REGRESO":
                cursor.execute("""UPDATE medicamentos SET stock_actual = stock_actual + ?, 
                                  entradas_devolucion = entradas_devolucion + ?,
                                  salidas_municipio = salidas_municipio - ? WHERE sku = ?""", 
                               (self.conteo_actual, self.conteo_actual, self.conteo_actual, self.sku_en_proceso))
            else: # MERMA
                cursor.execute("""UPDATE medicamentos SET salidas_municipio = salidas_municipio - ?, 
                                  salidas_merma = salidas_merma + ? WHERE sku = ?""", 
                               (self.conteo_actual, self.conteo_actual, self.sku_en_proceso))

            cursor.execute("""INSERT INTO historial_retornos (municipio, sku, tipo_movimiento, cantidad, fecha, periodo, anio) 
                              VALUES (?, ?, ?, ?, ?, ?, ?)
                              ON CONFLICT(municipio, sku, periodo, anio, tipo_movimiento) 
                              DO UPDATE SET cantidad = cantidad + excluded.cantidad, fecha = excluded.fecha""", 
                           (mun, self.sku_en_proceso, tipo, self.conteo_actual, fecha_hoy, per, anio))

            conn.commit()
            
            # SONIDO DE REGISTRO EXITOSO (Doble pitido ascendente)
            winsound.Beep(1500, 100)
            winsound.Beep(2200, 200)

            conn.close()
            self.reset_buffer()
            self.reset_y_buscar()
            messagebox.showinfo("Éxito", "Ajuste registrado correctamente.")
        except Exception as e:
            winsound.MessageBeep(winsound.MB_ICONERROR)
            messagebox.showerror("Error", str(e))

    # --- MÉTODOS DE APOYO (Se mantienen iguales) ---
    def obtener_saldo_en_municipio(self, cursor, municipio, sku, periodo, anio):
        cursor.execute("""SELECT SUM(CASE WHEN tipo_movimiento = 'SALIDA MUNICIPIO' THEN cantidad ELSE 0 END) -
                                 SUM(CASE WHEN tipo_movimiento IN ('REGRESO', 'MERMA') THEN cantidad ELSE 0 END)
                          FROM historial_retornos WHERE municipio = ? AND sku = ? AND periodo = ? AND anio = ?""", 
                       (municipio, sku, periodo, anio))
        res = cursor.fetchone()
        return res[0] if res[0] is not None else 0

    def cambiar_modo(self, modo):
        self.tipo_ajuste.set(modo)
        if modo == "REGRESO":
            self.btn_modo_regreso.config(bg="#27ae60", fg="white", relief="sunken")
            self.btn_modo_merma.config(bg="#ecf0f1", fg="gray", relief="raised")
        else:
            self.btn_modo_regreso.config(bg="#ecf0f1", fg="gray", relief="raised")
            self.btn_modo_merma.config(bg="#d35400", fg="white", relief="sunken")
        self.ent_sku.focus()

    def actualizar_municipios(self):
        self.combo_municipio['values'] = self.db.obtener_municipios()
        self.combo_municipio.set("--- Seleccione Municipio ---")

    def listar_historial(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        busqueda_mun = self.ent_busqueda_mun.get().strip().upper()
        busqueda_per = self.combo_busqueda_per.get()
        busqueda_anio = self.combo_busqueda_anio.get()
        busqueda_tipo = self.combo_busqueda_tipo.get()
        offset = self.pagina_actual * self.registros_por_pagina

        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        query = """SELECT h.fecha, h.municipio, h.sku, h.tipo_movimiento, h.cantidad, h.periodo, m.estatus
                   FROM historial_retornos h LEFT JOIN medicamentos m ON h.sku = m.sku
                   WHERE h.tipo_movimiento IN ('REGRESO', 'MERMA')"""
        params = []
        if busqueda_mun: query += " AND h.municipio LIKE ?"; params.append(f"%{busqueda_mun}%")
        if busqueda_per != "TODOS": query += " AND h.periodo = ?"; params.append(busqueda_per)
        if busqueda_anio != "TODOS": query += " AND h.anio = ?"; params.append(busqueda_anio)
        if busqueda_tipo != "TODOS": query += " AND h.tipo_movimiento = ?"; params.append(busqueda_tipo)
        
        query += " ORDER BY h.fecha DESC LIMIT ? OFFSET ?"
        params.extend([self.registros_por_pagina, offset])
        cursor.execute(query, tuple(params))
        filas = cursor.fetchall()
        for f in filas:
            tag = ('inactivo',) if f[6] == 'INACTIVO' else ()
            self.tabla.insert("", "end", values=f[:6], tags=tag)
        
        self.btn_anterior.config(state="normal" if self.pagina_actual > 0 else "disabled")
        self.btn_siguiente.config(state="normal" if len(filas) == self.registros_por_pagina else "disabled")
        self.lbl_pagina.config(text=f"Página {self.pagina_actual + 1}")
        conn.close()

    def revertir_ajuste_error(self):
        """Anula un movimiento de Regreso o Merma y restaura los saldos originales"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione un ajuste en la tabla para revertir.")
            return

        # Obtener datos: ("FECHA", "MUNICIPIO", "SKU", "TIPO", "CANT", "PERIODO")
        valores = self.tabla.item(seleccion)['values']
        fecha_reg, municipio, sku, tipo, cantidad, periodo = valores
        anio_actual = str(datetime.now().year)

        confirmar = messagebox.askyesno("Anular Ajuste", 
            f"¿Desea eliminar este registro de {tipo}?\n\n"
            f"Producto: {sku}\n"
            f"Cantidad: {cantidad}\n"
            f"Municipio: {municipio}\n\n"
            "Se recalcularán los saldos automáticamente.")

        if confirmar:
            try:
                conn = sqlite3.connect(self.db.db_name)
                cursor = conn.cursor()

                if tipo == "REGRESO":
                    # Si anulamos un REGRESO:
                    # 1. Quitamos del stock del almacén lo que "había vuelto".
                    # 2. Restamos de las entradas por devolución.
                    # 3. Se lo volvemos a "deber" al municipio (sumamos a salidas_municipio).
                    cursor.execute("""UPDATE medicamentos SET 
                                      stock_actual = stock_actual - ?, 
                                      entradas_devolucion = entradas_devolucion - ?,
                                      salidas_municipio = salidas_municipio + ? 
                                      WHERE sku = ?""", (cantidad, cantidad, cantidad, sku))
                else: 
                    # Si anulamos una MERMA:
                    # 1. Restamos de la cuenta de mermas totales.
                    # 2. Se lo volvemos a "deber" al municipio (sumamos a salidas_municipio).
                    cursor.execute("""UPDATE medicamentos SET 
                                      salidas_merma = salidas_merma - ?, 
                                      salidas_municipio = salidas_municipio + ? 
                                      WHERE sku = ?""", (cantidad, cantidad, sku))

                # Eliminar el registro del historial (basado en los criterios exactos)
                cursor.execute("""DELETE FROM historial_retornos 
                                  WHERE fecha = ? AND municipio = ? AND sku = ? 
                                  AND tipo_movimiento = ? AND periodo = ?""", 
                               (fecha_reg, municipio, sku, tipo, periodo))

                conn.commit()
                conn.close()

                winsound.Beep(1000, 250)
                messagebox.showinfo("Éxito", "El ajuste ha sido anulado y los saldos restaurados.")
                self.listar_historial() # Refrescar tabla

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo revertir: {e}")
    def reset_y_buscar(self, e=None): self.pagina_actual = 0; self.listar_historial()
    def pagina_siguiente(self): self.pagina_actual += 1; self.listar_historial()
    def pagina_anterior(self): self.pagina_actual -= 1; self.listar_historial()

    def reset_buffer(self):
        self.sku_en_proceso = None
        self.nombre_en_proceso = ""
        self.conteo_actual = 0
        self.lbl_status.config(text="Esperando escaneo...", fg="gray")
        self.btn_registrar.config(state="disabled")
        self.btn_cancelar.config(state="disabled")
        self.combo_municipio.config(state="readonly")
        self.combo_periodo.config(state="readonly")
        self.btn_modo_regreso.config(state="normal")
        self.btn_modo_merma.config(state="normal")
        self.limpiar()

    def limpiar(self):
        self.ent_sku.delete(0, tk.END)
        self.ent_cant.delete(0, tk.END)
        self.ent_cant.insert(0, "1") 
        self.ent_sku.focus() 

    def regresar(self):
        self.root.destroy()
        self.main_window.deiconify()