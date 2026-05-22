import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.stats import binom

# Mengatur tampilan halaman web
st.set_page_config(page_title="Simulasi Distribusi Binomial", layout="centered")

# Judul dan Deskripsi
st.title("Simulasi Distribusi Binomial")

# Membuat interaksi menggunakan Sidebar
n = st.sidebar.slider("Jumlah percobaan (n)", min_value=1, max_value=50, value=10, step=1)
p = st.sidebar.slider("Peluang sukses (p)", min_value=0.01, max_value=1.00, value=0.10, step=0.01)

# Menghitung probabilitas binomial
x = np.arange(0, n + 1)
y = binom.pmf(x, n, p)

# Membuat grafik dengan Plotly
fig = go.Figure()

# Menambahkan diagram batang
fig.add_trace(go.Bar(
    x=x, 
    y=y, 
    name='Peluang (PMF)', 
    marker_color='#3498db',
    marker_line_color='#2980b9',
    marker_line_width=1.5,
    opacity=0.8
))

# Menambahkan garis tren
fig.add_trace(go.Scatter(
    x=x, 
    y=y, 
    mode='lines+markers', 
    name='Tren', 
    line=dict(color='#e74c3c', width=3, dash='dot'),
    marker=dict(size=8, color='#c0392b')
))

# Mempercantik tampilan grafik
fig.update_layout(
    xaxis_title='Jumlah kejadian sukses (x)',
    yaxis_title='Peluang (Probabilitas)',
    template='plotly_white',
    hovermode='x unified',
    margin=dict(l=0, r=0, t=30, b=0),
    showlegend=False
)

# Menampilkan grafik ke dalam halaman web
st.plotly_chart(fig, use_container_width=True)

# Menambahkan penjelasan dinamis di bawah grafik
peluang_maks = np.max(y)
x_maks = x[np.argmax(y)]
st.info(f"💡 **Analisis Singkat:** Jika Anda melakukan **{n}** kali percobaan dengan peluang kesuksesan **{p*100:.0f}%**, kemungkinan paling besar adalah Anda akan mendapatkan **{x_maks}** kali kejadian sukses (Peluang: **{peluang_maks*100:.1f}%**).")