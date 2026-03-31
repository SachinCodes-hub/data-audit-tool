st.markdown(f"""
    <div style='margin-bottom: 24px'>
        <div style='font-family: "JetBrains Mono", monospace; font-size: 11px;
                    color: #3b82f6; letter-spacing: 0.1em; margin-bottom: 6px'>
            DATASET OVERVIEW
        </div>
        <div style='display: flex; align-items: center; gap: 12px'>
            <span style='font-family: "JetBrains Mono", monospace; font-size: 13px;
                         color: #ededed; font-weight: 600'>{file_name}</span>
            <span class='stat-pill'>{file_size:,} bytes</span>
            <span class='stat-pill'>{df.shape[0]:,} rows</span>
            <span class='stat-pill'>{df.shape[1]} cols</span>
        </div>
    </div>
    """, unsafe_allow_html=True)