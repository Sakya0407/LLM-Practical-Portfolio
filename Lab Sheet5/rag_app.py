# Lab 5 task - Streamlit app: multiple PDFs + user uploads.  Run: streamlit run rag_app.py
import os, tempfile, streamlit as st
from rag_core import answer, ingest_pdf, ingest_folder, list_sources, DATA_DIR

st.set_page_config(page_title="University AI Assistant", page_icon="🎓")
st.title("🎓 University AI Assistant")
st.caption("Ask questions based on university documents")

with st.sidebar:
    st.header("Documents")
    if st.button("Ingest PDFs in ./data"):
        os.makedirs(DATA_DIR, exist_ok=True)
        existing = set(list_sources())
        new = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf") and f not in existing]
        with st.spinner("Indexing..."):
            for f in new:
                st.success(f"{f}: {ingest_pdf(os.path.join(DATA_DIR, f))} chunks")
        if not new: st.info("Nothing new to index.")

    ups = st.file_uploader("Upload your own PDFs", type="pdf", accept_multiple_files=True)
    if ups and st.button("Add uploaded PDFs"):
        existing = set(list_sources())
        for f in ups:
            if f.name in existing:
                st.info(f"{f.name} is already indexed."); continue
            path = os.path.join(tempfile.gettempdir(), f.name)
            open(path, "wb").write(f.getbuffer())
            with st.spinner(f"Indexing {f.name}..."):
                n = ingest_pdf(path)
            if n == 0: st.error(f"{f.name}: no text found (scanned PDF?)")
            else: st.success(f"{f.name}: {n} chunks")

    st.divider()
    sources = list_sources()
    st.write("**Indexed files:**", ", ".join(sources) if sources else "none yet")
    choice = st.selectbox("Search in", ["All documents"] + sources)

if "msgs" not in st.session_state: st.session_state.msgs = []
for m in st.session_state.msgs:
    st.chat_message(m["role"]).write(m["content"])
if q := st.chat_input("Ask your university question..."):
    st.chat_message("user").write(q); st.session_state.msgs.append({"role": "user", "content": q})
    with st.spinner("Thinking..."):
        a, s = answer(q, None if choice == "All documents" else choice)
    out = f"{a}\n\n*Sources: {', '.join(s)}*"
    st.chat_message("assistant").write(out); st.session_state.msgs.append({"role": "assistant", "content": out})
