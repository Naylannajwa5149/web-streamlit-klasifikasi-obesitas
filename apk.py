import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime
import json
import base64
import time

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Analisis Obesitas",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS kustom untuk tampilan yang lebih baik
st.markdown("""
    <style>
    /* Base styles */
    body {
        background-color: #1e1e1e;
        color: white;
    }
    
    /* Container styles */
    .main {
        padding: 1rem 2rem;
    }
    
    /* Card styles */
    .card {
        background-color: #2c2c2c;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border-left: 5px solid #0066cc;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: bold;
        color: #0066cc;
        margin-bottom: 1.2rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #0066cc;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        background-color: #3a3a3a;
        color: white;
        border: 1px solid #4a4a4a;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        padding: 0.8rem !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        background-color: #0066cc !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #0052a3 !important;
        transform: translateY(-2px);
    }
    
    /* Metric value styling */
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background-color: #3a3a3a;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* History table styling */
    .history-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .history-table th, .history-table td {
        padding: 0.8rem;
        text-align: left;
        border-bottom: 1px solid #4a4a4a;
    }
    
    .history-table th {
        background-color: #0066cc;
        color: white;
    }
    
    /* Toast notification styling */
    .toast {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 1rem;
        background-color: #28a745;
        color: white;
        border-radius: 8px;
        z-index: 1000;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'show_success' not in st.session_state:
    st.session_state.show_success = False
if 'success_time' not in st.session_state:
    st.session_state.success_time = None

# Fungsi untuk menghitung BMI, BMR, dan kategori
def calculate_metrics(weight, height, age, gender):
    bmi = weight / (height ** 2)
    
    if gender == "Laki-laki":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height * 100) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height * 100) - (4.330 * age)
    
    if bmi < 18.5:
        category = "Insufficient Weight"
        color = "#ff6b6b"
    elif 18.5 <= bmi < 25:
        category = "Normal Weight"
        color = "#51cf66"
    elif 25 <= bmi < 30:
        category = "Overweight Level I"
        color = "#ffd43b"
    elif 30 <= bmi < 35:
        category = "Overweight Level II"
        color = "#fa5252"
    elif 35 <= bmi < 40:
        category = "Overweight Level III"
        color = "#fa5252"
    else:
        category = "Overweight Level IV"
        color = "#fa5252"

    return bmi, bmr, category, color

# Fungsi untuk generate rekomendasi
def generate_recommendations(bmi_category: str, input_data: dict) -> dict:
    recommendations = {
        "🥗 Rekomendasi Cara Diet": [],
        "💪 Rekomendasi Olahraga": [],
        "🧘‍♀️ Rekomendasi Gaya Hidup": []
    }
    
    # Diet Recommendations based on input data
    diet_factors = []
    if input_data.get('FAVC', '') == 'ya':
        diet_factors.append("Anda sering mengonsumsi makanan tinggi kalori")
    if input_data.get('FCVC', 0) < 2:
        diet_factors.append("Konsumsi sayur dan buah kurang")
    if input_data.get('NCP', '') in ['1', '2']:
        diet_factors.append("Jumlah makan utama per hari kurang")
    if input_data.get('CAEC', '') in ['Sering', 'Selalu']:
        diet_factors.append("Sering mengonsumsi camilan")
    
    # Determine target based on BMI category
    if bmi_category == "Insufficient Weight":
        Target = "Meningkatkan berat badan 0.5-1 kg per minggu hingga mencapai BMI minimal 18.5"
        recommendations["🥗 Rekomendasi Cara Diet"] = [
            "Tingkatkan asupan kalori 500-1000 kkal di atas kebutuhan maintenance",
            "Konsumsi protein tinggi (1.6-2.2 gram/kg berat badan)",
            "Makan 5-6 kali sehari dengan porsi sedang",
            "Fokus pada makanan padat nutrisi dan kalori"
        ]
        # Add specific warnings based on input
        if diet_factors:
            recommendations["🥗 Rekomendasi Cara Diet"].append(f"Perhatian: {', '.join(diet_factors)}")
    
    elif bmi_category == "Normal Weight":
        Target = "Mempertahankan berat badan current dengan fluktuasi maksimal 2 kg"
        recommendations["🥗 Rekomendasi Cara Diet"] = [
            "Pertahankan asupan kalori sesuai kebutuhan maintenance",
            "Konsumsi protein 1.2-1.6 gram/kg berat badan",
            "Jaga pola makan 3 kali sehari dengan 2 snack",
            "Seimbangkan makronutrien (50% karbo, 30% protein, 20% lemak)"
        ]
        # Add specific advice based on input
        if diet_factors:
            recommendations["🥗 Rekomendasi Cara Diet"].append(f"Perhatian: {', '.join(diet_factors)}")
    
    else:
        Target = "Menurunkan berat badan 0.5-1 kg per minggu hingga mencapai BMI 24.9"
        recommendations["🥗 Rekomendasi Cara Diet"] = [
            "Kurangi asupan kalori 500-750 kkal di bawah maintenance",
            "Tingkatkan protein (1.8-2.2 gram/kg ideal body weight)",
            "Batasi karbohidrat sederhana dan lemak jenuh",
            "Makan 3 kali sehari dengan porsi terkontrol",
            "Utamakan sayuran dan protein lean"
        ]
        # Add specific warnings based on input
        if diet_factors:
            recommendations["🥗 Rekomendasi Cara Diet"].append(f"Fokus perbaiki: {', '.join(diet_factors)}")
    
    recommendations["Target"] = Target
    
    # Exercise Recommendations based on Physical Activity Frequency (FAF)
    exercise_intensity = {
        "1": {
            "base_recs": [
                "Mulai dengan 30 menit jalan kaki setiap hari",
                "Tambahkan latihan kekuatan 2x seminggu",
                "Target: 150 menit aktivitas sedang per minggu",
                "Fokus pada latihan dasar seperti squat, push-up, dan plank"
            ]
        },
        "2": {
            "base_recs": [
                "Pertahankan rutinitas olahraga 3-4x seminggu",
                "Kombinasikan cardio dan strength training",
                "Target: 200 menit aktivitas sedang per minggu",
                "Tambahkan variasi latihan untuk menghindari plateau"
            ]
        },
        "3": {
            "base_recs": [
                "Lanjutkan rutinitas olahraga intensif",
                "Fokus pada high-intensity interval training (HIIT)",
                "Target: 250-300 menit aktivitas sedang per minggu",
                "Pertimbangkan untuk bekerja dengan personal trainer"
            ]
        }
    }
    
    # Customize exercise recommendations
    extra_exercise_factors = []
    if input_data.get('TUE', 0) > 8:
        extra_exercise_factors.append("Waktu screen time tinggi")
    
    exercise_recs = exercise_intensity.get(input_data.get('FAF', '1'), exercise_intensity['1'])['base_recs']
    
    if extra_exercise_factors:
        exercise_recs.append(f"Perhatian: {', '.join(extra_exercise_factors)}")
    
    recommendations["💪 Rekomendasi Olahraga"] = exercise_recs
    
    # Lifestyle Recommendations
    lifestyle_recs = []
    
    if input_data.get('CH2O', 0) < 2.0:
        lifestyle_recs.append("Tingkatkan konsumsi air minimal 2L/hari")
    
    if input_data.get('SMOKE', '') == 'ya':
        lifestyle_recs.append("Pertimbangkan program berhenti merokok")
    
    if input_data.get('TUE', 0) > 8:
        lifestyle_recs.extend([
            "Kurangi screen time, gunakan teknik 20-20-20 untuk kesehatan mata",
            "Atur postur saat menggunakan gadget"
        ])
    
    # If no specific recommendations, add general advice
    if not lifestyle_recs:
        lifestyle_recs = [
            "Pertahankan gaya hidup sehat",
            "Jaga kualitas tidur 7-9 jam per hari",
            "Kelola stress dengan meditasi atau yoga",
            "Lakukan check-up kesehatan rutin"
        ]
    
    recommendations["🧘‍♀️ Rekomendasi Gaya Hidup"] = lifestyle_recs
    
    return recommendations


# Fungsi untuk export data ke CSV
def get_csv_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="riwayat_analisis.csv">Download CSV</a>'
    return href

# Header Aplikasi
st.markdown('<h1 style="text-align: center; color: #0066cc;">🏥 Sistem Analisis dan Prediksi Obesitas</h1>', unsafe_allow_html=True)

# Membuat tab
tabs = st.tabs(["📝 Input Data", "📊 Hasil Analisis", "📈 Riwayat", "💡 Rekomendasi"])

# Tab Input Data
with tabs[0]:
    with st.form(key="input_form"):  # Added key parameter
        st.markdown('<div class="section-header">Data Pribadi</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nama Lengkap", value="")
            age = st.number_input("Usia (Tahun)", min_value=15, max_value=100, value=25) 
        with col2:
            gender = st.selectbox("Jenis Kelamin", ["", "Laki-laki", "Perempuan"])
            height = st.number_input("Berapa tinggi badan (m) Anda?", min_value=1.0, max_value=2.5, value=1.5, step=0.01) 
        
        st.markdown('<div class="section-header">Pengukuran Fisik</div>', unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)
        with col3:
            weight = st.number_input("Berapa berat badan (kg) Anda?", min_value=5.0, max_value=300.0, value=60.0, step=0.1)  
        with col4:
            family_history = st.selectbox("Apakah ada riwayat obesitas dalam keluarga Anda?", ["", "ya", "tidak"])
        
        st.markdown('<div class="section-header">Pola Makan</div>', unsafe_allow_html=True)
        
        col5, col6 = st.columns(2)
        with col5:
            FAVC = st.selectbox("Apakah Anda sering mengkonsumsi makanan tinggi kalori?", ["", "ya", "tidak"])
            FCVC = st.selectbox("Apakah anda sering mengkonsumsi sayur dan buah? (1 Tidak Pernah, 2 Jarang, 3 Selalu)", [1, 2, 3])  
            NCP = st.selectbox("Berapa kali Anda makan utama per hari nya?", ["", "1", "2", "3", "4"])
        
        with col6:
            CAEC = st.selectbox("Apakah Anda sering mengkonsumsi camilan di antara waktu makan?", ["", "Tidak Pernah", "Kadang", "Sering", "Selalu"])
            SMOKE = st.selectbox("Apakah Anda merokok?", ["", "ya", "tidak"])
        
        st.markdown('<div class="section-header">Gaya Hidup</div>', unsafe_allow_html=True)
        
        col7, col8 = st.columns(2)
        with col7:
            CH2O = st.number_input("Anda mengkonsumsi air per Hari berapa Liter?", min_value=1.0, max_value=10.0, value=2.0, step=0.1)  
            FAF = st.selectbox("Seberapa sering Anda berolahraga per Minggu nya? (1 Tidak Pernah, 2 Kadang, 3 Sering)", ["", "1", "2", "3"])
            TUE = st.number_input("Berapa jam Anda menggunakan perangkat elektronik per hari?", min_value=0.0, max_value=24.0, value=2.0, step=0.1)
        
        with col8:
            CALC = st.selectbox("Apakah Anda Mengkonsumsi Alkohol?", ["", "Tidak Pernah", "Kadang", "Sering", "Selalu"])
            SCC = st.selectbox("Apakah Anda menghitung konsumsi kalori harian?", ["", "ya", "tidak"])
            MTRANS = st.selectbox("Alat transportasi apa yang Anda gunakan setiap hari?", ["", "Mobil", "Motor", "Sepeda", "Transportasi Publik", "Jalan Kaki"])
        
        # Submit button inside the form
        submitted = st.form_submit_button("Analisis Data")

# Penjelasan BMI
bmi_explanation = """
### Apa itu BMI?
Body Mass Index (BMI) atau Indeks Massa Tubuh (IMT) adalah pengukuran yang digunakan untuk menilai apakah berat badan seseorang berada dalam kategori normal, kurang, atau berlebih. BMI dihitung dengan membagi berat badan (dalam kilogram) dengan kuadrat tinggi badan (dalam meter).
"""
### Penjelasan Kategori BMI:
kategori_bmi_explanation = """
### Kategori BMI
- **Insufficient Weight (< 18.5)**: 
  Berat badan kurang dari normal, berisiko terhadap beberapa masalah kesehatan.

- **Normal Weight (18.5 - 24.9)**: 
  Berat badan ideal, menunjukkan keseimbangan yang baik.

- **Overweight Level I (25.0 - 29.9)**: 
  Berat badan berlebih tingkat awal.

- **Overweight Level II (30.0 - 34.9)**: 
  Obesitas tingkat I, berisiko terhadap penyakit metabolik.

- **Overweight Level III (35.0 - 39.9)**: 
  Obesitas tingkat II, risiko kesehatan serius.

- **Overweight Level IV (≥ 40)**: 
  Obesitas tingkat III, risiko kesehatan sangat serius.
"""

# Penjelasan BMR
bmr_explanation = """
### Apa itu BMR?
Basal Metabolic Rate (BMR) atau Laju Metabolisme Basal adalah jumlah kalori yang dibutuhkan tubuh untuk menjalankan fungsi dasar saat istirahat, seperti bernafas, mengatur suhu tubuh, dan memelihara fungsi organ vital. BMR berbeda untuk setiap orang dan dipengaruhi oleh faktor seperti usia, jenis kelamin, berat badan, dan tinggi badan.
"""

# Tab Hasil Analisis
with tabs[1]:
    if submitted:
        if not all([name, age, gender, height, weight, family_history, FAVC, FCVC, NCP, CAEC, SMOKE, CH2O, FAF, TUE, CALC, SCC, MTRANS]):
            st.error("Mohon lengkapi semua field input!")
        else:
            # Menghitung BMI, BMR, dan kategori
            bmi, bmr, category, color = calculate_metrics(weight, height, age, gender)
            
            # Menyimpan data ke history
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            input_data = {
                'timestamp': current_time,
                'name': name,
                'age': age,
                'gender': gender,
                'height': height,
                'weight': weight,
                'bmi': round(bmi, 2),
                'bmr': round(bmr, 2),
                'category': category,
                'FAF': FAF,
                'TUE': TUE,
                'CH2O': CH2O,
                'SMOKE': SMOKE
            }
            st.session_state.history.append(input_data)
            
            # Menampilkan hasil analisis
            # BMR
            st.markdown(bmr_explanation)
            st.markdown(f"""
            <div class="card">
                <h2>Hasil Analisis BMR Anda</h2>
                <div class="metric-value">BMR: {bmr:.2f} kkal/hari</div>
            </div>
            """, unsafe_allow_html=True)

            # BMI
            st.markdown(bmi_explanation)
            st.markdown(f"""
            <div class="card">
                <h2 style="color: {color};">Hasil Analisis BMI Anda</h2>
                <div class="metric-value" style="color: {color};">BMI: {bmi:.2f}</div>
                <h3 style="text-align: center; color: {color};">{category}</h3>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">Skala BMI Anda</div>', unsafe_allow_html=True)
        
            # Definisikan batas-batas BMI dan warna
            bmi_ranges = [
                {'max': 18.5, 'color': '#ff6b6b', 'label': 'Kurang'},
                {'max': 25, 'color': '#51cf66', 'label': 'Normal'},
                {'max': 30, 'color': '#ffd43b', 'label': 'Berlebih'},
                {'max': 40, 'color': '#fa5252', 'label': 'Obesitas'},
                {'max': float('inf'), 'color': '#fa5252', 'label': 'Obesitas'}
            ]

            fig = go.Figure()

            # Tambahkan area untuk setiap rentang BMI
            for i, range_info in enumerate(bmi_ranges):
                fig.add_trace(go.Scatter(
                    x=[0 if i == 0 else bmi_ranges[i-1]['max'], range_info['max']],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color=range_info['color'], width=10),
                    name=range_info['label']
                ))

            # Tambahkan marker untuk label
            fig.add_trace(go.Scatter(
                x=[0, 18.5, 25, 30, 40],
                y=[0, 0, 0, 0, 0],
                mode='markers+text',
                text=['', 'Kurang', 'Normal', 'Berlebih', 'Obesitas'],
                textposition='bottom center',
                marker=dict(
                    size=20,
                    color=['#ff6b6b', '#51cf66', '#ffd43b', '#fa5252', '#fa5252'],
                )
            ))

            # Tambahkan garis vertikal untuk BMI pengguna
            fig.add_vline(
                x=bmi, 
                line_dash="dash", 
                line_color=color,
                annotation_text=f"BMI Anda: {bmi:.2f}",
                annotation_position="top right"
            )

            fig.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, title='BMI'),
                yaxis=dict(showgrid=False, showticklabels=False),
                height=200,
                margin=dict(l=20, r=20, t=20, b=40)
            )

            st.plotly_chart(fig, use_container_width=True)
            st.markdown(kategori_bmi_explanation)
    else:
        st.info("📋 Silakan lengkapi formulir input data terlebih dahulu untuk mendapatkan hasil analisis personal.")

            
# Menampilkan notifikasi sukses
st.session_state.show_success = True
st.session_state.success_time = time.time()

# Tab Riwayat
with tabs[2]:
    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)
        st.markdown('<div class="section-header">Riwayat Analisis</div>', unsafe_allow_html=True)
        st.dataframe(history_df)
        st.markdown(get_csv_download_link(history_df), unsafe_allow_html=True)

        # Visualisasi trend BMI
        fig = px.line(history_df, x='timestamp', y='bmi', title='Trend BMI Over Time')
        st.plotly_chart(fig)
    else:
        st.info("Belum ada riwayat analisis.")

# Tab Rekomendasi
with tabs[3]:
    if 'submitted' not in locals() or not submitted:
        st.info("📋 Silakan lengkapi formulir input data terlebih dahulu untuk mendapatkan rekomendasi personal.")
        
        # guide tab rekomendasi
        st.markdown("""
        ### Bagaimana Cara Mendapatkan Rekomendasi?
        1. Navigasi ke tab "Input Data"
        2. Lengkapi semua field dengan informasi Anda
        3. Klik tombol "Analisis Data"
        4. Kembali ke tab Rekomendasi untuk melihat saran personal
        
        ### Informasi yang Dibutuhkan
        - Data pribadi (nama, usia, jenis kelamin)
        - Pengukuran fisik (tinggi, berat badan)
        - Pola makan dan kebiasaan
        - Aktivitas fisik dan gaya hidup
        """)
    else:
        st.markdown('<div class="section-header">🎯 Target</div>', unsafe_allow_html=True)
        recommendations = generate_recommendations("Normal Weight" if 'category' not in locals() else category, {
            'FAF': FAF, 'TUE': TUE, 'SMOKE': SMOKE, 'CH2O': CH2O,
            'FAVC': FAVC, 'FCVC': FCVC, 'NCP': NCP, 'CAEC': CAEC
        })
        if 'Target' in recommendations:
            st.markdown(f"### {recommendations['Target']}")
        for key, recs in recommendations.items():
            if key != 'Target':
                st.markdown(f'<div class="section-header">{key.capitalize()}</div>', unsafe_allow_html=True)
                for rec in recs:
                    st.write(f"- {rec}")