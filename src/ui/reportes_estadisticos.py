import tkinter as tk
from ui.style import *
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime

# Librerías para PDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Librerías para Excel
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# Asumimos que existe el archivo database.py con la clase InventarioDB
from data.inventario_db import InventarioDB
from openpyxl.drawing.image import Image as OpenpyxlImage
import textwrap

class VentanaReportes:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.db = InventarioDB()
        self.canvas_grafica = None
        
        self.root.title("SISTEMA DE INTELIGENCIA DE INVENTARIOS - PLANACE")
        center_window(self.root, *MODULE_WINDOW_SIZE)
        self.root.configure(bg="#f4f7f6")
        self.root.protocol("WM_DELETE_WINDOW", self.regresar)

        # --- ENCABEZADO ---
        header = tk.Frame(root, bg="#16a085", pady=15)
        header.pack(fill="x")
        
        tk.Button(header, text="⬅ VOLVER", command=self.regresar, bg="#0e6655", fg="white", font=FONT_LABEL_BOLD).pack(side="left", padx=20)
        tk.Label(header, text="CENTRO DE REPORTES Y ANALÍTICA", bg="#16a085", fg="white", font=FONT_TITLE).pack(side="left", padx=20)

        # --- 1. FILTROS ---
        frame_filtros = tk.LabelFrame(root, text=" 1. FILTROS PARA EXPORTACIÓN ", bg="#f4f7f6", pady=10, font=FONT_LABEL_BOLD)
        frame_filtros.pack(fill="x", padx=20, pady=(10, 0))

        tk.Label(frame_filtros, text="AÑO:", bg="#f4f7f6", font=FONT_LABEL_BOLD).pack(side="left", padx=(20, 5))
        self.combo_anio = ttk.Combobox(frame_filtros, values=["TODOS"] + [str(a) for a in range(2024, 2035)], state="readonly", width=10)
        self.combo_anio.set("TODOS")
        self.combo_anio.pack(side="left", padx=5)

        tk.Label(frame_filtros, text="PERIODO:", bg="#f4f7f6", font=FONT_LABEL_BOLD).pack(side="left", padx=(30, 5))
        self.combo_periodo = ttk.Combobox(frame_filtros, values=("TODOS", "PRIMAVERA", "VERANO", "OTOÑO"), state="readonly", width=15)
        self.combo_periodo.set("TODOS")
        self.combo_periodo.pack(side="left", padx=5)

        # --- 2. BOTONES DE REPORTES ---
        btn_container = tk.LabelFrame(root, text=" 2. SELECCIONE EL REPORTE A GENERAR ", bg="#f4f7f6", pady=15, font=FONT_LABEL_BOLD)
        btn_container.pack(fill="x", padx=20, pady=10)

        # Fila 0: Balances
        tk.Label(btn_container, text="BALANCES ING/SAL:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=0, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊 EXCEL", command=self.reporte_balances_excel, bg="#27ae60", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF", command=self.reporte_balances_pdf, bg="#c0392b", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=0, column=2, padx=5, pady=5)

        # Fila 1: Mermas
        tk.Label(btn_container, text="REPORTE DE MERMAS:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=1, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊 EXCEL", command=self.exportar_excel_mermas, bg="#27ae60", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF", command=self.exportar_pdf_mermas, bg="#c0392b", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=1, column=2, padx=5, pady=5)

        # Fila 2: Compras
        tk.Label(btn_container, text="INGRESOS POR COMPRAS:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=2, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="🛒 EXCEL", command=self.reporte_compras_excel, bg="#27ae60", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF", command=self.reporte_compras_pdf, bg="#c0392b", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=2, column=2, padx=5, pady=5)

        # Fila 3: Stock Crítico 
        tk.Label(btn_container, text="ALERTA STOCK CRÍTICO:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=3, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊EXCEL", command=self.reporte_stock_bajo_excel, bg="#27ae60", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF", command=self.reporte_stock_bajo_pdf, bg="#c0392b", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=3, column=2, padx=5, pady=5)
        
        # Fila 4: Análisis de Demanda (Movido para evitar solapamiento)
        tk.Label(btn_container, text="ANÁLISIS DE DEMANDA:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=4, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊 TOP 10", command=self.reporte_demanda_total_excel, bg="#27ae60", fg="white", font=FONT_SMALL_BOLD, width=15).grid(row=4, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📊 VER TOP 10", command=self.graficar_top_10, bg="#2980b9", fg="white", font=FONT_SMALL_BOLD, width=15).grid(row=4, column=2, padx=5, pady=5)

        # --- FILA 5: REPORTES CON GRÁFICA (RESTAURADA) ---
        tk.Label(btn_container, text="REPORTES CON GRÁFICA:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=5, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊 EXCEL + GRÁFICA", command=self.exportar_excel_con_grafica, bg="#27ae60", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=5, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF + GRÁFICA", command=self.exportar_pdf_con_grafica, bg="#c0392b", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=5, column=2, padx=5, pady=5)
        # NUEVO BOTÓN: Regresar a la gráfica histórica
        tk.Button(btn_container, text="📈 VER CONSUMO HISTÓRICO", command=self.graficar_estacionalidad, bg="#8e44ad", fg="white", font=FONT_SMALL_BOLD, width=25).grid(row=4, column=3, padx=5, pady=5)
        # --- FILA 6: CATÁLOGO MAESTRO ---
        tk.Label(btn_container, text="CATÁLOGO MAESTRO:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=6, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊 EXCEL ", command=self.reporte_maestro_excel, bg="#27ae60", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=6, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF", command=self.reporte_maestro_pdf, bg="#c0392b", fg="white", font=FONT_LABEL_BOLD, width=15).grid(row=6, column=2, padx=5, pady=5)

        # --- NUEVA FILA 7: INVENTARIO OPERATIVO (GENERAL) ---
        tk.Label(btn_container, text="CATÁLOGO GENERAL:", bg="#f4f7f6", font=FONT_LABEL_BOLD).grid(row=7, column=0, sticky="e", padx=10, pady=5)
        tk.Button(btn_container, text="📊 EXCEL ", command=self.reporte_operativo_excel, bg="#27ae60", fg="white", font=FONT_SMALL_BOLD, width=18).grid(row=7, column=1, padx=5, pady=5)
        tk.Button(btn_container, text="📄 PDF ", command=self.reporte_operativo_pdf, bg="#c0392b", fg="white", font=FONT_SMALL_BOLD, width=18).grid(row=7, column=2, padx=5, pady=5)
        
              # --- 3. ÁREA DE GRÁFICA ---
        self.chart_frame = tk.Frame(root, bg="white", bd=1, relief="solid")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.graficar_estacionalidad()
    # --- CONSULTAS A BASE DE DATOS ---

    def obtener_datos_balances(self):
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
        conn = sqlite3.connect(self.db.db_name)
        
        query = """
            SELECT municipio as MUNICIPIO, periodo as PERIODO, anio as AÑO,
            SUM(CASE WHEN tipo_movimiento = 'SALIDA MUNICIPIO' THEN cantidad ELSE 0 END) as ENVIADO,
            SUM(CASE WHEN tipo_movimiento = 'REGRESO' THEN cantidad ELSE 0 END) as DEVUELTO,
            SUM(CASE WHEN tipo_movimiento = 'MERMA' THEN cantidad ELSE 0 END) as MERMA,
            (SUM(CASE WHEN tipo_movimiento = 'SALIDA MUNICIPIO' THEN cantidad ELSE 0 END) -
             SUM(CASE WHEN tipo_movimiento = 'REGRESO' THEN cantidad ELSE 0 END) -
             SUM(CASE WHEN tipo_movimiento = 'MERMA' THEN cantidad ELSE 0 END)) as CONSUMO_REAL
            FROM historial_retornos
        """
        condiciones = ["tipo_movimiento != 'COMPRA'"]
        params = []
        if anio_sel != "TODOS":
            condiciones.append("anio = ?")
            params.append(anio_sel)
        if per_sel != "TODOS":
            condiciones.append("periodo = ?")
            params.append(per_sel)
            
        query += " WHERE " + " AND ".join(condiciones)
        query += " GROUP BY municipio, periodo, anio"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df, anio_sel, per_sel

    def obtener_datos_mermas(self):
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
        conn = sqlite3.connect(self.db.db_name)
        
        # --- SQL ACTUALIZADO ---
        query = """
            SELECT h.municipio as MUNICIPIO, 
                   m.nombre || ' ' || m.gramaje || ' - ' || m.presentacion as MEDICAMENTO,
                   SUM(h.cantidad) as CANTIDAD, h.periodo as PERIODO, h.anio as AÑO
            FROM historial_retornos h
            LEFT JOIN medicamentos m ON h.sku = m.sku
            WHERE h.tipo_movimiento = 'MERMA'
        """
        
        condiciones = []
        params = []
        if anio_sel != "TODOS":
            condiciones.append("h.anio = ?")
            params.append(anio_sel)
        if per_sel != "TODOS":
            condiciones.append("h.periodo = ?")
            params.append(per_sel)
            
        if condiciones: query += " AND " + " AND ".join(condiciones)
        query += " GROUP BY h.municipio, h.sku, h.periodo, h.anio"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df, anio_sel, per_sel
    # --- MÉTODOS DE EXPORTACIÓN EXCEL ---

    def reporte_balances_excel(self):
        df, anio_sel, per_sel = self.obtener_datos_balances()
        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay movimientos para generar el balance.")
            return
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Balance_{fecha_str}.xlsx", filetypes=[("Excel", "*.xlsx")])
        if path: self.formatear_y_guardar_excel(df, path, "REPORTE EJECUTIVO DE BALANCES TERRITORIALES", anio_sel, per_sel)

    def exportar_excel_mermas(self):
        df, anio_sel, per_sel = self.obtener_datos_mermas()
        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay mermas registradas con esos filtros.")
            return
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Mermas_{fecha_str}.xlsx", filetypes=[("Excel", "*.xlsx")])
        if path: self.formatear_y_guardar_excel(df, path, "REPORTE DETALLADO DE MERMAS TERRITORIALES", anio_sel, per_sel)

    
    def exportar_pdf_mermas(self):
        # 1. Ajuste en la obtención de datos para esta función
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
        conn = sqlite3.connect(self.db.db_name)
        
        # --- CAMBIO SQL AQUÍ ---
        query = """
            SELECT h.municipio as MUNICIPIO, 
                   m.nombre || ' ' || m.gramaje || ' - ' || m.presentacion as MEDICAMENTO,
                   SUM(h.cantidad) as CANTIDAD, h.periodo as PERIODO, h.anio as AÑO
            FROM historial_retornos h
            LEFT JOIN medicamentos m ON h.sku = m.sku
            WHERE h.tipo_movimiento = 'MERMA'
        """
        condiciones = []
        params = []
        if anio_sel != "TODOS":
            condiciones.append("h.anio = ?")
            params.append(anio_sel)
        if per_sel != "TODOS":
            condiciones.append("h.periodo = ?")
            params.append(per_sel)
            
        if condiciones: query += " AND " + " AND ".join(condiciones)
        query += " GROUP BY h.municipio, h.sku, h.periodo, h.anio"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        # -----------------------

        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay mermas registradas.")
            return
            
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Mermas_{fecha_str}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path: return

        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter

        def draw_header_mermas(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 14)
            canvas_obj.drawString(50, height - 50, "REPORTE DETALLADO DE MERMAS")
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.drawString(50, height - 65, f"Filtros: {anio_sel} / {per_sel}")
            canvas_obj.line(50, height - 75, width - 50, height - 75)
            y_table = height - 95
            headers = ["MUNICIPIO", "MEDICAMENTO", "PERIODO", "CANT"]
            x_pos = [50, 190, 460, 520] 
            for h, x in zip(headers, x_pos): canvas_obj.drawString(x, y_table, h)
            return y_table - 20

        y = draw_header_mermas(c)
        c.setFont("Helvetica", 8)
        
        for _, row in df.iterrows():
            # --- TEXTWRAP ---
            lineas_mun = textwrap.wrap(str(row['MUNICIPIO']), width=26)
            lineas_med = textwrap.wrap(str(row['MEDICAMENTO']), width=44)
            
            c.drawString(460, y, str(row['PERIODO']))
            c.drawString(520, y, str(row['CANTIDAD']))
            
            y_mun = y
            for linea in lineas_mun:
                c.drawString(50, y_mun, linea)
                y_mun -= 10
                
            y_med = y
            for linea in lineas_med:
                c.drawString(190, y_med, linea)
                y_med -= 10
                
            y = min(y_mun, y_med) - 4
            
            if y < 50:
                c.showPage()
                y = draw_header_mermas(c)
                c.setFont("Helvetica", 8)
        
        c.save()
        os.startfile(path)
    
    def reporte_compras_excel(self):
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
        conn = sqlite3.connect(self.db.db_name)
        
        # --- SQL ACTUALIZADO ---
        query = """
            SELECT h.sku as SKU, 
                   m.nombre || ' ' || m.gramaje || ' - ' || m.presentacion as MEDICAMENTO,
                   h.cantidad as CAJAS_INGRESADAS, h.periodo as PERIODO, h.anio as AÑO
            FROM historial_retornos h
            LEFT JOIN medicamentos m ON h.sku = m.sku
            WHERE h.tipo_movimiento = 'COMPRA'
        """
        
        condiciones = []
        params = []
        if anio_sel != "TODOS":
            condiciones.append("h.anio = ?")
            params.append(anio_sel)
        if per_sel != "TODOS":
            condiciones.append("h.periodo = ?")
            params.append(per_sel)
        if condiciones: query += " AND " + " AND ".join(condiciones)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay compras registradas.")
            return

        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Compras_{fecha_str}.xlsx", filetypes=[("Excel", "*.xlsx")])
        if path: self.formatear_y_guardar_excel(df, path, "REPORTE DE INGRESOS POR COMPRAS (ALMACÉN CENTRAL)", anio_sel, per_sel)
    # --- MÉTODOS DE EXPORTACIÓN PDF ---

    def reporte_balances_pdf(self):
        df, anio_sel, per_sel = self.obtener_datos_balances()
        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay movimientos para generar el balance.")
            return
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Balance_{fecha_str}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path: return

        c = canvas.Canvas(path, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        def draw_header(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawString(50, height - 50, "REPORTE EJECUTIVO DE BALANCES TERRITORIALES")
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawString(50, height - 70, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Filtros: Año [{anio_sel}] - Periodo [{per_sel}]")
            canvas_obj.line(50, height - 80, width - 50, height - 80)
            # Encabezados de tabla
            canvas_obj.setFont("Helvetica-Bold", 10)
            y_table = height - 100
            headers = ["MUNICIPIO", "PERIODO", "AÑO", "ENVIADO", "DEVUELTO", "MERMA", "CONSUMO"]
            x_pos = [50, 250, 350, 420, 500, 580, 660]
            for h, x in zip(headers, x_pos): canvas_obj.drawString(x, y_table, h)
            return y_table - 20

        y = draw_header(c)
        c.setFont("Helvetica", 9)
        for _, row in df.iterrows():
            if y < 50:
                c.showPage()
                y = draw_header(c)
                c.setFont("Helvetica", 9)
            c.drawString(50, y, str(row['MUNICIPIO'])[:35])
            c.drawString(250, y, str(row['PERIODO']))
            c.drawString(350, y, str(row['AÑO']))
            c.drawString(420, y, str(row['ENVIADO']))
            c.drawString(500, y, str(row['DEVUELTO']))
            c.drawString(580, y, str(row['MERMA']))
            c.drawString(660, y, str(row['CONSUMO_REAL']))
            y -= 15

        c.save()
        os.startfile(path)

    

        def draw_header_mermas(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 14)
            canvas_obj.drawString(50, height - 50, "REPORTE DETALLADO DE MERMAS")
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.drawString(50, height - 65, f"Filtros: {anio_sel} / {per_sel}")
            canvas_obj.line(50, height - 75, width - 50, height - 75)
            y_table = height - 95
            headers = ["MUNICIPIO", "MEDICAMENTO", "PERIODO", "CANT"]
            x_pos = [50, 200, 450, 520]
            for h, x in zip(headers, x_pos): canvas_obj.drawString(x, y_table, h)
            return y_table - 20

        y = draw_header_mermas(c)
        c.setFont("Helvetica", 8)
        for _, row in df.iterrows():
            if y < 50:
                c.showPage()
                y = draw_header_mermas(c)
                c.setFont("Helvetica", 8)
            c.drawString(50, y, str(row['MUNICIPIO'])[:28])
            c.drawString(200, y, str(row['MEDICAMENTO'])[:45])
            c.drawString(450, y, str(row['PERIODO']))
            c.drawString(520, y, str(row['CANTIDAD']))
            y -= 15
        
        c.save()
        os.startfile(path)

    def reporte_compras_pdf(self):
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
        conn = sqlite3.connect(self.db.db_name)
        
        # --- CAMBIO SQL AQUÍ ---
        query = """
            SELECT h.sku as SKU, 
                   m.nombre || ' ' || m.gramaje || ' - ' || m.presentacion as MEDICAMENTO,
                   h.cantidad as CANTIDAD, h.periodo as PERIODO, h.anio as AÑO
            FROM historial_retornos h
            LEFT JOIN medicamentos m ON h.sku = m.sku
            WHERE h.tipo_movimiento = 'COMPRA'
        """
        # -----------------------
        
        condiciones = []
        params = []
        if anio_sel != "TODOS":
            condiciones.append("h.anio = ?")
            params.append(anio_sel)
        if per_sel != "TODOS":
            condiciones.append("h.periodo = ?")
            params.append(per_sel)
        if condiciones: query += " AND " + " AND ".join(condiciones)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay compras registradas.")
            return

        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Compras_{fecha_str}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path: return

        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter
        
        def draw_header_compras(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 14)
            canvas_obj.drawString(50, height - 50, "INGRESOS POR COMPRAS - ALMACÉN CENTRAL")
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.drawString(50, height - 65, f"Generado: {datetime.now().strftime('%d/%m/%Y')}")
            canvas_obj.line(50, height - 75, width - 50, height - 75)
            y_table = height - 95
            headers = ["SKU", "MEDICAMENTO", "CANT", "PERIODO", "AÑO"]
            x_pos = [50, 130, 420, 470, 530]
            for h, x in zip(headers, x_pos): canvas_obj.drawString(x, y_table, h)
            return y_table - 20

        y = draw_header_compras(c)
        c.setFont("Helvetica", 9)
        
        for _, row in df.iterrows():
            # --- TEXTWRAP ---
            lineas_med = textwrap.wrap(str(row['MEDICAMENTO']), width=45)
            
            c.drawString(50, y, str(row['SKU']))
            c.drawString(420, y, str(row['CANTIDAD']))
            c.drawString(470, y, str(row['PERIODO']))
            c.drawString(530, y, str(row['AÑO']))
            
            y_temp = y
            for linea in lineas_med:
                c.drawString(130, y_temp, linea)
                y_temp -= 11
                
            y = y_temp - 4
            
            if y < 50:
                c.showPage()
                y = draw_header_compras(c)
                c.setFont("Helvetica", 9)
        
        c.save()
        os.startfile(path)

    # --- UTILIDADES DE FORMATO ---

    def formatear_y_guardar_excel(self, df, path, titulo, anio_sel, per_sel):
        try:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, startrow=3, sheet_name='Reporte')
                worksheet = writer.sheets['Reporte']
                
                # Título
                worksheet['A1'] = titulo
                worksheet['A1'].font = Font(size=14, bold=True, color="003366")
                worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
                worksheet['A1'].alignment = Alignment(horizontal='center')

                # Subtítulo (Filtros)
                worksheet['A2'] = f"Año: {anio_sel} | Periodo: {per_sel} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                worksheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(df.columns))
                worksheet['A2'].alignment = Alignment(horizontal='center')

                # Estilo de encabezados
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="2980B9", end_color="2980B9", fill_type="solid")
                
                for col_num, col_name in enumerate(df.columns, 1):
                    cell = worksheet.cell(row=4, column=col_num)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center')
                    # Ajuste de ancho automático
                    worksheet.column_dimensions[get_column_letter(col_num)].width = 20

            os.startfile(path)
            messagebox.showinfo("Éxito", "Reporte generado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")

    # --- CONSULTAS ---
    def obtener_datos_stock_critico(self):
        conn = sqlite3.connect(self.db.db_name)
        # --- CAMBIO SQL AQUÍ ---
        query = """
            SELECT sku as SKU, 
                   nombre || ' ' || gramaje || ' - ' || presentacion as MEDICAMENTO, 
                   stock_actual as STOCK_REAL, stock_min as MINIMO_REQUERIDO 
            FROM medicamentos 
            WHERE stock_actual <= stock_min AND (estatus = 'ACTIVO' OR estatus IS NULL)
        """
        # -----------------------
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # --- REPORTES DE STOCK CRÍTICO ---
    def reporte_stock_bajo_excel(self):
        df = self.obtener_datos_stock_critico()
        if df.empty:
            messagebox.showinfo("Inventario OK", "No hay productos bajo el stock mínimo.")
            return
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Stock_Critico_{fecha_str}.xlsx", filetypes=[("Excel", "*.xlsx")])
        if path:
            self.formatear_y_guardar_excel(df, path, "REPORTE DE PRODUCTOS EN NIVEL CRÍTICO", "TODOS", "ACTIVOS")

    def reporte_stock_bajo_pdf(self):
        df = self.obtener_datos_stock_critico()
        if df.empty:
            messagebox.showinfo("Inventario OK", "No hay productos bajo el stock mínimo.")
            return
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Stock_Critico_{fecha_str}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path: return

        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter

        def draw_header_stock(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 14)
            canvas_obj.setFillColorRGB(0.5, 0, 0)
            canvas_obj.drawString(50, height - 50, "ALERTA DE REABASTECIMIENTO - STOCK CRÍTICO")
            canvas_obj.setFillColorRGB(0, 0, 0)
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.drawString(50, height - 65, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            canvas_obj.line(50, height - 75, width - 50, height - 75)
            canvas_obj.setFont("Helvetica-Bold", 10)
            y_tab = height - 95
            canvas_obj.drawString(50, y_tab, "SKU")
            canvas_obj.drawString(130, y_tab, "MEDICAMENTO")
            canvas_obj.drawString(420, y_tab, "S. ACTUAL")
            canvas_obj.drawString(490, y_tab, "S. MÍNIMO")
            return y_tab - 20

        y = draw_header_stock(c)
        c.setFont("Helvetica", 9)
        for _, row in df.iterrows():
            # --- TEXTWRAP ---
            lineas_med = textwrap.wrap(str(row['MEDICAMENTO']), width=50)
            
            c.drawString(50, y, str(row['SKU']))
            c.drawString(420, y, str(row['STOCK_REAL']))
            c.drawString(490, y, str(row['MINIMO_REQUERIDO']))
            
            y_temp = y
            for linea in lineas_med:
                c.drawString(130, y_temp, linea)
                y_temp -= 11
                
            y = y_temp - 4
            
            if y < 50:
                c.showPage()
                y = draw_header_stock(c)
                c.setFont("Helvetica", 9)
        
        c.save()
        os.startfile(path)
    
    def obtener_analisis_demanda_por_municipio(self):
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
        conn = sqlite3.connect(self.db.db_name)
        
        # --- SQL ACTUALIZADO ---
        query = """
            SELECT 
                h.municipio as MUNICIPIO, 
                m.nombre || ' ' || m.gramaje || ' - ' || m.presentacion as MEDICAMENTO,
                SUM(h.cantidad) as TOTAL_USADO,
                h.periodo as PERIODO,
                h.anio as AÑO
            FROM historial_retornos h
            LEFT JOIN medicamentos m ON h.sku = m.sku
            WHERE h.tipo_movimiento = 'SALIDA MUNICIPIO'
        """
        
        condiciones = []
        params = []
        if anio_sel != "TODOS":
            condiciones.append("h.anio = ?")
            params.append(anio_sel)
        if per_sel != "TODOS":
            condiciones.append("h.periodo = ?")
            params.append(per_sel)
            
        if condiciones:
            query += " AND " + " AND ".join(condiciones)
            
        query += " GROUP BY h.municipio, h.sku"
        df_completo = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df_completo.empty:
            return pd.DataFrame()

        df_sorted = df_completo.sort_values(by=['MUNICIPIO', 'TOTAL_USADO'], ascending=[True, False])
        df_top_10_por_municipio = df_sorted.groupby('MUNICIPIO').head(10)
        return df_top_10_por_municipio
    
    def reporte_demanda_total_excel(self):
        df = self.obtener_analisis_demanda_por_municipio()
        
        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay registros para los filtros seleccionados.")
            return
        
        ahora = datetime.now().strftime('%Y%m%d_%H%M')
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"Top10_Municipios_{ahora}.xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not path: return

        try:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, startrow=3, sheet_name='Analisis_Demanda')
                ws = writer.sheets['Analisis_Demanda']
                
                # --- DISEÑO ---
                ws['A1'] = "TOP 10 MEDICAMENTOS MÁS UTILIZADOS POR MUNICIPIO"
                ws['A1'].font = Font(size=16, bold=True, color="16A085")
                ws['A2'] = f"Filtros Aplicados: Año [{self.combo_anio.get()}] | Periodo [{self.combo_periodo.get()}]"
                
                # Estilo de encabezados de tabla
                header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
                for col in range(1, len(df.columns) + 1):
                    cell = ws.cell(row=4, column=col)
                    cell.fill = header_fill
                    cell.font = Font(bold=True, color="FFFFFF")
                    ws.column_dimensions[get_column_letter(col)].width = 25

                # Resaltar cambios de municipio para que sea legible
                municipio_actual = ""
                highlight_fill = PatternFill(start_color="D5F5E3", end_color="D5F5E3", fill_type="solid")
                
                for row in range(5, ws.max_row + 1):
                    val_municipio = ws.cell(row=row, column=1).value
                    if val_municipio != municipio_actual:
                        # Dibujar una línea o resaltar cuando cambia el municipio
                        for col in range(1, len(df.columns) + 1):
                            ws.cell(row=row, column=col).fill = highlight_fill
                        municipio_actual = val_municipio

            os.startfile(path)
            messagebox.showinfo("Éxito", "El reporte por municipio se ha generado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear el Excel: {e}")
    def graficar_top_10(self):
        """Muestra el Top 10 respetando los filtros de Año y Periodo."""
        if self.canvas_grafica:
            self.canvas_grafica.get_tk_widget().destroy()
            
        anio_sel = self.combo_anio.get()
        per_sel = self.combo_periodo.get()
            
        try:
            conn = sqlite3.connect(self.db.db_name)
            
            # --- SQL ACTUALIZADO ---
            query = """
                SELECT m.nombre || ' ' || m.gramaje || ' - ' || m.presentacion as MEDICAMENTO, 
                       SUM(h.cantidad) as TOTAL
                FROM historial_retornos h
                JOIN medicamentos m ON h.sku = m.sku
                WHERE h.tipo_movimiento = 'SALIDA MUNICIPIO'
            """
            
            condiciones = []
            params = []
            if anio_sel != "TODOS":
                condiciones.append("h.anio = ?")
                params.append(anio_sel)
            if per_sel != "TODOS":
                condiciones.append("h.periodo = ?")
                params.append(per_sel)
                
            if condiciones:
                query += " AND " + " AND ".join(condiciones)
            
            query += " GROUP BY h.sku ORDER BY TOTAL DESC LIMIT 10"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            fig, ax = plt.subplots(figsize=(7, 4))
            fig.patch.set_facecolor('#f4f7f6') 

            if not df.empty:
                colores = plt.cm.Paired(range(len(df))) 
                etiquetas_ajustadas = ['\n'.join(textwrap.wrap(str(med), width=35)) for med in df['MEDICAMENTO']]
                ax.barh(etiquetas_ajustadas, df['TOTAL'], color=colores)
                ax.set_title(f"TOP 10 MEDICAMENTOS ({anio_sel} - {per_sel})", fontweight='bold', color='#2c3e50')
                ax.invert_yaxis() 
                ax.set_xlabel("Unidades Despachadas")
                # Reducimos un poco la fuente en el eje Y por si el nombre es muy largo
                plt.yticks(fontsize=7) 
                plt.tight_layout()
            else:
                ax.text(0.5, 0.5, f"Sin datos para:\nAño: {anio_sel}\nPeriodo: {per_sel}", 
                        ha='center', va='center', fontsize=12, color='red')

            self.canvas_grafica = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas_grafica.draw()
            self.canvas_grafica.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al filtrar gráfica: {e}")
    
    def graficar_estacionalidad(self):
        if self.canvas_grafica: self.canvas_grafica.get_tk_widget().destroy()
        try:
            conn = sqlite3.connect(self.db.db_name)
            query = "SELECT periodo, SUM(cantidad) as total FROM historial_retornos WHERE tipo_movimiento = 'SALIDA MUNICIPIO' GROUP BY periodo"
            df = pd.read_sql_query(query, conn)
            conn.close()

            fig, ax = plt.subplots(figsize=(7, 4))
            if not df.empty:
                orden = {'PRIMAVERA': 1, 'VERANO': 2, 'OTOÑO': 3}
                df['n'] = df['periodo'].map(orden)
                df = df.sort_values('n')
                ax.plot(df['periodo'], df['total'], marker='o', color='#8e44ad', linewidth=2)
                ax.fill_between(df['periodo'], df['total'], color='#a29bfe', alpha=0.3)
                ax.set_title("VOLUMEN DE DESPACHO POR TEMPORADA (HISTÓRICO)", fontweight='bold')
            else:
                ax.text(0.5, 0.5, "Sin datos para graficar", ha='center')

            self.canvas_grafica = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas_grafica.draw()
            self.canvas_grafica.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error gráfico: {e}")

    def exportar_pdf_con_grafica(self):
        df = self.obtener_analisis_demanda_por_municipio()
        if df.empty: 
            messagebox.showwarning("Sin Datos", "No hay información para exportar.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                            initialfile=f"Reporte_Visual_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        if not path: return

        try:
            # 1. Guardar imagen temporal en alta resolución para PDF
            temp_pdf_img = "temp_grafica_pdf.png"
            self.canvas_grafica.figure.savefig(temp_pdf_img, dpi=150, bbox_inches='tight')

            c = canvas.Canvas(path, pagesize=letter)
            w, h = letter

            # 2. Título y Estilo
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, h - 50, "SISTEMA PLANACE - ANÁLISIS DE DEMANDA")
            c.line(50, h - 60, w - 50, h - 60)

            # 3. Insertar la Gráfica
            c.drawImage(temp_pdf_img, 50, h - 380, width=500, preserveAspectRatio=True)

            # 4. Tabla de datos debajo de la gráfica
            y = h - 420
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "DETALLE DE SALIDAS POR MUNICIPIO:")
            
            y -= 25
            c.setFont("Helvetica", 9)
            
            for _, row in df.iterrows():
                # --- TEXTWRAP PARA EL REPORTE CON GRÁFICA ---
                texto_base = f"• {row['MUNICIPIO']} - {row['MEDICAMENTO']}: {row['TOTAL_USADO']} unidades"
                lineas_texto = textwrap.wrap(texto_base, width=90) # Ancho casi total de la página
                
                for linea in lineas_texto:
                    if y < 50: # Salto de página automático si se llena
                        c.showPage()
                        y = h - 50
                        c.setFont("Helvetica", 9)
                    
                    c.drawString(60, y, linea)
                    y -= 14
                
                y -= 4 # Espacio extra entre cada producto distinto

            c.save()
            if os.path.exists(temp_pdf_img): os.remove(temp_pdf_img) # Limpiar
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF: {e}")
    def exportar_excel_con_grafica(self):
        df = self.obtener_analisis_demanda_por_municipio()
        if df.empty:
            messagebox.showwarning("Sin Datos", "No hay información para exportar.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".xlsx", 
                                            initialfile=f"Analisis_Grafico_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
        if not path: return

        try:
            # 1. Guardar la gráfica actual como imagen temporal
            temp_img = "temp_grafica_excel.png"
            self.canvas_grafica.figure.savefig(temp_img, dpi=100, bbox_inches='tight')

            # 2. Crear el archivo Excel
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, startrow=22, sheet_name='Analisis Visual')
                ws = writer.sheets['Analisis Visual']
                
                # 3. Insertar la imagen en la celda B2
                img = OpenpyxlImage(temp_img)
                ws.add_image(img, 'B2')
                
                # Formato de título
                ws['A1'] = "REPORTE ESTADÍSTICO DE DEMANDA - PLANACE"
                ws['A1'].font = Font(size=14, bold=True)

            if os.path.exists(temp_img): os.remove(temp_img) # Limpiar
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el Excel: {e}")
    
    def obtener_datos_maestro(self):
        """Extrae el catálogo completo de medicamentos (sin filtros de fecha)"""
        conn = sqlite3.connect(self.db.db_name)
        query = """
            SELECT sku as SKU, nombre as MEDICAMENTO, gramaje as GRAMAJE, 
                   presentacion as PRESENTACION, laboratorio as LABORATORIO, 
                   grupo as GRUPO, tipo as TIPO, stock_actual as STOCK_REAL, estatus as ESTATUS
            FROM medicamentos
            ORDER BY nombre ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    def reporte_maestro_excel(self):
        df = self.obtener_datos_maestro()
        if df.empty:
            messagebox.showwarning("Sin Datos", "El catálogo maestro está vacío.")
            return
            
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Catalogo_Maestro_{fecha_str}.xlsx", filetypes=[("Excel", "*.xlsx")])
        
        if path: 
            # Mandamos "N/A" a los filtros porque este reporte es general
            self.formatear_y_guardar_excel(df, path, "CATÁLOGO MAESTRO DE INVENTARIO - PLANACE", "N/A", "N/A")
    
    def reporte_maestro_pdf(self):
        df = self.obtener_datos_maestro()
        if df.empty:
            messagebox.showwarning("Sin Datos", "El catálogo maestro está vacío.")
            return
            
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Catalogo_Maestro_{fecha_str}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path: return

        # Usamos landscape (horizontal) porque son muchos datos
        c = canvas.Canvas(path, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        def draw_header_maestro(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawString(50, height - 50, "CATÁLOGO MAESTRO DE INVENTARIO GENERAL")
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawString(50, height - 70, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            canvas_obj.line(50, height - 80, width - 50, height - 80)
            
            # Encabezados
            canvas_obj.setFont("Helvetica-Bold", 9)
            y_table = height - 105
            headers = ["SKU", "MEDICAMENTO", "GRAMAJE", "PRESENTACIÓN", "TIPO", "STOCK", "ESTATUS"]
            x_pos = [50, 130, 370, 450, 540, 650, 710]
            
            for h, x in zip(headers, x_pos): 
                canvas_obj.drawString(x, y_table, h)
            return y_table - 20

        y = draw_header_maestro(c)
        c.setFont("Helvetica", 8)
        
        for _, row in df.iterrows():
            if y < 50:
                c.showPage()
                y = draw_header_maestro(c)
                c.setFont("Helvetica", 8)
                
            c.drawString(50, y, str(row['SKU']))
            c.drawString(130, y, str(row['MEDICAMENTO'])[:50]) # Cortamos a 50 chars si es muy largo
            c.drawString(370, y, str(row['GRAMAJE'])[:15])
            c.drawString(450, y, str(row['PRESENTACION'])[:15])
            c.drawString(540, y, str(row['TIPO'])[:15])
            c.drawString(650, y, str(row['STOCK_REAL']))
            
            # Resaltar en rojo si está INACTIVO
            estatus = str(row['ESTATUS'])
            if estatus == 'INACTIVO':
                c.setFillColorRGB(0.8, 0, 0)
            c.drawString(710, y, estatus)
            c.setFillColorRGB(0, 0, 0) # Regresar a negro
            
            y -= 15

        c.save()
        os.startfile(path)
    
    def obtener_datos_operativos(self):
        """Extrae toda la información de entradas y salidas operativas"""
        conn = sqlite3.connect(self.db.db_name)
        query = """
            SELECT sku as SKU, nombre || ' ' || gramaje || ' - ' || presentacion as DESCRIPCION, 
                   entradas_registro as E_REGISTRO, entradas_devolucion as E_DEVOLUCION, 
                   salidas_municipio as S_MUNICIPIO, salidas_merma as S_MERMA, 
                   stock_actual as STOCK_ACTUAL, stock_min as S_MIN, stock_max as S_MAX
            FROM medicamentos 
            WHERE estatus = 'ACTIVO' OR estatus IS NULL
            ORDER BY nombre ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Calculamos el estado (Óptimo, Reabastecer, Exceso) para el reporte
        def calcular_estado(row):
            if row['STOCK_ACTUAL'] <= row['S_MIN']: return "REABASTECER"
            if row['STOCK_ACTUAL'] > row['S_MAX']: return "EXCESO"
            return "ÓPTIMO"

        if not df.empty:
            df['ESTADO'] = df.apply(calcular_estado, axis=1)
            # Borramos las columnas de Min y Max para que no ocupen espacio innecesario en el PDF
            df = df.drop(columns=['S_MIN', 'S_MAX'])
            
        return df
    def reporte_operativo_excel(self):
        df = self.obtener_datos_operativos()
        if df.empty:
            messagebox.showwarning("Sin Datos", "El inventario operativo está vacío.")
            return
            
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"Inventario_Operativo_{fecha_str}.xlsx", filetypes=[("Excel", "*.xlsx")])
        if path: 
            self.formatear_y_guardar_excel(df, path, "REPORTE DE INVENTARIO OPERATIVO (MOVIMIENTOS)", "TODOS", "ACTIVOS")

    def reporte_operativo_pdf(self):
        df = self.obtener_datos_operativos()
        if df.empty:
            messagebox.showwarning("Sin Datos", "El inventario operativo está vacío.")
            return
            
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"Inventario_Operativo_{fecha_str}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path: return

        c = canvas.Canvas(path, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        def draw_header_operativo(canvas_obj):
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawString(50, height - 40, "REPORTE DE INVENTARIO OPERATIVO GENERAL")
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawString(50, height - 55, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            canvas_obj.line(50, height - 65, width - 50, height - 65)
            
            canvas_obj.setFont("Helvetica-Bold", 8)
            y_table = height - 85
            headers = ["SKU", "DESCRIPCIÓN", "E.REG", "E.DEV", "S.MUN", "S.MER", "STOCK", "ESTADO"]
            x_pos = [50, 110, 360, 410, 460, 510, 560, 620]
            
            for h, x in zip(headers, x_pos): 
                canvas_obj.drawString(x, y_table, h)
            return y_table - 20

        y = draw_header_operativo(c)
        c.setFont("Helvetica", 8)
        
        for _, row in df.iterrows():
            if y < 40:
                c.showPage()
                y = draw_header_operativo(c)
                c.setFont("Helvetica", 8)
                
            c.drawString(50, y, str(row['SKU']))
            c.drawString(110, y, str(row['DESCRIPCION'])[:55]) 
            c.drawString(360, y, str(row['E_REGISTRO']))
            c.drawString(410, y, str(row['E_DEVOLUCION']))
            c.drawString(460, y, str(row['S_MUNICIPIO']))
            c.drawString(510, y, str(row['S_MERMA']))
            
            # Pintar el Stock de acuerdo al estado
            c.setFont("Helvetica-Bold", 8)
            c.drawString(560, y, str(row['STOCK_ACTUAL']))
            
            estado = str(row['ESTADO'])
            if estado == 'REABASTECER': c.setFillColorRGB(0.8, 0, 0)
            elif estado == 'EXCESO': c.setFillColorRGB(0.8, 0.5, 0)
            else: c.setFillColorRGB(0, 0.5, 0) 
            
            c.drawString(620, y, estado)
            c.setFillColorRGB(0, 0, 0) 
            c.setFont("Helvetica", 8)
            
            y -= 14

        c.save()
        os.startfile(path)
    def regresar(self):
        self.root.destroy()
        self.main_window.deiconify()