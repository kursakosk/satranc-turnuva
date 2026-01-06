import streamlit as st
import pandas as pd
import random
import os

# --- Sayfa Ayarları ve İsim ---
st.set_page_config(
    page_title="Kurtköy Satranç ve Akıl Oyunları SK",
    page_icon="♟️",
    layout="centered"
)

# --- Session State (Hafıza) ---
if 'players' not in st.session_state:
    st.session_state.players = []
if 'rounds_played' not in st.session_state:
    st.session_state.rounds_played = 0
if 'pairings' not in st.session_state:
    st.session_state.pairings = []
if 'bye_player' not in st.session_state:
    st.session_state.bye_player = None
if 'round_active' not in st.session_state:
    st.session_state.round_active = False

# --- Fonksiyonlar ---
def calculate_buchholz():
    for p in st.session_state.players:
        bh_score = 0
        for opp_name in p['opponents']:
            opponent = next((x for x in st.session_state.players if x['name'] == opp_name), None)
            if opponent:
                bh_score += opponent['score']
        p['buchholz'] = bh_score

def generate_pairings():
    players = st.session_state.players
    random.shuffle(players)
    players.sort(key=lambda x: x['score'], reverse=True)
    unpaired = players[:]
    pairings = []
    bye = None

    if len(unpaired) % 2 == 1:
        bye = unpaired.pop()
    
    while len(unpaired) > 0:
        p1 = unpaired.pop(0)
        found_opponent = False
        for i, p2 in enumerate(unpaired):
            if p2['name'] not in p1['opponents']:
                pairings.append({'white': p1, 'black': p2, 'result': None})
                unpaired.pop(i)
                found_opponent = True
                break
        if not found_opponent and unpaired:
            p2 = unpaired.pop(0)
            pairings.append({'white': p1, 'black': p2, 'result': None})

    return pairings, bye

# --- Arayüz (UI) ---

# LOGO VE BAŞLIK ALANI
col1, col2 = st.columns([1, 4])
with col1:
    # Logo dosyasını kontrol et, varsa göster
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=100)
    else:
        st.write("♟️") # Logo yoksa piyon ikonu
with col2:
    st.title("Kurtköy Satranç ve Akıl Oyunları Spor Kulübü")
    st.caption("2026 - Turnuva Yönetim Sistemi")

st.divider()

# Yan Panel
with st.sidebar:
    st.header("Oyuncu İşlemleri")
    new_player_name = st.text_input("Oyuncu İsmi Girin")
    if st.button("Oyuncu Ekle"):
        if new_player_name and not any(p['name'] == new_player_name for p in st.session_state.players):
            st.session_state.players.append({
                'name': new_player_name, 
                'score': 0.0, 
                'opponents': [], 
                'buchholz': 0.0
            })
            st.success(f"{new_player_name} eklendi.")
    
    st.divider()
    if st.button("Turnuvayı Sıfırla"):
        st.session_state.clear()
        st.rerun()

# Ana Ekran
if not st.session_state.players:
    st.info("👈 Turnuvaya başlamak için sol panelden oyuncu ekleyin.")
else:
    calculate_buchholz()
    df = pd.DataFrame(st.session_state.players)
    df = df.sort_values(by=['score', 'buchholz'], ascending=[False, False]).reset_index(drop=True)
    df = df[['name', 'score', 'buchholz']]
    df.columns = ['İsim', 'Puan', 'Buchholz']
    
    st.subheader(f"📊 Puan Durumu (Tur: {st.session_state.rounds_played})")
    st.dataframe(df, use_container_width=True)

    st.divider()

    if not st.session_state.round_active:
        if len(st.session_state.players) >= 2:
            if st.button(f"{st.session_state.rounds_played + 1}. Tur Eşleşmelerini Oluştur", type="primary"):
                pairings, bye = generate_pairings()
                st.session_state.pairings = pairings
                st.session_state.bye_player = bye
                st.session_state.round_active = True
                st.rerun()
        else:
            st.warning("En az 2 oyuncu gerekli.")
    
    else:
        st.subheader(f"⚔️ {st.session_state.rounds_played + 1}. Tur Maçları")
        
        if st.session_state.bye_player:
            st.info(f"🛑 BAY GEÇEN (+1 Puan): **{st.session_state.bye_player['name']}**")

        results_submitted = []
        with st.form("match_results"):
            for i, match in enumerate(st.session_state.pairings):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1: st.write(f"⚪ {match['white']['name']}")
                with c2: res = st.selectbox("Sonuç", ["Seçiniz", "1-0 (Beyaz)", "0-1 (Siyah)", "Berabere"], key=f"m_{i}", label_visibility="collapsed")
                with c3: st.write(f"⚫ {match['black']['name']}")
                st.markdown("---")
                results_submitted.append(res)
            
            submit_btn = st.form_submit_button("Turu Tamamla")

        if submit_btn:
            if "Seçiniz" in results_submitted:
                st.error("Lütfen tüm sonuçları girin!")
            else:
                for i, match in enumerate(st.session_state.pairings):
                    w, b = match['white'], match['black']
                    result = results_submitted[i]
                    w['opponents'].append(b['name'])
                    b['opponents'].append(w['name'])
                    if "1-0" in result: w['score'] += 1.0
                    elif "0-1" in result: b['score'] += 1.0
                    else: 
                        w['score'] += 0.5
                        b['score'] += 0.5
                
                if st.session_state.bye_player:
                    st.session_state.bye_player['score'] += 1.0
                
                st.session_state.rounds_played += 1
                st.session_state.round_active = False
                st.session_state.pairings = []
                st.session_state.bye_player = None
                st.rerun()
