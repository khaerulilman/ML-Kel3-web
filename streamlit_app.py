# streamlit_app.py
import streamlit as st
import requests
import time

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Apriori Hukum Tajwid", layout="wide")
st.title("🕌 Apriori: Analisis Pola Hukum Tajwid")

# URL API Flask
API_URL = "https://web-production-012bf.up.railway.app/"

# Fungsi untuk mengecek koneksi API
def check_api_connection():
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

# Fungsi untuk mendapatkan dataset
@st.cache_data(ttl=5)  # Cache data selama 5 detik
def get_dataset():
    try:
        response = requests.get(f"{API_URL}/dataset", timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Cek koneksi API
if not check_api_connection():
    st.error("⚠️ Tidak dapat terhubung ke Flask API!")
    st.info("Pastikan Flask API berjalan di http://localhost:5000")
    st.code("python app.py", language="bash")
    st.stop()
else:
    st.success("✅ Terhubung ke Flask API")

# --- Sidebar Input Data ---
st.sidebar.header("📝 Tambah Data Transaksi")

# Initialize session state untuk mencegah loop
if "data_added" not in st.session_state:
    st.session_state.data_added = False
if "data_deleted" not in st.session_state:
    st.session_state.data_deleted = False
if "data_edited" not in st.session_state:
    st.session_state.data_edited = False
if "last_action_time" not in st.session_state:
    st.session_state.last_action_time = 0

with st.sidebar.form(key="input_form"):
    input_items = st.text_area(
        "Masukkan hukum tajwid (pisahkan dengan koma)",
        placeholder="Contoh: ikhfa, qalqalah, mad, ghunnah",
        height=100
    )
    submit_button = st.form_submit_button("➕ Tambah Data")

if submit_button and input_items:
    items = [x.strip() for x in input_items.split(",") if x.strip()]
    if items:
        try:
            response = requests.post(f"{API_URL}/dataset", json=items, timeout=5)
            if response.status_code == 200:
                st.sidebar.success("✅ Data berhasil ditambahkan!")
                # Clear cache untuk memuat ulang data
                st.cache_data.clear()
                # Set flag untuk refresh data tanpa infinite loop
                st.session_state.data_added = True
                st.session_state.last_action_time = time.time()
            else:
                error_msg = response.json().get('error', 'Gagal menambahkan data')
                st.sidebar.error(f"❌ {error_msg}")
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
    else:
        st.sidebar.warning("⚠️ Masukkan data yang valid")

# Reset flag setelah beberapa saat
if st.session_state.data_added and (time.time() - st.session_state.last_action_time) > 2:
    st.session_state.data_added = False

# --- Tampilkan Dataset ---
st.header("📊 Dataset Hukum Tajwid")
dataset = get_dataset()

if not dataset:
    st.warning("📋 Dataset masih kosong. Silakan tambahkan data melalui sidebar.")
    st.info("💡 Contoh data: ikhfa, qalqalah, mad, ghunnah")
else:
    st.success(f"📈 Total transaksi: {len(dataset)}")
    
    # Tampilkan dataset dalam tabel yang rapi
    for idx, transaction in enumerate(dataset):
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            st.write(f"**{idx+1}.** {', '.join(transaction)}")
        with col2:
            if st.button("✏️", key=f"edit_{idx}", help="Edit transaksi"):
                st.session_state.edit_idx = idx
                st.session_state.edit_value = ', '.join(transaction)
        with col3:
            # Menggunakan confirm dialog untuk delete
            if st.button("🗑️", key=f"del_{idx}", help="Hapus transaksi"):
                if f"confirm_delete_{idx}" not in st.session_state:
                    st.session_state[f"confirm_delete_{idx}"] = True
                else:
                    try:
                        response = requests.delete(f"{API_URL}/dataset/{idx}", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ Transaksi berhasil dihapus!")
                            st.cache_data.clear()
                            # Reset confirmation state
                            if f"confirm_delete_{idx}" in st.session_state:
                                del st.session_state[f"confirm_delete_{idx}"]
                            st.session_state.data_deleted = True
                            st.session_state.last_action_time = time.time()
                        else:
                            st.error("❌ Gagal menghapus transaksi")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        # Tampilkan konfirmasi delete
        if f"confirm_delete_{idx}" in st.session_state:
            st.warning(f"⚠️ Yakin ingin menghapus transaksi {idx+1}? Klik lagi tombol hapus untuk konfirmasi.")

# Reset delete flag
if st.session_state.data_deleted and (time.time() - st.session_state.last_action_time) > 2:
    st.session_state.data_deleted = False

# --- Form Edit ---
if "edit_idx" in st.session_state:
    st.markdown("---")
    st.subheader("✏️ Edit Transaksi")
    with st.form("edit_form"):
        new_value = st.text_input(
            "Edit hukum tajwid (pisahkan dengan koma):",
            value=st.session_state.edit_value
        )
        col1, col2 = st.columns(2)
        with col1:
            save_edit = st.form_submit_button("💾 Simpan Perubahan")
        with col2:
            cancel_edit = st.form_submit_button("❌ Batal")
    
    if save_edit and new_value:
        new_items = [x.strip() for x in new_value.split(",") if x.strip()]
        if new_items:
            try:
                response = requests.put(
                    f"{API_URL}/dataset/{st.session_state.edit_idx}", 
                    json=new_items, 
                    timeout=5
                )
                if response.status_code == 200:
                    st.success("✅ Transaksi berhasil diubah!")
                    del st.session_state.edit_idx
                    del st.session_state.edit_value
                    st.cache_data.clear()
                    st.session_state.data_edited = True
                    st.session_state.last_action_time = time.time()
                else:
                    st.error("❌ Gagal mengubah transaksi")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    if cancel_edit:
        del st.session_state.edit_idx
        del st.session_state.edit_value

# Reset edit flag
if st.session_state.data_edited and (time.time() - st.session_state.last_action_time) > 2:
    st.session_state.data_edited = False

# --- Proses Apriori ---
if dataset:
    st.markdown("---")
    st.header("🔍 Analisis Asosiasi")
    
    col1, col2 = st.columns(2)
    with col1:
        min_support = st.slider(
            "Minimum Support", 
            0.01, 1.0, 0.3, 0.01,
            help="Minimum support threshold untuk frequent itemsets"
        )
    with col2:
        min_confidence = st.slider(
            "Minimum Confidence", 
            0.01, 1.0, 0.6, 0.01,
            help="Minimum confidence threshold untuk association rules"
        )
    
    # Informasi parameter
    st.info(f"📊 Parameter: Support ≥ {min_support:.2f}, Confidence ≥ {min_confidence:.2f}")
    
    if st.button("🚀 Generate Aturan Asosiasi", type="primary"):
        with st.spinner("🔄 Memproses data..."):
            try:
                params = {
                    "min_support": min_support,
                    "min_confidence": min_confidence
                }
                response = requests.post(f"{API_URL}/rules", json=params, timeout=30)
                
                if response.status_code == 200:
                    rules = response.json()
                    if rules:
                        st.success(f"✅ Ditemukan {len(rules)} aturan asosiasi")
                        
                        # Tampilkan rules dalam format yang rapi
                        for i, rule in enumerate(rules, 1):
                            with st.expander(f"📋 Aturan {i}: {', '.join(rule['antecedents'])} → {', '.join(rule['consequents'])}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Support", f"{rule['support']:.3f}")
                                with col2:
                                    st.metric("Confidence", f"{rule['confidence']:.3f}")
                                with col3:
                                    st.metric("Lift", f"{rule['lift']:.3f}")
                                
                                st.markdown(f"""
                                **Interpretasi:**
                                - Jika seorang pembaca menggunakan hukum **{', '.join(rule['antecedents'])}**
                                - Maka kemungkinan dia juga akan menggunakan hukum **{', '.join(rule['consequents'])}**
                                - Dengan tingkat kepercayaan **{rule['confidence']:.1%}**
                                """)
                    else:
                        st.warning("⚠️ Tidak ditemukan aturan dengan parameter saat ini")
                        st.info("💡 Coba turunkan nilai minimum support atau confidence")
                else:
                    error_msg = response.json().get('error', 'Gagal memproses data')
                    st.error(f"❌ {error_msg}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# --- Footer ---
st.markdown("---")
st.markdown("""
### 📚 Petunjuk Penggunaan:
1. **Tambah Data**: Masukkan hukum tajwid yang digunakan dalam satu ayat, pisahkan dengan koma
2. **Edit/Hapus**: Gunakan tombol edit ✏️ atau hapus 🗑️ untuk mengelola data
3. **Analisis**: Atur parameter dan klik tombol generate untuk mendapatkan aturan asosiasi
4. **Interpretasi**: Lihat hasil analisis untuk memahami pola penggunaan hukum tajwid

### 🎯 Contoh Data:
- `ikhfa, qalqalah, mad thabi'i`
- `ghunnah, idgham, mad lazim`
- `ikhfa, mad wajib, qalqalah`
""")

# Status API
with st.expander("🔧 Status Sistem"):
    if check_api_connection():
        st.success("✅ Flask API: Terhubung")
    else:
        st.error("❌ Flask API: Tidak terhubung")
    
    st.info(f"🌐 API URL: {API_URL}")
    st.info(f"📈 Total Dataset: {len(dataset)}")
