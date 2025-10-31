#!/usr/bin/env python3
"""Streamlit entry point for the file browser GUI."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from neat_fs.gui.streamlit_app import run_file_browser


def main():
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            st.error(f"CSV file not found: {csv_path}")
            st.stop()
        df = pd.read_csv(csv_path, low_memory=False)
        run_file_browser(df)
    else:
        st.set_page_config(page_title="Neat FS Browser", layout="wide", page_icon="🧭")
        
        st.sidebar.header("Load Data")
        uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
        csv_path = st.sidebar.text_input("Or enter CSV path", value="./data/hashed_duplicates.csv")
        
        # Use session state to cache the DataFrame
        df_key = "file_browser_df"
        df_source_key = "file_browser_df_source"
        
        # Check if we need to reload
        current_source = None
        if uploaded_file is not None:
            current_source = ("upload", uploaded_file.name)
        elif csv_path and csv_path.strip():
            path = Path(csv_path)
            if path.exists():
                current_source = ("file", str(path.resolve()))
        
        # Load DataFrame if source changed or not in cache
        if current_source and current_source != st.session_state.get(df_source_key):
            try:
                if uploaded_file is not None:
                    df = pd.read_csv(uploaded_file, low_memory=False)
                    st.session_state[df_key] = df
                    st.session_state[df_source_key] = current_source
                    st.session_state["csv_file_path"] = None  # Can't save back to uploaded file
                elif csv_path and csv_path.strip():
                    path = Path(csv_path)
                    if path.exists():
                        df = pd.read_csv(path, low_memory=False)
                        st.session_state[df_key] = df
                        st.session_state[df_source_key] = current_source
                        st.session_state["csv_file_path"] = str(path.resolve())  # Store absolute path for saving
                    else:
                        st.error(f"File not found: {csv_path}")
                        if df_key in st.session_state:
                            del st.session_state[df_key]
                            del st.session_state[df_source_key]
            except Exception as e:
                st.error(f"Error loading file: {e}")
                if df_key in st.session_state:
                    del st.session_state[df_key]
                    del st.session_state[df_source_key]
        
        # Display the browser if we have data
        if df_key in st.session_state:
            # Add save button if we have a CSV file path
            csv_file_path = st.session_state.get("csv_file_path")
            if csv_file_path:
                # The browser uses "file_browser_main_df" internally
                browser_df_key = "file_browser_main_df"
                col1, col2 = st.columns([6, 1])
                with col2:
                    if st.button("💾 Save to CSV", type="primary"):
                        try:
                            # Save from the browser's session state (where updates are stored)
                            if browser_df_key in st.session_state:
                                st.session_state[browser_df_key].to_csv(csv_file_path, index=False)
                                st.success(f"Saved to {csv_file_path}")
                            else:
                                # Fallback to original if browser hasn't initialized yet
                                st.session_state[df_key].to_csv(csv_file_path, index=False)
                                st.success(f"Saved to {csv_file_path}")
                        except Exception as e:
                            st.error(f"Error saving: {e}")
            run_file_browser(st.session_state[df_key])
        else:
            st.info("Upload a CSV file or enter a path to get started")


if __name__ == "__main__":
    main()

