import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
import datetime
import requests

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Calculadora Maestra Pro", page_icon="🏗️", layout="wide")

cursor_svg = """
<style>
.stApp, button, input, textarea, a, select, div[role="button"], div[data-baseweb="select"], div[data-testid="stSelectbox"] > div, div[data-testid="stNumberInput"] > div, label {
    cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="%23FF5722" stroke="white" stroke-width="2"><path d="M2 2l11 18.5 3.5-7.5 7.5-3.5L2 2z"/></svg>'), auto !important;
}
div.stButton > button:hover { border-color: #FF5722 !important; color: #FF5722 !important; transform: scale(1.02); transition: all 0.2s ease; }
</style>
"""
st.markdown(cursor_svg, unsafe_allow_html=True)

# --- 2. GESTIÓN DE SEGURIDAD (EMAIL + CLAVE) ---
URL_LICENCIAS = "https://gist.githubusercontent.com/PabloDevCode/ebd32710506e47dcc3194d29da566398/raw/8b38d505eca9ab4964212ba634d413d35b0e9e1a/licencias.txt" 

# Respaldo local para pruebas (formato email:clave)
if "PEGAR_AQUI" in URL_LICENCIAS:
    URL_LICENCIAS = None 
    BASE_DATOS_LOCAL = {
        "admin@test.com": "MASTER2026",
        "cliente@obra.com": "PRUEBA1"
    }

if "usuario_validado" not in st.session_state:
    st.session_state["usuario_validado"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""
if "carrito_proyecto" not in st.session_state:
    st.session_state["carrito_proyecto"] = []

def verificar_credenciales_online(email, clave):
    """Verifica el par Email:Clave en el Gist"""
    if not email or not clave: return False
    
    # Normalizamos el email a minúsculas para evitar errores
    email = email.lower().strip()
    clave = clave.strip()

    # MODO LOCAL
    if URL_LICENCIAS is None:
        # Verifica si el email existe y si la clave coincide
        return BASE_DATOS_LOCAL.get(email) == clave
    
    # MODO ONLINE
    try:
        response = requests.get(URL_LICENCIAS, timeout=5)
        if response.status_code == 200:
            # Procesamos el texto línea por línea
            lineas = response.text.splitlines()
            for linea in lineas:
                if ":" in linea:
                    # Separamos "juan@gmail.com:CLAVE123"
                    datos = linea.split(":")
                    email_remoto = datos[0].strip().lower()
                    clave_remota = datos[1].strip()
                    
                    if email_remoto == email and clave_remota == clave:
                        return True
            return False
        else:
            st.error("⚠️ Error de conexión con servidor de licencias.")
            return False
    except:
        st.error("⚠️ Sin internet.")
        return False

def intentar_ingreso():
    if not st.session_state["check_terminos"]:
        st.error("⚠️ Debes aceptar los términos.")
        return

    email = st.session_state["input_email"]
    clave = st.session_state["input_password"]
    
    with st.spinner("Validando identidad..."):
        es_valido = verificar_credenciales_online(email, clave)
    
    if es_valido:
        st.session_state["usuario_validado"] = True
        st.session_state["user_email"] = email # Guardamos el email para el PDF
        st.toast(f"Hola {email.split('@')[0]}! Acceso concedido.")
    else:
        st.error("🚫 Credenciales incorrectas. Verifique Email y Clave.")

def limpiar_proyecto():
    st.session_state["carrito_proyecto"] = []

def eliminar_item(index):
    del st.session_state["carrito_proyecto"][index]

# --- 3. MOTOR PDF (CON MARCA DE AGUA DE EMAIL) ---
class PDFReport(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        hoy = datetime.date.today().strftime("%d/%m/%Y")
        # AQUI ESTA LA MAGIA: Imprime el email del usuario en el PDF
        usuario = st.session_state.get("user_email", "Usuario Desconocido")
        texto = f"Generado el {hoy} por {usuario}. Licencia intransferible. Prohibida su copia."
        self.cell(0, 10, texto, 0, 0, 'C')

def generar_pdf(df_total):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt="LISTA DE MATERIALES CONSOLIDADA", ln=True, align='C')
    pdf.ln(5)
    
    # Subtítulo con datos del cliente
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(80, 80, 80)
    usuario = st.session_state.get("user_email", "")
    pdf.cell(0, 10, txt=f"Licencia otorgada a: {usuario}", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, txt=f"Proyecto: {len(st.session_state['carrito_proyecto'])} ambientes calculados.", ln=True, align='L')
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(220, 230, 241) 
    w_cat, w_mat, w_uni, w_cant = 55, 95, 20, 20
    pdf.cell(w_cat, 10, "Categoría", 1, 0, 'C', 1)
    pdf.cell(w_mat, 10, "Material", 1, 0, 'C', 1)
    pdf.cell(w_uni, 10, "Unid.", 1, 0, 'C', 1) 
    pdf.cell(w_cant, 10, "Cant.", 1, 1, 'C', 1)
    pdf.set_font("Arial", size=9)
    for index, row in df_total.iterrows():
        cat = (str(row['Categoría'])[:28] + '..') if len(str(row['Categoría'])) > 28 else str(row['Categoría'])
        mat = (str(row['Material'])[:50] + '..') if len(str(row['Material'])) > 50 else str(row['Material'])
        pdf.cell(w_cat, 8, cat, 1)
        pdf.cell(w_mat, 8, mat, 1)
        pdf.cell(w_uni, 8, str(row['Unidad']), 1, 0, 'C')
        pdf.cell(w_cant, 8, str(row['Cantidad']), 1, 1, 'C')
    return pdf.output(dest="S").encode("latin-1")

# --- 4. MOTOR DE CÁLCULO ---
class CalculadoraConstruccion:
    def __init__(self, largo, altura, tipo_sistema, separacion, desperdicio, caras=1, capas=1, aislacion=False, espesor_cielo="9.5"):
        self.largo = largo
        self.altura = altura
        self.sup = largo * altura 
        self.tipo = tipo_sistema
        self.sep = separacion
        self.desp = 1 + (desperdicio / 100)
        self.caras = caras   
        self.capas = capas   
        self.con_aislacion = aislacion 
        self.espesor_cielo = espesor_cielo
        self.L_PERFIL_SF, self.L_PERFIL_DW, self.SUP_PLACA = 6.00, 2.60, 2.88    

    def calcular(self):
        materiales = []
        
        # --- A: TABIQUE DRYWALL ---
        if self.tipo == "Tabique Drywall (Interior)":
            ml_soleras = self.largo * 2
            cant_soleras = math.ceil((ml_soleras * self.desp) / self.L_PERFIL_DW)
            cant_montantes = math.ceil(((self.largo / self.sep) + 1) * (self.altura / self.L_PERFIL_DW) * self.desp)
            materiales.append(["Estructura", "Solera 70mm (2.6m)", "Unidades", cant_soleras])
            materiales.append(["Estructura", "Montante 69mm (2.6m)", "Unidades", cant_montantes])
            if self.con_aislacion:
                m2_lana = math.ceil(self.sup * self.desp)
                materiales.append(["Aislación", "Aislación Térmica/Acústica", "m²", m2_lana])
            sup_total_placas = self.sup * self.caras * self.capas
            cant_placas = math.ceil((sup_total_placas * self.desp) / self.SUP_PLACA)
            materiales.append(["Emplacado", "Placa Yeso 12.5mm", "Unidades", cant_placas])
            factor_tornillos = 30 * self.capas 
            cant_t2 = math.ceil(self.sup * self.caras * factor_tornillos * self.desp)
            materiales.append(["Fijaciones", "Tornillos T1", "Unidades", math.ceil(self.sup * 15 * self.desp)])
            materiales.append(["Fijaciones", "Tornillos T2 Aguja", "Unidades", cant_t2])
            materiales.append(["Fijaciones", "Tarugos 8mm + Tornillo", "Unidades", math.ceil((ml_soleras / 0.60) * self.desp)])
            materiales.append(["Terminación", "Cinta de Papel", "Metros", math.ceil(sup_total_placas * 1.6)])
            materiales.append(["Terminación", "Masilla (Juntas)", "Kg", math.ceil(sup_total_placas * 0.9)])

        # --- B: CIELORRASO 35mm ---
        elif self.tipo == "Cielorraso (Perfileria 35mm)":
            ml_perimetro = (self.largo + self.altura) * 2 
            cant_solera35 = math.ceil((ml_perimetro * self.desp) / self.L_PERFIL_DW)
            cant_montante35_teorica = (self.sup / self.sep) 
            cant_montante35 = math.ceil((cant_montante35_teorica * self.desp) / self.L_PERFIL_DW)
            materiales.append(["Estructura", "Solera 35mm (2.6m)", "Unidades", cant_solera35])
            materiales.append(["Estructura", "Montante 35mm (2.6m)", "Unidades", cant_montante35])
            materiales.append(["Suspensión", "Tornillos T1", "Unidades", math.ceil(self.sup * 15 * self.desp)])
            cant_tarugos_cielo = math.ceil((ml_perimetro / 0.60) * self.desp)
            materiales.append(["Fijaciones", "Tarugos 8mm + Tornillo", "Unidades", cant_tarugos_cielo])
            if self.con_aislacion:
                m2_lana = math.ceil(self.sup * self.desp)
                materiales.append(["Aislación", "Aislación Térmica/Acústica", "m²", m2_lana])
            cant_placas = math.ceil((self.sup * self.desp) / self.SUP_PLACA)
            nombre_placa_cielo = "Placa Yeso 12.5mm" if "12.5" in self.espesor_cielo else "Placa Yeso 9.5mm"
            materiales.append(["Emplacado", nombre_placa_cielo, "Unidades", cant_placas]) 
            materiales.append(["Fijaciones", "Tornillos T2 Aguja", "Unidades", math.ceil(self.sup * 25 * self.desp)])
            materiales.append(["Terminación", "Masilla (Juntas)", "Kg", math.ceil(self.sup * 0.90)])
            materiales.append(["Terminación", "Cinta de Papel", "Metros", math.ceil(self.sup * 1.6)])

        # --- C: STEEL FRAME + EIFS ---
        elif self.tipo == "Muro Steel Frame (EIFS)":
            ml_pgu = self.largo * 2
            cant_pgu = math.ceil((ml_pgu * self.desp) / self.L_PERFIL_SF)
            cant_pgc = math.ceil(((self.largo / self.sep) + 1) * self.desp)
            if self.altura > 3.0: cant_pgc *= 2
            materiales.append(["Estructura", "PGU 100mm (6m)", "Unidades", cant_pgu])
            materiales.append(["Estructura", "PGC 100mm (6m)", "Unidades", cant_pgc])
            ml_fleje = self.sup * 1.5 
            materiales.append(["Rigidización", "Fleje Acero Galvanizado", "Metros", math.ceil(ml_fleje)])
            cant_osb = math.ceil((self.sup * self.desp) / self.SUP_PLACA)
            cant_eps_placas = math.ceil((self.sup * self.desp) / self.SUP_PLACA)
            materiales.append(["EIFS - Sustrato", "Placa OSB 11.1mm", "Unidades", cant_osb])
            materiales.append(["EIFS - Aislación", "Barrera Agua/Viento (Tyvek)", "m²", math.ceil(self.sup * self.desp)])
            materiales.append(["EIFS - Aislación", "Plancha EPS Alta Densidad", "m²", math.ceil(self.sup * self.desp)])
            materiales.append(["EIFS - Base", "Base Coat", "Kg", math.ceil(self.sup * 3.5 * self.desp)])
            materiales.append(["EIFS - Malla", "Malla Fibra de Vidrio", "m²", math.ceil(self.sup * 1.1 * self.desp)])
            tornillos_eps = cant_eps_placas * 20
            materiales.append(["Fijaciones", "Tornillos + Arandelas PVC (EPS)", "Unidades", tornillos_eps])
            if self.con_aislacion:
                materiales.append(["Aislación", "Aislación Térmica/Acústica", "m²", math.ceil(self.sup * self.desp)])
            sup_placas_int = self.sup * self.capas 
            cant_yeso = math.ceil((sup_placas_int * self.desp) / self.SUP_PLACA)
            materiales.append(["Interior", "Placa Yeso 12.5mm", "Unidades", cant_yeso])
            materiales.append(["Fijaciones", "Tornillo Hexagonal", "Unidades", math.ceil(self.sup * 20 * self.desp)])
            cant_t2_osb = math.ceil(self.sup * 30 * self.desp)
            cant_t2_int = math.ceil(self.sup * 30 * self.capas * self.desp)
            total_t2_mecha = cant_t2_osb + cant_t2_int
            materiales.append(["Fijaciones", "Tornillos T2 Mecha", "Unidades", total_t2_mecha])

        df = pd.DataFrame(materiales, columns=["Categoría", "Material", "Unidad", "Cantidad"])
        return df[df["Cantidad"] > 0]

# --- 5. INTERFAZ (UI) ---
if not st.session_state["usuario_validado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🔒 Pack Estimación PRO</h1>", unsafe_allow_html=True)
        if URL_LICENCIAS and "PEGAR_AQUI" not in URL_LICENCIAS:
            st.caption("🟢 Servidor: Conectado")
        
        with st.form("login_form"):
            # AHORA PEDIMOS EMAIL TAMBIEN
            email = st.text_input("Correo Electrónico (Registrado):", key="input_email")
            password = st.text_input("Contraseña de Licencia:", type="password", key="input_password")
            terminos = st.checkbox("Acepto los Términos de Licencia.", key="check_terminos")
            st.form_submit_button("Ingresar", on_click=intentar_ingreso)

else:
    with st.sidebar:
        st.header("➕ Nuevo Cálculo")
        nombre_ambiente = st.text_input("Nombre (ej: Pasillo)", "Ambiente 1")
        tipo_sis = st.selectbox("Sistema", ["Tabique Drywall (Interior)", "Cielorraso (Perfileria 35mm)", "Muro Steel Frame (EIFS)"])
        
        st.subheader("Medidas")
        if "Cielorraso" in tipo_sis:
            l1 = st.number_input("Ancho (m)", min_value=0.1, value=3.0, step=0.1)
            l2 = st.number_input("Largo (m)", min_value=0.1, value=4.0, step=0.1)
            largo_calc, alto_calc = l1 * l2, 1
            st.caption(f"Superficie: {largo_calc:.2f} m²")
        else:
            largo_calc = st.number_input("Largo Muro (m)", min_value=0.1, value=5.0, step=0.1)
            alto_calc = st.number_input("Altura Muro (m)", min_value=0.1, value=2.6, step=0.1)
        
        st.subheader("Detalles Constructivos")
        caras, capas, aislacion, espesor_cielo = 1, 1, False, "9.5"
        
        if "Drywall" in tipo_sis:
            colA, colB = st.columns(2)
            with colA: caras = st.radio("Caras a emplacar", [1, 2], index=1)
            with colB: capas_idx = st.radio("Placas por cara", ["1 Placa", "2 Placas"], index=0)
            capas = 1 if "1" in capas_idx else 2
            st.divider()
            aislacion = st.checkbox("Incluir Aislación")
            
        elif "Steel" in tipo_sis:
            st.info("Exterior: EIFS (Std)")
            capas_idx = st.radio("Placas cara interior", ["1 Placa", "2 Placas"], index=0)
            capas = 1 if "1" in capas_idx else 2
            st.divider()
            aislacion = st.checkbox("Incluir Aislación")
            
        elif "Cielorraso" in tipo_sis:
            st.info("Estructura: Perfilería 35mm")
            espesor_idx = st.radio("Espesor Placa:", ["9.5mm (Estándar)", "12.5mm (Reforzado)"], index=0)
            espesor_cielo = "9.5" if "9.5" in espesor_idx else "12.5"
            st.divider()
            aislacion = st.checkbox("Incluir Aislación")

        sep = st.select_slider("Modulación (cm)", [40, 48, 60], value=40)
        desp = st.slider("Desperdicio (%)", 0, 20, 10)
        
        if st.button("Calcular y Agregar", type="primary"):
            L = largo_calc if "Cielorraso" not in tipo_sis else l1
            H = alto_calc if "Cielorraso" not in tipo_sis else l2
            calc = CalculadoraConstruccion(L, H, tipo_sis, sep/100, desp, caras, capas, aislacion, espesor_cielo)
            df_res = calc.calcular()
            st.session_state["carrito_proyecto"].append({"nombre": nombre_ambiente, "sistema": tipo_sis, "data": df_res})
            st.toast(f"✅ {nombre_ambiente} agregado!")

        st.divider()
        st.button("🗑️ Borrar Todo", on_click=limpiar_proyecto)

    # --- PANTALLA PRINCIPAL ---
    st.title("📋 Computo de Materiales - Profesional")
    
    if len(st.session_state["carrito_proyecto"]) > 0:
        all_dfs = [x['data'] for x in st.session_state["carrito_proyecto"]]
        df_concat = pd.concat(all_dfs)
        df_grouped = df_concat.groupby(["Material", "Unidad"], as_index=False)["Cantidad"].sum()
        mapa_categorias = df_concat.drop_duplicates(subset=["Material"]).set_index("Material")["Categoría"]
        df_grouped["Categoría"] = df_grouped["Material"].map(mapa_categorias)
        df_total = df_grouped[["Categoría", "Material", "Unidad", "Cantidad"]]
        df_total = df_total.sort_values(by=["Categoría", "Material"])
        
        st.success(f"Proyecto activo: {len(st.session_state['carrito_proyecto'])} ambientes calculados.")
        st.dataframe(df_total, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        csv = df_total.to_csv(index=False).encode('utf-8')
        col1.download_button("📥 Descargar CSV", csv, "materiales_consolidados.csv", "text/csv", type="secondary")
        pdf_bytes = generar_pdf(df_total)
        col2.download_button("📄 Descargar PDF Oficial", pdf_bytes, "lista_compras_oficial.pdf", "application/pdf", type="primary")
        
        st.divider()
        st.subheader("🛠️ Gestión de Ambientes")
        for i, item in enumerate(st.session_state["carrito_proyecto"]):
            with st.expander(f"📍 {i+1}. {item['nombre']} ({item['sistema']})"):
                c1, c2 = st.columns([4, 1])
                c1.table(item['data'])
                c2.button("🗑️ Eliminar", key=f"del_{i}", on_click=eliminar_item, args=(i,))
    else:
        st.info("Configura los muros o cielorrasos en la izquierda para comenzar.")