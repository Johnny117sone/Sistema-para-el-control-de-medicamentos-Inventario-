import tkinter as tk
from ui.style import *
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime
from ui.municipios import VentanaMunicipios 
from data.inventario_db import InventarioDB
import winsound

class VentanaDestino:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.db = InventarioDB() 
        self.offset = 0  
        self.limite = 50
        
        # --- VARIABLES DE CONTROL (BUFFER) ---
        self.sku_en_proceso = None
        self.nombre_en_proceso = ""
        self.conteo_actual = 0
        
        self.root.title("DESPACHO Y DESGLOSE DE SALIDAS - PLANACE")
        center_window(self.root, *MODULE_WINDOW_SIZE)
        self.root.configure(bg="#fdfefe")
        self.root.protocol("WM_DELETE_WINDOW", self.regresar)

        # --- 1. BARRA SUPERIOR ---
        header = tk.Frame(root, bg="#d35400", pady=10)
        header.pack(fill="x")
        tk.Button(header, text="⬅ MENÚ", command=self.regresar, bg="#a04000", fg="white", font=FONT_LABEL_BOLD).pack(side="left", padx=20)
        tk.Label(header, text="SISTEMA DE DESPACHO POR BRIGADAS", bg="#d35400", fg="white", font=FONT_HEADER).pack(side="left", expand=True)
        tk.Button(header, text="🏙️ MUNICIPIOS", command=self.abrir_gestion_municipios, bg="#e67e22", fg="white", font=FONT_LABEL_BOLD).pack(side="right", padx=20)


        # --- 2. RECUADRO DE OPERACIÓN (ACTUALIZADO CON CANTIDAD) ---
        frame_registro = tk.LabelFrame(root, text=" REGISTRO DE SALIDA CONTROLADA (BUFFER) ", font=FONT_BUTTON, padx=15, pady=15, fg="#d35400")
        frame_registro.pack(fill="x", padx=20, pady=10)

        # Fila 0: Municipio y Periodo
        tk.Label(frame_registro, text="MUNICIPIO DESTINO:").grid(row=0, column=0, sticky="w")
        self.combo_destino = ttk.Combobox(frame_registro, state="readonly", width=30, font=FONT_LABEL)
        self.combo_destino.grid(row=0, column=1, padx=5)
        self.actualizar_combobox_municipios()

        tk.Label(frame_registro, text="PERIODO:").grid(row=0, column=2, sticky="w", padx=10)
        self.combo_periodo_reg = ttk.Combobox(frame_registro, values=("PRIMAVERA", "VERANO", "OTOÑO"), state="readonly", width=12)
        self.combo_periodo_reg.set("PRIMAVERA")
        self.combo_periodo_reg.grid(row=0, column=3, padx=5)

        # Fila 1: Cantidad y SKU (NUEVO ORDEN)
        tk.Label(frame_registro, text="CANT:", font=FONT_BUTTON).grid(row=1, column=0, sticky="w", pady=(15,0))
        self.ent_cant = ttk.Entry(frame_registro, font=FONT_TITLE_REGULAR, width=7)
        self.ent_cant.insert(0, "1")
        self.ent_cant.grid(row=1, column=1, sticky="w", padx=5, pady=(15,0))

        tk.Label(frame_registro, text="SKU / CÓDIGO:", font=FONT_BUTTON).grid(row=1, column=1, sticky="e", pady=(15,0))
        self.ent_scan = ttk.Entry(frame_registro, font=FONT_TITLE_REGULAR, width=18)
        self.ent_scan.grid(row=1, column=2, padx=10, pady=(15,0))
        self.ent_scan.bind("<Return>", self.gestionar_buffer_salida)

        # Monitor y Botones
        self.lbl_status_buffer = tk.Label(frame_registro, text="ESPERANDO ESCANEO...", font=FONT_BUTTON_LARGE, 
                                         fg="#7f8c8d", bg="#f2f3f4", width=30, relief="sunken", pady=8)
        self.lbl_status_buffer.grid(row=1, column=3, padx=10, pady=(15,0))

        self.btn_registrar = tk.Button(frame_registro, text="✅ REGISTRAR", command=self.confirmar_despacho_final, 
                                      bg="#27ae60", fg="white", font=FONT_BUTTON, state="disabled", relief="raised", bd=3)
        self.btn_registrar.grid(row=1, column=4, padx=5, pady=(15,0))

        # ... (dentro del __init__, debajo de self.btn_cancelar)
        self.btn_cancelar = tk.Button(frame_registro, text="❌", command=self.reset_buffer, 
                                      bg="#c0392b", fg="white", font=FONT_BUTTON, state="disabled", relief="raised", bd=3)
        self.btn_cancelar.grid(row=1, column=5, padx=5, pady=(15,0))

        # --- BOTÓN DE RESTABLECER (CORREGIDO Y UBICADO EN LA PARTE SUPERIOR) ---
        self.btn_revertir = tk.Button(frame_registro, text="🔄 REVERTIR TABLA", 
                                      command=self.revertir_salida_error, 
                                      bg="#5d6d7e", fg="white", font=FONT_BUTTON, relief="raised", bd=3)
        self.btn_revertir.grid(row=1, column=6, padx=15, pady=(15,0))
        # -----------------------------------------------------------------------
        # --- 3. RECUADRO DE TABLA Y FILTROS ---
        frame_consulta = tk.LabelFrame(root, text=" DESGLOSE DETALLADO DE ENVÍOS ", font=FONT_BUTTON, padx=15, pady=10)
        frame_consulta.pack(fill="both", expand=True, padx=20, pady=10)

        # Filtros de búsqueda en tabla
        filtros_frame = tk.Frame(frame_consulta)
        filtros_frame.pack(fill="x", pady=5)

        tk.Label(filtros_frame, text="Periodo:").pack(side="left", padx=2)
        self.f_periodo = ttk.Combobox(filtros_frame, values=("TODOS", "PRIMAVERA", "VERANO", "OTOÑO"), state="readonly", width=12)
        self.f_periodo.set("TODOS")
        self.f_periodo.pack(side="left", padx=5)
        self.f_periodo.bind("<<ComboboxSelected>>", lambda e: self.reset_y_cargar())

        tk.Label(filtros_frame, text="Año:").pack(side="left", padx=2)
        self.f_anio = ttk.Combobox(filtros_frame, values=["TODOS"] + [str(a) for a in range(2024, 2036)], state="readonly", width=8)
        self.f_anio.set(str(datetime.now().year))
        self.f_anio.pack(side="left", padx=5)
        self.f_anio.bind("<<ComboboxSelected>>", lambda e: self.reset_y_cargar())

        # Tabla Treeview
        columnas = ("MUNICIPIO", "SKU", "MEDICAMENTO", "PERIODO", "AÑO", "CANTIDAD")
        self.tabla = ttk.Treeview(frame_consulta, columns=columnas, show="headings")
        for col in columnas:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, anchor="center")
        self.tabla.column("MEDICAMENTO", width=350, anchor="w") 
        self.tabla.column("MUNICIPIO", width=200, anchor="w")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.tag_configure('inactivo', foreground='#c0392b')

        pag_frame = tk.Frame(frame_consulta)
        pag_frame.pack(fill="x", pady=10)
        
        
        
        # Paginación
        pag_frame = tk.Frame(frame_consulta)
        pag_frame.pack(fill="x", pady=10)
        self.btn_ant = tk.Button(pag_frame, text="◀ ANTERIORES", command=self.pag_anterior, state="disabled", width=15)
        self.btn_ant.pack(side="left", padx=20)
        self.lbl_pag = tk.Label(pag_frame, text="Mostrando desglose de envíos", font=FONT_SMALL_ITALIC)
        self.lbl_pag.pack(side="left", expand=True)
        self.btn_sig = tk.Button(pag_frame, text="SIGUIENTES ▶", command=self.pag_siguiente, width=15)
        self.btn_sig.pack(side="right", padx=20)

        self.cargar_totales_consolidados()

    # --- LÓGICA DE GESTIÓN (BUFFER) ---

    def gestionar_buffer_salida(self, event=None):
        destino = self.combo_destino.get()
        sku = self.ent_scan.get().strip().upper()

        if destino.startswith("---") or not destino:
            messagebox.showwarning("Atención", "Seleccione primero el municipio destino.")
            self.ent_scan.delete(0, tk.END)
            return

        if not sku: return

        # Bloquear municipio para evitar cambios durante el conteo
        self.combo_destino.config(state="disabled")

        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, stock_actual, estatus FROM medicamentos WHERE sku = ?", (sku,))
        res = cursor.fetchone()
        conn.close()

        if res:
            nombre, stock, estatus = res
            if estatus == 'INACTIVO':
                messagebox.showerror("Bloqueado", "Este producto está dado de baja.")
                self.ent_scan.delete(0, tk.END)
                return
            
            # Si ya hay un SKU diferente en el buffer
            if self.sku_en_proceso and self.sku_en_proceso != sku:
                messagebox.showwarning("Pendiente", f"Termine el registro de '{self.nombre_en_proceso}' antes de cambiar de SKU.")
                self.ent_scan.delete(0, tk.END)
                return

            # Validar stock disponible contra el buffer
            if (self.conteo_actual + 1) > stock:
                messagebox.showerror("Sin Stock", f"Stock insuficiente en Almacén.\nDisponible: {stock} unidades.")
                self.ent_scan.delete(0, tk.END)
                return

            if not self.sku_en_proceso:
                self.sku_en_proceso = sku
                self.nombre_en_proceso = nombre
                self.btn_registrar.config(state="normal")
                self.btn_cancelar.config(state="normal")

            self.conteo_actual += 1
            self.lbl_status_buffer.config(text=f"{self.conteo_actual} pzs de {self.nombre_en_proceso}", fg="#d35400", bg="#fef5e7")
            self.ent_scan.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "SKU no encontrado en el catálogo.")
            self.ent_scan.delete(0, tk.END)
    # --- LÓGICA DE GESTIÓN (BUFFER CORREGIDA) ---

    def gestionar_buffer_salida(self, event=None):
        destino = self.combo_destino.get()
        sku = self.ent_scan.get().strip().upper()

        # 1. Validar Destino
        if destino.startswith("---") or not destino:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            messagebox.showwarning("Atención", "Seleccione primero el municipio destino.")
            self.ent_scan.delete(0, tk.END)
            return

        if not sku: return

        # 2. Obtener cantidad del campo editable
        try:
            unidades_a_sumar = int(self.ent_cant.get().strip())
            if unidades_a_sumar <= 0: unidades_a_sumar = 1
        except:
            unidades_a_sumar = 1

        # Bloquear municipio para evitar errores de integridad
        self.combo_destino.config(state="disabled")

        conn = sqlite3.connect(self.db.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, stock_actual, estatus FROM medicamentos WHERE sku = ?", (sku,))
        res = cursor.fetchone()
        conn.close()

        if res:
            nombre, stock, estatus = res
            
            # 3. Validar Estatus
            if estatus == 'INACTIVO':
                winsound.MessageBeep(winsound.MB_ICONHAND)
                messagebox.showerror("Bloqueado", "Este producto está dado de baja.")
                self.ent_scan.delete(0, tk.END)
                return
            
            # 4. Validar si es el mismo SKU en proceso
            if self.sku_en_proceso and self.sku_en_proceso != sku:
                winsound.MessageBeep(winsound.MB_ICONHAND)
                messagebox.showwarning("Pendiente", f"Termine el registro de '{self.nombre_en_proceso}' antes de cambiar de SKU.")
                self.ent_scan.delete(0, tk.END)
                return

            # 5. VALIDACIÓN DE STOCK (CORREGIDA)
            # Comparamos: (Lo que ya hay en buffer + lo que se quiere sumar) contra el Stock Real
            total_intento = self.conteo_actual + unidades_a_sumar
            
            if total_intento > stock:
                winsound.MessageBeep(winsound.MB_ICONHAND) # Sonido de Error
                messagebox.showerror("Sin Stock", 
                                     f"No hay suficiente inventario para esta salida.\n\n"
                                     f"Stock en Almacén: {stock}\n"
                                     f"Ya en Buffer: {self.conteo_actual}\n"
                                     f"Intento de suma: {unidades_a_sumar}\n"
                                     f"Faltante: {total_intento - stock}")
                self.ent_scan.delete(0, tk.END)
                return # Salimos sin marcar

            # 6. ÉXITO: REGISTRAR EN BUFFER
            if not self.sku_en_proceso:
                self.sku_en_proceso = sku
                self.nombre_en_proceso = nombre
                self.btn_registrar.config(state="normal")
                self.btn_cancelar.config(state="normal")

            self.conteo_actual += unidades_a_sumar
            
            # SONIDO DE ESCANEO EXITOSO
            winsound.Beep(2500, 150)

            self.lbl_status_buffer.config(
                text=f"{self.conteo_actual} pzs de {self.nombre_en_proceso}", 
                fg="#d35400", bg="#fef5e7"
            )
            self.ent_scan.delete(0, tk.END)
            self.ent_scan.focus()
            
        else:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            messagebox.showerror("Error", "SKU no encontrado en el catálogo.")
            self.ent_scan.delete(0, tk.END)
    
    def confirmar_despacho_final(self):
        # 1. VALIDACIÓN DE SEGURIDAD (Evita procesar si el buffer está vacío)
        if not self.sku_en_proceso or self.conteo_actual <= 0:
            winsound.MessageBeep(winsound.MB_ICONHAND) # Sonido de advertencia
            return

        destino = self.combo_destino.get()
        periodo = self.combo_periodo_reg.get()

        # 2. CONFIRMACIÓN VISUAL AL USUARIO
        confirmar = messagebox.askyesno("Confirmar Despacho", 
                                        f"¿Desea registrar la salida de {self.conteo_actual} pzs de:\n"
                                        f"'{self.nombre_en_proceso}'\n"
                                        f"Con destino a: {destino}?")
        if not confirmar: 
            return

        try:
            # 3. CONEXIÓN A BASE DE DATOS
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            
            # 4. ACTUALIZAR STOCK MAESTRO (Resta del inventario y suma a salidas de municipio)
            cursor.execute("""
                UPDATE medicamentos 
                SET stock_actual = stock_actual - ?, 
                    salidas_municipio = salidas_municipio + ? 
                WHERE sku = ?
            """, (self.conteo_actual, self.conteo_actual, self.sku_en_proceso))
            
            # 5. REGISTRAR EN HISTORIAL (Lógica de consolidación ON CONFLICT)
            ahora = datetime.now()
            fecha_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
            anio_str = str(ahora.year)

            cursor.execute("""
                INSERT INTO historial_retornos (municipio, sku, tipo_movimiento, cantidad, fecha, periodo, anio) 
                VALUES (?, ?, 'SALIDA MUNICIPIO', ?, ?, ?, ?)
                ON CONFLICT(municipio, sku, periodo, anio, tipo_movimiento) 
                DO UPDATE SET
                    cantidad = cantidad + excluded.cantidad,
                    fecha = excluded.fecha
            """, (destino, self.sku_en_proceso, self.conteo_actual, fecha_str, periodo, anio_str))

            # 6. GUARDAR CAMBIOS Y CERRAR
            conn.commit()
            conn.close()

            # 7. BIT DE ÉXITO (Doble tono ascendente)
            winsound.Beep(1500, 100)
            winsound.Beep(2000, 150)

            # 8. FINALIZAR OPERACIÓN Y LIMPIAR INTERFAZ
            messagebox.showinfo("Éxito", "Despacho registrado y consolidado correctamente.")
            self.reset_buffer()
            self.cargar_totales_consolidados()

        except Exception as e:
            # En caso de error, emitir sonido de alerta crítica
            winsound.MessageBeep(winsound.MB_ICONERROR)
            messagebox.showerror("Error de Base de Datos", f"No se pudo completar el despacho:\n{str(e)}")
    
    def reset_buffer(self):
        self.sku_en_proceso = None
        self.nombre_en_proceso = ""
        self.conteo_actual = 0
        self.lbl_status_buffer.config(text="ESPERANDO ESCANEO...", fg="#7f8c8d", bg="#f2f3f4")
        self.btn_registrar.config(state="disabled")
        self.btn_cancelar.config(state="disabled")
        self.combo_destino.config(state="readonly")
        # Resetear cantidad a 1
        self.ent_cant.delete(0, tk.END)
        self.ent_cant.insert(0, "1")
        self.ent_scan.delete(0, tk.END)
        self.ent_scan.focus()

    # --- MÉTODOS DE TABLA Y NAVEGACIÓN ---

    def reset_y_cargar(self):
        self.offset = 0
        self.cargar_totales_consolidados()

    def cargar_totales_consolidados(self):
        for item in self.tabla.get_children(): self.tabla.delete(item)
        per, anio = self.f_periodo.get(), self.f_anio.get()
        
        query = """
            SELECT h.municipio, h.sku, m.nombre || ' ' || m.gramaje, h.periodo, h.anio, h.cantidad, m.estatus
            FROM historial_retornos h
            LEFT JOIN medicamentos m ON h.sku = m.sku
            WHERE h.tipo_movimiento = 'SALIDA MUNICIPIO' AND h.municipio != 'ALMACÉN CENTRAL'
        """
        params = []
        if per != "TODOS":
            query += " AND h.periodo = ?"; params.append(per)
        if anio != "TODOS":
            query += " AND h.anio = ?"; params.append(anio)

        query += f" ORDER BY h.fecha DESC LIMIT {self.limite} OFFSET {self.offset}"

        try:
            conn = sqlite3.connect(self.db.db_name)
            cursor = conn.cursor()
            cursor.execute(query, params)
            filas = cursor.fetchall()
            for f in filas:
                mun, sku, med, p, a, cant, est = f
                tag = ('inactivo',) if est == 'INACTIVO' else ()
                self.tabla.insert("", "end", values=(mun, sku, med, p, a, cant), tags=tag)
            
            self.btn_ant["state"] = "normal" if self.offset > 0 else "disabled"
            self.btn_sig["state"] = "normal" if len(filas) == self.limite else "disabled"
            conn.close()
        except Exception as e: print(f"Error: {e}")

    def revertir_salida_error(self):
        """Revierte una salida mal capturada devolviendo el stock al almacén"""
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione el registro que desea corregir en la tabla.")
            return

        # Obtener datos de la fila seleccionada
        valores = self.tabla.item(seleccion)['values']
        municipio, sku, nombre_med, periodo, anio, cantidad = valores

        confirmar = messagebox.askyesno("Confirmar Corrección", 
            f"¿Desea anular esta salida?\n\n"
            f"Medicamento: {nombre_med}\n"
            f"Cantidad a devolver: {cantidad}\n"
            f"Municipio: {municipio}\n\n"
            "Esto regresará las piezas al almacén central.")

        if confirmar:
            try:
                conn = sqlite3.connect(self.db.db_name)
                cursor = conn.cursor()

                # 1. Regresar el stock al medicamento
                cursor.execute("""
                    UPDATE medicamentos 
                    SET stock_actual = stock_actual + ?, 
                        salidas_municipio = salidas_municipio - ? 
                    WHERE sku = ?
                """, (cantidad, cantidad, sku))

                # 2. Borrar el registro del historial
                cursor.execute("""
                    DELETE FROM historial_retornos 
                    WHERE municipio = ? AND sku = ? AND periodo = ? AND anio = ? AND tipo_movimiento = 'SALIDA MUNICIPIO'
                """, (municipio, sku, periodo, anio))

                conn.commit()
                conn.close()

                winsound.Beep(1000, 200)
                messagebox.showinfo("Corregido", "El inventario ha sido restaurado exitosamente.")
                self.cargar_totales_consolidados() # Refrescar tabla

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo revertir el registro: {e}")
    
    def pag_siguiente(self): self.offset += self.limite; self.cargar_totales_consolidados()
    def pag_anterior(self): self.offset -= self.limite; self.cargar_totales_consolidados()

    def actualizar_combobox_municipios(self):
        self.combo_destino['values'] = self.db.obtener_municipios()
        self.combo_destino.set("--- Seleccione el destino ---")

    def abrir_gestion_municipios(self):
        self.root.withdraw() 
        nueva_ventana = tk.Toplevel() 
        VentanaMunicipios(nueva_ventana, self)


    def regresar(self):
        self.root.destroy()
        self.main_window.deiconify()