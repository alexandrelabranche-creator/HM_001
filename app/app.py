#!/usr/bin/env python3
"""
Streamlit GUI (v4d):
- Preview renders on every change (reliable)
- Export snapshots
- Button to save current levels into the "state in use" (atomic write)
- Dirty flag indicator (saved vs unsaved)
- 🟥 TPK button: sets all levels to 6 and refreshes preview (joke button)

Run:
  pip install streamlit pillow numpy pandas
  streamlit run rothmorgil_heatmap_gui_streamlit_v4d_tpk_button.py
"""
from __future__ import annotations

import json
import os
import hashlib
from datetime import datetime
from typing import Dict

import pandas as pd
import streamlit as st

from heatmap_render_lib import render_from_state

DEFAULT_MAP = "MAP.jpg"
DEFAULT_STATE = "Rothmorgil_heatmap_state_cumulatif_v17_manualCenters.json"
OUT_DIR = "outputs_heatmap"

st.set_page_config(page_title="Doppelvelt — Chaos Heatmap", layout="wide")

# --- CSS: make PRIMARY button red (we reserve primary for TPK only) ---
st.markdown(
    """
<style>
/* Streamlit primary buttons */
button[kind="primary"]{
  background: #c62828 !important;
  border: 1px solid #8e1b1b !important;
}
button[kind="primary"]:hover{
  background: #b71c1c !important;
  border: 1px solid #7f1616 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Doppelvelt — Interface Chaos (Heatmap Rothmorgil)")
st.caption("Ajuste les niveaux (0–6). Aperçu auto à chaque changement + export + 💾 sauvegarde + indicateur (dirty) + 🟥 TPK.")

def stable_hash(levels: Dict[str, int]) -> str:
    items = sorted(levels.items(), key=lambda x: x[0].lower())
    s = "|".join([f"{k}={int(v)}" for k, v in items])
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

def load_state(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def atomic_write_json(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    write_json(tmp, data)
    os.replace(tmp, path)

def write_state_snapshot(state: dict, out_tag: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, f"state_{out_tag}.json")
    write_json(p, state)
    return p

def current_levels_from_df(df: pd.DataFrame) -> Dict[str, int]:
    return {row["Ville"]: int(row["Chaos (0-6)"]) for _, row in df.iterrows()}

# -------- Sidebar --------
with st.sidebar:
    st.header("Réglages")
    map_path = st.text_input("Chemin de la carte (MAP.jpg)", value=DEFAULT_MAP)
    state_path = st.text_input("Chemin du state JSON (en usage)", value=DEFAULT_STATE)
    auto_render = st.checkbox("Aperçu automatique", value=True)
    write_pdf = st.checkbox("PDF à l'export", value=True)

# -------- Load base state --------
try:
    state = load_state(state_path)
except Exception as e:
    st.error(f"Impossible de lire le state JSON: {e}")
    st.stop()

levels_file = state.get("levels", {})
cities = sorted(levels_file.keys(), key=lambda s: s.lower())
file_hash = stable_hash({k: int(v) for k, v in levels_file.items()})

# -------- Session State init --------
if "edited_df" not in st.session_state:
    st.session_state.edited_df = pd.DataFrame({"Ville": cities, "Chaos (0-6)": [int(levels_file[c]) for c in cities]})

if "last_preview_hash" not in st.session_state:
    st.session_state.last_preview_hash = ""
if "last_out" not in st.session_state:
    st.session_state.last_out = None
if "last_out_tag" not in st.session_state:
    st.session_state.last_out_tag = ""
if "last_snapshot" not in st.session_state:
    st.session_state.last_snapshot = ""

# Saved-hash tracking (dirty flag)
if "saved_hash" not in st.session_state:
    st.session_state.saved_hash = file_hash
if "saved_time" not in st.session_state:
    st.session_state.saved_time = state.get("last_saved_from_gui", {}).get("local_time", "")

# -------- Main Layout --------
left, right = st.columns([1.15, 1.0], gap="large")

with left:
    st.subheader("Édition des niveaux")
    edited = st.data_editor(
        st.session_state.edited_df,
        use_container_width=True,
        hide_index=True,
        key="editor",
        column_config={
            "Ville": st.column_config.TextColumn(disabled=True),
            "Chaos (0-6)": st.column_config.NumberColumn(min_value=0, max_value=6, step=1),
        },
    )
    if not edited.equals(st.session_state.edited_df):
        st.session_state.edited_df = edited

    c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1.2,1.4,0.9])
    with c1:
        if st.button("Tout à 0"):
            st.session_state.edited_df["Chaos (0-6)"] = 0
    with c2:
        if st.button("+1 partout"):
            st.session_state.edited_df["Chaos (0-6)"] = (st.session_state.edited_df["Chaos (0-6)"] + 1).clip(0, 6)
    with c3:
        if st.button("-1 partout"):
            st.session_state.edited_df["Chaos (0-6)"] = (st.session_state.edited_df["Chaos (0-6)"] - 1).clip(0, 6)
    with c4:
        preview_btn = st.button("🔄 Forcer aperçu")
    with c5:
        save_btn = st.button("💾 Sauvegarder state")  # secondary (default)
    with c6:
        tpk_btn = st.button("TPK", type="primary", help="Blague DM: met toutes les villes à 6/6.")

    if tpk_btn:
        st.session_state.edited_df["Chaos (0-6)"] = 6

    st.divider()
    st.subheader("Export (snapshot + fichiers)")
    export_tag = st.text_input("Tag d'export", value=datetime.now().strftime("export_%Y%m%d_%H%M%S"))
    export_btn = st.button("📦 Générer export")
    st.caption("Export écrit un snapshot + PNG/PDF dans outputs_heatmap/.")

def do_render(out_tag: str, write_pdf_flag: bool) -> dict:
    new_levels = current_levels_from_df(st.session_state.edited_df)
    state2 = dict(state)
    state2["levels"] = new_levels
    state2["generated_utc"] = datetime.utcnow().isoformat() + "Z"
    state2["last_gui_edit"] = {"tag": out_tag, "local_time": datetime.now().isoformat()}
    snap = write_state_snapshot(state2, out_tag)
    out = render_from_state(snap, map_path, OUT_DIR, out_tag, write_pdf=write_pdf_flag)
    out["state_snapshot"] = snap
    return out

# Dirty flag calculation
current_levels = current_levels_from_df(st.session_state.edited_df)
current_hash = stable_hash(current_levels)
dirty = (current_hash != st.session_state.saved_hash)

# Sidebar dirty indicator
with st.sidebar:
    st.divider()
    if dirty:
        st.markdown("### 🔴 Non sauvegardé")
        st.caption(f"Hash (actuel): `{current_hash}`")
        st.caption(f"Hash (sauvé): `{st.session_state.saved_hash}`")
    else:
        st.markdown("### 🟢 Sauvegardé")
        st.caption(f"Hash: `{current_hash}`")
    if st.session_state.saved_time:
        st.caption(f"Dernière sauvegarde: {st.session_state.saved_time}")

with right:
    st.subheader("Aperçu (heatmap)")
    st.caption(f"hash={current_hash} | preview={st.session_state.last_preview_hash or '—'}")

    # Auto preview render (every change)
    if auto_render and current_hash != st.session_state.last_preview_hash:
        with st.spinner("Rendu aperçu…"):
            out_tag = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_hash}"
            try:
                out = do_render(out_tag, write_pdf_flag=False)
                st.session_state.last_out = out
                st.session_state.last_out_tag = out_tag
                st.session_state.last_preview_hash = current_hash
                st.session_state.last_snapshot = out["state_snapshot"]
            except Exception as e:
                st.error(f"Erreur rendu aperçu: {e}")

    if preview_btn:
        with st.spinner("Rendu aperçu (forcé)…"):
            out_tag = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_hash}"
            try:
                out = do_render(out_tag, write_pdf_flag=False)
                st.session_state.last_out = out
                st.session_state.last_out_tag = out_tag
                st.session_state.last_preview_hash = current_hash
                st.session_state.last_snapshot = out["state_snapshot"]
            except Exception as e:
                st.error(f"Erreur rendu aperçu: {e}")

    if st.session_state.last_out:
        out = st.session_state.last_out
        st.image(open(out["on_map_png"], "rb").read(), use_container_width=True)
        st.caption(f"Dernier rendu: {st.session_state.last_out_tag}")
        st.caption(f"Dernier snapshot: {st.session_state.last_snapshot}")
    else:
        st.info("Aucun aperçu encore. Modifie une valeur (ou clique Forcer aperçu).")

# Save-to-state action
if save_btn:
    try:
        state_save = load_state(state_path)  # keep latest non-level fields
        state_save["levels"] = current_levels
        state_save["generated_utc"] = datetime.utcnow().isoformat() + "Z"
        state_save["last_saved_from_gui"] = {"local_time": datetime.now().isoformat(), "hash": current_hash}
        atomic_write_json(state_path, state_save)

        st.session_state.saved_hash = current_hash
        st.session_state.saved_time = state_save["last_saved_from_gui"]["local_time"]

        st.success(f"State sauvegardé: {state_path}")
    except Exception as e:
        st.error(f"Erreur sauvegarde state: {e}")

# Export action
if export_btn:
    try:
        with st.spinner("Génération export…"):
            out = do_render(export_tag, write_pdf_flag=write_pdf)
        st.success("Export généré.")
        st.caption(f"State snapshot: {out['state_snapshot']}")

        st.session_state.last_out = out
        st.session_state.last_out_tag = export_tag
        st.session_state.last_preview_hash = current_hash
        st.session_state.last_snapshot = out["state_snapshot"]
    except Exception as e:
        st.error(f"Erreur export: {e}")
