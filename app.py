import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
from pydantic import BaseModel, Field

# ==========================================
# 1. Definisi Skema JSON Multi-Soal (Deskripsi dalam Bahasa Indonesia)
# ==========================================
class QuestionGradingResult(BaseModel):
    question_number: int = Field(description="Nomor soal pada ujian.")
    transcribed_latex: str = Field(description="Pekerjaan tulisan tangan asli siswa yang ditranskripsikan menggunakan format LaTeX.")
    ai_solution_steps: list[str] = Field(description="Langkah-langkah solusi yang benar, diselesaikan oleh AI sebelum melihat pekerjaan siswa.")
    student_final_answer: str = Field(description="Jawaban akhir yang ditulis oleh siswa.")
    is_correct: bool = Field(description="True jika logika dan jawaban akhir siswa sepenuhnya benar.")
    work_shown_rating: str = Field(description="Misalnya: 'Sangat Baik', 'Baik', atau 'Perlu Perbaikan'.")
    identified_error: str = Field(description="Baris spesifik dan deskripsi di mana logika siswa salah. Jika tidak ada, tulis 'Tidak ada'.")
    student_facing_feedback: str = Field(description="Umpan balik yang empatik dan memotivasi untuk siswa khusus pada soal ini (dalam Bahasa Indonesia).")
    suggested_score: str = Field(description="Saran nilai untuk soal ini (misalnya, '4/5').")

class TestGradingResult(BaseModel):
    overall_suggested_score: str = Field(description="Total nilai yang dihitung untuk seluruh ujian (misalnya, '85/100').")
    overall_teacher_summary: str = Field(description="Ringkasan singkat kinerja siswa secara keseluruhan untuk dibaca oleh guru (dalam Bahasa Indonesia).")
    overall_student_feedback: str = Field(description="Catatan umum yang memotivasi untuk siswa mengenai seluruh ujian (dalam Bahasa Indonesia).")
    questions: list[QuestionGradingResult] = Field(description="Rincian penilaian untuk setiap soal secara individu.")

# ==========================================
# Pengaturan UI Streamlit
# ==========================================
st.set_page_config(page_title="AI Penilai Matematika Multi-Soal", layout="wide")
st.title("📝 AI Penilai Matematika Multi-Soal")
st.markdown("Nilai seluruh ujian sekaligus. Unggah soal ujian, lembar kerja siswa, dan berikan contoh penilaian Anda per soal.")

# Input API Key
api_key = st.sidebar.text_input("Masukkan API Key Gemini Anda:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("Silakan masukkan API Key Gemini Anda di sidebar untuk melanjutkan.")

# ==========================================
# Pengunggah File & Input Dinamis
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Konfigurasi Ujian & Lembar Kerja Siswa")
    
    # Input untuk jumlah soal
    num_questions = st.number_input("Berapa banyak soal dalam ujian ini?", min_value=1, max_value=20, value=3, step=1)
    
    st.markdown("**Soal Ujian:**")
    test_q_files = st.file_uploader("Unggah gambar soal ujian (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    test_q_images = [Image.open(f) for f in test_q_files] if test_q_files else []
    
    st.markdown("---")
    
    st.markdown("**Lembar Jawaban Siswa:**")
    student_files = st.file_uploader("Unggah halaman lembar jawaban siswa (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    student_images = [Image.open(f) for f in student_files] if student_files else []

with col2:
    st.subheader("2. Contoh Penilaian per Soal (Opsional)")
    st.info("Berikan contoh bagaimana Anda menilai soal tertentu pada ujian ini agar AI dapat meniru rubrik Anda.")
    
    example_data_by_question = {}
    
    # Membuat expander dinamis untuk setiap soal
    for i in range(1, int(num_questions) + 1):
        with st.expander(f"Rubrik / Contoh untuk Soal {i}"):
            ex_files = st.file_uploader(f"Unggah contoh penilaian untuk Soal {i}", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key=f"ex_upload_{i}")
            
            q_examples = []
            if ex_files:
                for j, ex_file in enumerate(ex_files):
                    img = Image.open(ex_file)
                    st.image(img, width=150)
                    ex_grade = st.text_input(
                        f"Nilai/Umpan balik yang diberikan untuk contoh ini:", 
                        key=f"g_{i}_{j}",
                        placeholder="Contoh: 3/5 - Dikurangi 2 poin karena lupa menambahkan negatif."
                    )
                    q_examples.append({"image": img, "grade": ex_grade})
            
            if q_examples:
                example_data_by_question[i] = q_examples

# ==========================================
# Logika Penilaian & Panggilan API Gemini
# ==========================================
if st.button("Nilai Seluruh Ujian", type="primary") and test_q_images and student_images and api_key:
    with st.spinner(f"Menganalisis {num_questions} soal, mengeksekusi kode, dan membuat umpan balik..."):
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                tools="code_execution" 
            )

            prompt_content = []
            
            prompt_content.append(f"Anda adalah seorang guru matematika SMP yang ahli dan sedang menilai ujian yang berisi tepat {num_questions} soal.")
            
            # 1. Memberikan Soal Ujian
            prompt_content.append("Pertama, tinjau gambar soal ujian kosong di bawah ini untuk mengidentifikasi dan membaca semua soal:")
            prompt_content.extend(test_q_images)
            
            # 2. Memberikan Contoh Spesifik per Soal
            if example_data_by_question:
                prompt_content.append("Selanjutnya, berikut adalah rubrik dan contoh penilaian yang dirinci per soal:")
                for q_num, examples in example_data_by_question.items():
                    prompt_content.append(f"--- Contoh Penilaian untuk Soal {q_num} ---")
                    for ex in examples:
                        prompt_content.append(ex["image"])
                        prompt_content.append(f"Umpan balik yang diberikan untuk gambar di atas: {ex['grade']}")
            
            # 3. Memberikan Lembar Kerja Siswa
            prompt_content.append("Sekarang, evaluasi halaman lembar jawaban siswa berikut ini:")
            prompt_content.extend(student_images)
            
            # 4. Instruksi untuk pemrosesan Multi-Soal
            instructions = f"""
            Ikuti instruksi ini dengan saksama untuk SEMUA {num_questions} soal:
            Langkah 1: Iterasi setiap soal mulai dari soal nomor 1 hingga {num_questions}.
            Langkah 2: Untuk soal saat ini, gunakan alat eksekusi kode (code execution) Anda untuk menghitung aritmatika langkah demi langkah dan mendapatkan jawaban akhir yang benar.
            Langkah 3: Temukan letak pekerjaan siswa untuk soal tersebut pada gambar lembar jawaban yang dikirim, lalu transkripsikan baris demi baris menggunakan format LaTeX.
            Langkah 4: Bandingkan langkah terverifikasi Anda dengan langkah siswa yang ditranskripsikan untuk mengidentifikasi penyimpangan atau kesalahan logika matematika.
            Langkah 5: Rujuk pada contoh penilaian yang diberikan secara khusus untuk soal ini (jika ada) untuk menentukan nilai parsial dan menyarankan skor yang adil.
            Langkah 6: Ulangi langkah 2-5 untuk semua soal yang ada.
            Langkah 7: Hitung total nilai keseluruhan dan buat ringkasan umpan balik. Pastikan umpan balik ditulis dalam Bahasa Indonesia.
            Langkah 8: Kembalikan output akhir yang secara ketat mematuhi skema JSON yang disediakan.
            """
            prompt_content.append(instructions)

            generation_config = genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=TestGradingResult,
                temperature=0.1 
            )

            response = model.generate_content(
                prompt_content,
                generation_config=generation_config
            )

            result_data = json.loads(response.text)
            
            st.success("Penilaian Ujian Selesai!")
            
            # ==========================================
            # Tampilan Dashboard & Hasil
            # ==========================================
            st.header("🏆 Ringkasan Keseluruhan Ujian")
            col_score, col_summary = st.columns([1, 2])
            with col_score:
                st.metric("Saran Total Nilai", result_data['overall_suggested_score'])
            with col_summary:
                st.write(f"**Ringkasan untuk Guru:** {result_data['overall_teacher_summary']}")
                st.info(f"**Umpan Balik Keseluruhan untuk Siswa:** {result_data['overall_student_feedback']}")
            
            st.markdown("---")
            st.header("📋 Rincian per Soal")
            
            for q in result_data['questions']:
                with st.expander(f"Soal {q['question_number']}: {q['suggested_score']} - {'✅ Benar' if q['is_correct'] else '❌ Salah'}", expanded=not q['is_correct']):
                    
                    st.write(f"**Jawaban Siswa:** {q['student_final_answer']}")
                    st.write(f"**Kesalahan Teridentifikasi:** {q['identified_error']}")
                    st.write(f"**Umpan Balik:** {q['student_facing_feedback']}")
                    
                    st.markdown("#### Data Verifikasi")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Transkripsi Pekerjaan Siswa (LaTeX):**")
                        st.code(q['transcribed_latex'], language="latex")
                    with col_b:
                        st.write("**Langkah Solusi Terverifikasi AI:**")
                        for step in q['ai_solution_steps']:
                            st.write(f"- {step}")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat menilai: {e}")