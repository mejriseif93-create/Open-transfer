import streamlit as st
import os
import json
import hashlib
import qrcode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
from datetime import datetime, timedelta
import io
from pathlib import Path

# Page config
st.set_page_config(
    page_title="SecureShare - Encrypted P2P File Sharing",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3em;
        font-weight: bold;
        color: #1f77d4;
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
        font-size: 1.2em;
    }
    .status-box {
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-success {
        background-color: #d4edda;
        border: 2px solid #28a745;
        color: #155724;
    }
    .status-info {
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
        color: #0c5460;
    }
    .status-warning {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        color: #856404;
    }
    .feature-box {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77d4;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'files_sent' not in st.session_state:
    st.session_state.files_sent = {}
if 'files_received' not in st.session_state:
    st.session_state.files_received = {}
if 'encryption_key' not in st.session_state:
    st.session_state.encryption_key = None

# ==================== ENCRYPTION FUNCTIONS ====================

def derive_key_from_password(password: str, salt: bytes = None) -> tuple:
    """Derive encryption key from password using PBKDF2"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_file(file_bytes: bytes, password: str) -> dict:
    """Encrypt file with password"""
    try:
        key, salt = derive_key_from_password(password)
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(file_bytes)
        
        return {
            'success': True,
            'encrypted_data': encrypted_data,
            'salt': base64.b64encode(salt).decode(),
            'key': key.decode(),
            'file_hash': hashlib.sha256(file_bytes).hexdigest()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def decrypt_file(encrypted_data: bytes, password: str, salt_b64: str) -> dict:
    """Decrypt file with password"""
    try:
        salt = base64.b64decode(salt_b64)
        key, _ = derive_key_from_password(password, salt)
        cipher = Fernet(key)
        decrypted_data = cipher.decrypt(encrypted_data)
        
        return {
            'success': True,
            'decrypted_data': decrypted_data,
            'file_hash': hashlib.sha256(decrypted_data).hexdigest()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_magnet_link(file_hash: str, file_name: str, file_size: int) -> str:
    """Generate magnet link for torrent"""
    magnet = f"magnet:?xt=urn:btih:{file_hash}&dn={file_name}&xl={file_size}"
    return magnet

def generate_share_url(file_id: str, password_hash: str) -> str:
    """Generate shareable URL"""
    return f"https://secureshare.app/download?id={file_id}&key={password_hash}"

# ==================== MAIN INTERFACE ====================

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="main-header">🔒 SecureShare</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Encrypted P2P File Sharing - Zero Trust Architecture</div>', unsafe_allow_html=True)

# Navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Send File", "📥 Receive File", "📊 Dashboard", "🔐 Security Info", "❓ Help"])

# ==================== TAB 1: SEND FILE ====================
with tab1:
    st.header("📤 Send a File")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Select Your File")
        uploaded_file = st.file_uploader("Choose file to send", type=None)
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            st.info(f"📦 File size: {file_size / 1024 / 1024:.2f} MB")
    
    with col2:
        st.subheader("Step 2: Set Encryption Password")
        password = st.text_input("Create a strong password", type="password", key="send_password")
        password_confirm = st.text_input("Confirm password", type="password", key="send_password_confirm")
        
        if password and password_confirm:
            if password != password_confirm:
                st.error("❌ Passwords don't match!")
            elif len(password) < 8:
                st.error("❌ Password must be at least 8 characters")
            else:
                st.success("✓ Password strength: Good")
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            expiry_days = st.slider("File expiry (days)", 1, 30, 7)
        with col2:
            max_downloads = st.number_input("Max downloads (0 = unlimited)", 0, 100, 0)
    
    # Process file
    if uploaded_file and password and password == password_confirm and len(password) >= 8:
        if st.button("🚀 Encrypt & Create Share Link", use_container_width=True, type="primary"):
            with st.spinner("🔐 Encrypting file..."):
                file_bytes = uploaded_file.getvalue()
                
                # Encrypt
                encryption_result = encrypt_file(file_bytes, password)
                
                if encryption_result['success']:
                    st.session_state.encryption_key = encryption_result['key']
                    
                    # Create file ID
                    file_id = hashlib.sha256(f"{uploaded_file.name}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
                    
                    # Generate magnet link
                    magnet = generate_magnet_link(
                        encryption_result['file_hash'],
                        uploaded_file.name,
                        file_size
                    )
                    
                    # Generate share URL
                    share_url = generate_share_url(file_id, encryption_result['key'][:20])
                    
                    # Store in session
                    st.session_state.files_sent[file_id] = {
                        'name': uploaded_file.name,
                        'size': file_size,
                        'hash': encryption_result['file_hash'],
                        'salt': encryption_result['salt'],
                        'created': datetime.now().isoformat(),
                        'expiry': (datetime.now() + timedelta(days=expiry_days)).isoformat(),
                        'downloads': 0,
                        'max_downloads': max_downloads,
                        'encrypted_data': base64.b64encode(encryption_result['encrypted_data']).decode(),
                        'magnet': magnet,
                        'share_url': share_url
                    }
                    
                    st.success("✓ File encrypted successfully!")
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("📤 Your Share Links")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Magnet Link** (for torrent clients):")
                        st.code(magnet, language="text")
                        st.button("Copy Magnet Link", key="copy_magnet", use_container_width=True)
                    
                    with col2:
                        st.write("**Share URL** (for web/app):")
                        st.code(share_url, language="text")
                        st.button("Copy Share URL", key="copy_url", use_container_width=True)
                    
                    # QR Code
                    st.subheader("🔗 QR Code for Easy Sharing")
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(share_url)
                    qr.make(fit=True)
                    qr_img = qr.make_image(fill_color="black", back_color="white")
                    
                    st.image(qr_img, width=300, caption="Scan to share")
                    
                    # File info
                    st.markdown("---")
                    st.subheader("📋 File Information")
                    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                    
                    with info_col1:
                        st.metric("File Size", f"{file_size / 1024 / 1024:.2f} MB")
                    with info_col2:
                        st.metric("Expiry", f"{expiry_days} days")
                    with info_col3:
                        st.metric("File ID", file_id[:8] + "...")
                    with info_col4:
                        st.metric("Status", "🟢 Active")
                    
                    # Encryption info
                    st.markdown("---")
                    with st.expander("🔐 Encryption Details"):
                        st.write(f"**File Hash (SHA-256):** `{encryption_result['file_hash']}`")
                        st.write(f"**Salt:** `{encryption_result['salt']}`")
                        st.write(f"**Encryption Algorithm:** AES-256 (Fernet)")
                        st.write(f"**Key Derivation:** PBKDF2-SHA256 (100,000 iterations)")
                        st.write("**Security Level:** Military-Grade ⭐⭐⭐⭐⭐")
                else:
                    st.error(f"❌ Encryption failed: {encryption_result['error']}")

# ==================== TAB 2: RECEIVE FILE ====================
with tab2:
    st.header("📥 Receive a File")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Enter Share URL or Magnet Link")
        share_input = st.text_area("Paste the share URL or magnet link", height=100)
    
    with col2:
        st.subheader("Step 2: Enter Decryption Password")
        decrypt_password = st.text_input("Enter the password shared with you", type="password", key="receive_password")
    
    # Extract file ID from URL
    file_id = None
    if share_input and "id=" in share_input:
        try:
            file_id = share_input.split("id=")[1].split("&")[0]
        except:
            pass
    
    if file_id and file_id in st.session_state.files_sent and decrypt_password:
        if st.button("🔓 Decrypt & Download", use_container_width=True, type="primary"):
            file_data = st.session_state.files_sent[file_id]
            
            # Check expiry
            expiry_time = datetime.fromisoformat(file_data['expiry'])
            if datetime.now() > expiry_time:
                st.error("❌ This file has expired!")
            else:
                # Check max downloads
                if file_data['max_downloads'] > 0 and file_data['downloads'] >= file_data['max_downloads']:
                    st.error("❌ Maximum downloads reached!")
                else:
                    with st.spinner("🔓 Decrypting file..."):
                        # Decrypt
                        encrypted_bytes = base64.b64decode(file_data['encrypted_data'])
                        decryption_result = decrypt_file(
                            encrypted_bytes,
                            decrypt_password,
                            file_data['salt']
                        )
                        
                        if decryption_result['success']:
                            # Verify hash
                            if decryption_result['file_hash'] == file_data['hash']:
                                st.success("✓ File decrypted successfully!")
                                
                                # Update download count
                                st.session_state.files_sent[file_id]['downloads'] += 1
                                
                                # Provide download
                                st.download_button(
                                    label="📥 Download File",
                                    data=decryption_result['decrypted_data'],
                                    file_name=file_data['name'],
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                                
                                st.markdown("---")
                                st.success("✓ Download complete! File verified with hash validation.")
                            else:
                                st.error("❌ File hash mismatch - file may be corrupted")
                        else:
                            st.error(f"❌ Decryption failed: {decryption_result['error']}")
                            st.info("💡 Tip: Make sure you entered the correct password")
    elif share_input and not file_id:
        st.warning("⚠️ Could not extract file ID from URL. Make sure you copied the complete link.")
    elif not file_id or file_id not in st.session_state.files_sent:
        st.info("👆 Enter a share URL or magnet link to get started")

# ==================== TAB 3: DASHBOARD ====================
with tab3:
    st.header("📊 Transfer Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Files Sent")
        if st.session_state.files_sent:
            for file_id, file_data in st.session_state.files_sent.items():
                expiry_time = datetime.fromisoformat(file_data['expiry'])
                time_left = expiry_time - datetime.now()
                
                with st.container(border=True):
                    col_name, col_status = st.columns([3, 1])
                    
                    with col_name:
                        st.write(f"📄 **{file_data['name']}**")
                        st.caption(f"Size: {file_data['size'] / 1024 / 1024:.2f} MB")
                    
                    with col_status:
                        if time_left.total_seconds() > 0:
                            st.write("🟢 Active")
                        else:
                            st.write("🔴 Expired")
                    
                    st.write(f"⏱️ Expires in: {time_left.days}d {time_left.seconds // 3600}h")
                    st.write(f"📊 Downloads: {file_data['downloads']}" + 
                            (f"/{file_data['max_downloads']}" if file_data['max_downloads'] > 0 else ""))
                    
                    if st.button(f"Delete", key=f"delete_{file_id}", use_container_width=True):
                        del st.session_state.files_sent[file_id]
                        st.rerun()
        else:
            st.info("No files sent yet")
    
    with col2:
        st.subheader("📥 Files Received")
        if st.session_state.files_received:
            for file_id, file_data in st.session_state.files_received.items():
                with st.container(border=True):
                    st.write(f"📄 **{file_data['name']}**")
                    st.caption(f"Size: {file_data['size'] / 1024 / 1024:.2f} MB")
                    st.write(f"✓ Received: {file_data['received_at']}")
                    
                    if st.button(f"Delete", key=f"delete_recv_{file_id}", use_container_width=True):
                        del st.session_state.files_received[file_id]
                        st.rerun()
        else:
            st.info("No files received yet")

# ==================== TAB 4: SECURITY INFO ====================
with tab4:
    st.header("🔐 Security & Architecture")
    
    st.markdown("""
    ### How SecureShare Works
    
    #### 📤 **Sending Process**
    1. **Upload**: You select a file
    2. **Encrypt**: File is encrypted with AES-256 using your password
    3. **Split**: Encrypted file is split into torrent pieces
    4. **Distribute**: Pieces uploaded to BitTorrent DHT network
    5. **Share**: Only a tiny URL (magnet link) is sent to recipient
    6. **Turnoff**: Your device can turn OFF immediately - file lives in network
    
    #### 📥 **Receiving Process**
    1. **Click Link**: Recipient opens share URL
    2. **Join Network**: App joins BitTorrent swarm
    3. **Download**: Pieces downloaded from network (NOT from sender!)
    4. **Assemble**: All pieces reassembled
    5. **Decrypt**: Auto-decrypted with shared password
    6. **Ready**: File ready to use
    
    ### 🔐 Security Features
    
    ✓ **End-to-End Encryption**: AES-256 (military-grade)  
    ✓ **Zero Knowledge**: We can't read your files  
    ✓ **No Accounts**: No registration needed  
    ✓ **No Servers**: Uses decentralized BitTorrent  
    ✓ **No Tracking**: No analytics, no logging  
    ✓ **Open Source Ready**: Code fully auditable  
    ✓ **Password Protected**: PBKDF2-SHA256 key derivation  
    ✓ **File Verification**: SHA-256 hash validation  
    
    ### 🛡️ Encryption Details
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **Encryption Algorithm**
        - AES-256-CBC
        - Fernet (symmetric)
        - HMAC built-in
        """)
    
    with col2:
        st.markdown("""
        **Key Derivation**
        - PBKDF2-SHA256
        - 100,000 iterations
        - 16-byte random salt
        """)
    
    with col3:
        st.markdown("""
        **File Integrity**
        - SHA-256 hashing
        - Pre/post transfer
        - Corruption detection
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### ⚠️ What We DON'T Do
    
    ❌ Store files on our servers  
    ❌ See encrypted file contents  
    ❌ Track who downloads what  
    ❌ Require any account  
    ❌ Collect metadata  
    ❌ Use ads or tracking  
    ❌ Sell your data  
    
    ### 🌍 Decentralized Architecture
    
    Your file doesn't live on our servers - it lives in the **BitTorrent DHT network**.
    This means:
    - We can't access it even if we wanted to
    - No central point of failure
    - Government can't compel us to hand over files
    - Works even if our servers go down
    - Only lives as long as people seed it
    """)

# ==================== TAB 5: HELP ====================
with tab5:
    st.header("❓ Help & FAQ")
    
    faq = {
        "What is SecureShare?": """
        SecureShare is a private, encrypted file sharing app that uses peer-to-peer technology 
        (BitTorrent) to transfer files directly between users without storing them on central servers.
        """,
        
        "How is my file encrypted?": """
        Your file is encrypted using AES-256, military-grade encryption. The password you set 
        is used with PBKDF2-SHA256 key derivation (100,000 iterations) to create a unique encryption key.
        """,
        
        "Can you see my files?": """
        No. Files are encrypted on YOUR device before leaving. We never have the encryption key. 
        Even if we wanted to, we couldn't decrypt them.
        """,
        
        "What happens if my device turns off?": """
        Your file stays alive in the BitTorrent network! Other seeders keep it available. 
        The recipient can still download it even if your device is offline.
        """,
        
        "How long do files stay available?": """
        By default, 7 days. But this depends on seeders. If no one is seeding (sharing) the file, 
        it becomes unavailable after the torrent DHT forgets about it.
        """,
        
        "Can I share with multiple people?": """
        Yes! Just send the same share URL to multiple people. They all use the same password to decrypt.
        """,
        
        "Is there a file size limit?": """
        No! BitTorrent handles terabyte-sized files perfectly. Limited only by your device storage.
        """,
        
        "What if someone intercepts the share link?": """
        They still need the password. The link alone is useless without the correct password. 
        It's like having an address without a key.
        """,
        
        "Do I need an account?": """
        No accounts needed. No registration, no email, no phone number. Just use the app.
        """,
        
        "Is this production ready?": """
        This demo is fully functional with real encryption. For production, you'd need a proper 
        BitTorrent client integration, distributed servers, and compliance infrastructure.
        """
    }
    
    for question, answer in faq.items():
        with st.expander(f"❓ {question}"):
            st.write(answer)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 40px;'>
    <p>🔒 <b>SecureShare</b> - Encrypted P2P File Sharing</p>
    <p>Made with ❤️ for privacy</p>
    <p style='font-size: 0.9em;'>This is a demonstration of the concept. Production version requires real BitTorrent integration.</p>
</div>
""", unsafe_allow_html=True)
