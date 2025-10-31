from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from .components import Metric, human_size, metrics_row
from .file_ops import delete_files, move_files, rename_file


DEFAULT_DATE_COLS = ["created_at", "modified_at", "accessed_at"]
DEFAULT_TEXT_COLS = ["path", "name", "stem", "suffix", "parent", "symlink_target"]
DEFAULT_BOOL_COLS = ["is_symlink", "is_hardlink"]
DEFAULT_NUM_COLS = ["size_count", "hash_count"]


def _ensure_datetime(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns and not pd.api.types.is_datetime64_any_dtype(df[c]):
            with pd.option_context("mode.chained_assignment", None):
                df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def _ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Ensure numeric columns are properly typed."""
    for c in cols:
        if c in df.columns:
            if not pd.api.types.is_numeric_dtype(df[c]):
                with pd.option_context("mode.chained_assignment", None):
                    df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _filters_ui(df: pd.DataFrame) -> dict[str, Any]:
    with st.expander("Filters", expanded=True):
        cols = st.columns(4)
        filt: dict[str, Any] = {}

        # Text contains filters
        with cols[0]:
            for c in DEFAULT_TEXT_COLS:
                if c in df.columns:
                    v = st.text_input(f"{c} contains")
                    if v:
                        filt.setdefault("text", []).append((c, v))

        # Numeric ranges
        with cols[1]:
            for c in DEFAULT_NUM_COLS:
                if c in df.columns:
                    s = pd.to_numeric(df[c], errors="coerce") if not df.empty else pd.Series(dtype=float)
                    s = s.dropna()
                    if s.empty:
                        continue
                    min_v = int(s.min())
                    max_v = int(s.max())
                    if min_v < max_v:
                        rng = st.slider(f"{c} range", min_value=min_v, max_value=max_v, value=(min_v, max_v))
                        filt.setdefault("numeric", {})[c] = rng
                    else:
                        st.caption(f"{c}: {min_v}")
                        filt.setdefault("numeric", {})[c] = (min_v, max_v)

        # Date ranges
        with cols[2]:
            for c in DEFAULT_DATE_COLS:
                if c in df.columns:
                    col = df[c]
                    if col.isna().all():
                        continue
                    dmin = col.min()
                    dmax = col.max()
                    if pd.isna(dmin) or pd.isna(dmax):
                        continue
                    if dmin < dmax:
                        date_range = st.date_input(f"{c} between", value=(dmin.date(), dmax.date()), key=f"date_filter_{c}")
                        # Handle both single date and tuple returns
                        if isinstance(date_range, tuple) and len(date_range) == 2:
                            d1, d2 = date_range
                            if d1 and d2:
                                filt.setdefault("date", {})[c] = (pd.Timestamp(d1), pd.Timestamp(d2) + pd.Timedelta(days=1))
                        elif isinstance(date_range, tuple) and len(date_range) == 1:
                            # User selected only one date, use it as both start and end
                            d1 = date_range[0]
                            if d1:
                                filt.setdefault("date", {})[c] = (pd.Timestamp(d1), pd.Timestamp(d1) + pd.Timedelta(days=1))
                    else:
                        st.caption(f"{c}: {dmin.date()}")
                        filt.setdefault("date", {})[c] = (pd.Timestamp(dmin.date()), pd.Timestamp(dmin.date()) + pd.Timedelta(days=1))

        # Booleans
        with cols[3]:
            for c in DEFAULT_BOOL_COLS:
                if c in df.columns:
                    tri = st.selectbox(f"{c}", ["Any", "True", "False"], index=0)
                    if tri != "Any":
                        filt.setdefault("bool", {})[c] = (tri == "True")

    return filt


def _apply_filters(df: pd.DataFrame, filt: dict[str, Any]) -> pd.DataFrame:
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)

    # Text contains
    for c, v in filt.get("text", []):
        if c in df.columns:
            mask &= df[c].astype(str).str.contains(v, case=False, na=False)

    # Numeric ranges
    for c, (lo, hi) in filt.get("numeric", {}).items():
        if c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            mask &= (s >= lo) & (s <= hi)

    # Dates
    for c, (d1, d2) in filt.get("date", {}).items():
        if c in df.columns:
            s = df[c]
            mask &= (s >= d1) & (s < d2)

    # Bools
    for c, val in filt.get("bool", {}).items():
        if c in df.columns:
            s = df[c].astype("boolean")
            mask &= (s == val)

    return df[mask]


def _render_metrics(df: pd.DataFrame) -> None:
    total = len(df)
    total_size = int(pd.to_numeric(df.get("size", pd.Series(dtype=int)), errors="coerce").sum()) if total else 0
    num_symlink = int(pd.to_numeric(df.get("is_symlink", pd.Series(dtype=int)), errors="coerce").fillna(0).sum())
    m = [
        Metric("Rows", f"{total:,}"),
        Metric("Total Size", human_size(total_size)),
        Metric("Symlinks", f"{num_symlink:,}"),
    ]
    st.markdown(metrics_row(m), unsafe_allow_html=True)


def _decorate_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "size" in out.columns:
        out["size_pretty"] = pd.to_numeric(out["size"], errors="coerce").fillna(0).astype(int).map(human_size)
    return out


def _aggrid(df: pd.DataFrame, grid_key=None, initial_page=0) -> dict:
    gob = GridOptionsBuilder.from_dataframe(df)
    gob.configure_selection("multiple", use_checkbox=False, pre_selected_rows=[])
    gob.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=25)
    gob.configure_default_column(filter=True, sortable=True, resizable=True, wrapText=False, autoHeight=False, minWidth=100, editable=False)
    
    # Configure important columns with proper widths
    width_map = {
        "path": (400, True),
        "name": (200, False),
        "stem": (150, False),
        "suffix": (80, False),
        "parent": (350, False),
        "size": (100, False),
        "hash": (280, False),  # Increased from 100 to fit hash on one line
        "hash_count": (90, False),
        "size_count": (90, False),
    }
    
    # Numeric columns that should be displayed as numbers
    numeric_cols = ["hash_count", "size_count"]
    
    # Default sort by hash
    if "hash" in df.columns:
        try:
            gob.configure_column("hash", sort="asc")
        except Exception:
            pass
    for col in df.columns:
        if col in width_map:
            width, pinned = width_map[col]
            # Configure numeric columns with proper type
            if col in numeric_cols:
                gob.configure_column(col, width=width, pinned="left" if pinned else False, filter=True, 
                                     wrapText=False, autoHeight=False, editable=False, type="numericColumn")
            else:
                gob.configure_column(col, width=width, pinned="left" if pinned else False, filter=True, 
                                     wrapText=False, autoHeight=False, editable=False)
        elif col in ["created_at", "modified_at", "accessed_at"]:
            gob.configure_column(col, width=140, wrapText=False, autoHeight=False, editable=False, type=["dateColumn", "dateFilter"])
        elif col in ["is_symlink", "is_hardlink"]:
            gob.configure_column(col, width=100, wrapText=False, autoHeight=False, editable=False, type="booleanColumn")
        elif col in numeric_cols:
            gob.configure_column(col, minWidth=120, wrapText=False, autoHeight=False, editable=False, type="numericColumn")
        else:
            gob.configure_column(col, minWidth=120, wrapText=False, autoHeight=False, editable=False)
    
    grid_options = gob.build()
    # Use stable row IDs so selection adheres to rows, not indices
    try:
        grid_options["getRowId"] = JsCode("function(params) { return params.data.path; }")
    except Exception:
        pass
    # Initialize current page if possible
    if initial_page and isinstance(initial_page, int):
        grid_options['pagination'] = True
        grid_options['paginationCurrentPage'] = initial_page
    # Ensure rowSelection is set
    grid_options["rowSelection"] = "multiple"
    grid_options["rowMultiSelectWithClick"] = True
    # Enable text selection in cells
    grid_options["enableCellTextSelection"] = True
    grid_options["ensureDomOrder"] = True
    grid_options["suppressRowClickSelection"] = False
    grid_options["suppressCellFocus"] = False
    
    return AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,  # Changed from SELECTION_CHANGED
        data_return_mode="FILTERED_AND_SORTED",
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=False,
        height=600,
        allow_unsafe_jscode=True,
        reload_data=st.session_state.pop('file_browser_grid_reload', False),
        key=grid_key if grid_key is not None else "file_browser_grid",
    )


def _actions_ui(selected_paths: list[str], df: pd.DataFrame, main_df_key: str) -> None:
    """Actions UI - updates main dataframe in session state."""
    st.subheader("Actions")
    if not selected_paths:
        st.info("Select rows to enable actions")
        return

    cols = st.columns([1, 1, 1, 3])

    with cols[0]:
        st.caption("Delete")
        dry = st.toggle("Dry-run", value=st.session_state.get("delete_dry", False), key="delete_dry")
        if st.button("Delete selected", type="primary"):
            res = delete_files(selected_paths, dry_run=dry)
            # Show results
            for r in res:
                if r.success:
                    st.success(f"✓ {str(r.path)}: {r.message}")
                else:
                    st.error(f"✗ {str(r.path)}: {r.message}")
            # Remove successfully deleted files from main dataframe in session state
            if not dry:
                successful_paths = {str(r.path) for r in res if r.success}
                if successful_paths and main_df_key in st.session_state and "path" in st.session_state[main_df_key].columns:
                    before_count = len(st.session_state[main_df_key])
                    # Normalize paths for comparison (convert to strings, strip)
                    main_df = st.session_state[main_df_key].copy()
                    main_df["path_str"] = main_df["path"].astype(str).str.strip()
                    successful_paths_normalized = {p.strip() for p in successful_paths}
                    mask = ~main_df["path_str"].isin(successful_paths_normalized)
                    st.session_state[main_df_key] = main_df[mask].drop(columns=["path_str"])
                    after_count = len(st.session_state[main_df_key])
                    removed_count = before_count - after_count
                    st.success(f"Removed {removed_count} file(s) from view")
                    # Flag grid to reload data to clear selection on next render
                    st.session_state['file_browser_grid_reload'] = True
                    st.session_state.selected_rows_cache = []
                    # Only reset grid_key if really wanted
                    # st.session_state.file_browser_grid_key = f"file_browser_grid_{uuid.uuid4()}"
                    st.rerun()

    with cols[1]:
        st.caption("Move")
        dest = st.text_input("Destination dir", key="move_dest", value="/home/md/temp/", placeholder="/path/to/dir")
        dry2 = st.toggle("Dry-run ", value=st.session_state.get("move_dry", False), key="move_dry")
        btn_move = st.button("Move selected")
        if btn_move and dest and isinstance(dest, str):
            res = move_files(selected_paths, dest, dry_run=dry2)
            st.write([{ "path": str(r.path), "ok": r.success, "msg": r.message } for r in res])
            # Remove successfully moved files from main dataframe in session state (moved = no longer at original path)
            if not dry2:
                successful_paths = {str(r.path) for r in res if r.success}
                if successful_paths and main_df_key in st.session_state and "path" in st.session_state[main_df_key].columns:
                    before_count = len(st.session_state[main_df_key])
                    # Normalize paths for comparison (convert to strings, strip)
                    main_df = st.session_state[main_df_key].copy()
                    main_df["path_str"] = main_df["path"].astype(str).str.strip()
                    successful_paths_normalized = {p.strip() for p in successful_paths}
                    mask = ~main_df["path_str"].isin(successful_paths_normalized)
                    st.session_state[main_df_key] = main_df[mask].drop(columns=["path_str"])
                    after_count = len(st.session_state[main_df_key])
                    removed_count = before_count - after_count
                    st.success(f"Removed {removed_count} file(s) from view (moved)")
                    st.session_state['file_browser_grid_reload'] = True
                    st.session_state.selected_rows_cache = []
                    # Only reset grid_key if really wanted
                    # st.session_state.file_browser_grid_key = f"file_browser_grid_{uuid.uuid4()}"
                    st.rerun()

    with cols[2]:
        st.caption("Rename (single)")
        if len(selected_paths) == 1:
            new_name = st.text_input("New name", key="rename_new")
            dry3 = st.toggle("Dry-run  ", value=True, key="rename_dry")
            btn_rename = st.button("Rename")
            if btn_rename and new_name and isinstance(new_name, str):
                r = rename_file(selected_paths[0], new_name, dry_run=dry3)
                st.write({ "path": str(r.path), "ok": r.success, "msg": r.message })
        else:
            st.info("Select exactly one row to rename")

    with cols[3]:
        st.caption("Selection summary")
        try:
            if "path" in df.columns and len(selected_paths) > 0:
                mask = df["path"].isin(selected_paths)
                if isinstance(mask, pd.Series):
                    sel_df = df[mask]
                    if len(sel_df) > 0:
                        total_sel = len(sel_df)
                        sel_size = int(pd.to_numeric(sel_df.get("size", pd.Series(dtype=int)), errors="coerce").sum()) if "size" in sel_df.columns else 0
                        st.markdown(metrics_row([Metric("Selected", f"{total_sel}"), Metric("Size", human_size(sel_size))]), unsafe_allow_html=True)
                    else:
                        st.caption(f"{len(selected_paths)} selected")
                else:
                    st.caption(f"{len(selected_paths)} selected")
            else:
                st.caption(f"{len(selected_paths)} selected")
        except Exception as e:
            st.caption(f"{len(selected_paths)} selected")
            st.error(f"Error: {e}")


def run_file_browser(df: pd.DataFrame) -> None:
    try:
        st.set_page_config(page_title="Neat FS Browser", layout="wide", page_icon="🧭")
    except Exception:
        pass  # Already set

    st.title("Neat FS File Browser")
    
    # Debug toggle in sidebar
    with st.sidebar:
        debug_mode = st.checkbox("Debug mode", value=False, key="debug_aggrid_mode")
        if debug_mode:
            st.session_state["_debug_aggrid"] = True
        else:
            st.session_state["_debug_aggrid"] = False
    
    # Use session state to persist dataframe modifications (deletions, moves)
    df_key = "file_browser_main_df"
    # Always initialize from input df if not in session state
    if df_key not in st.session_state:
        st.session_state[df_key] = df.copy()
    
    # Always use the dataframe from session state
    df = st.session_state[df_key].copy()
    df = _ensure_datetime(df, [c for c in DEFAULT_DATE_COLS if c in df.columns])
    numeric_cols = ["hash_count", "size_count"]
    # Only keep explicitly allowed columns, but always keep 'size' up to _decorate_df
    allowed = set(DEFAULT_TEXT_COLS + DEFAULT_BOOL_COLS + DEFAULT_NUM_COLS + DEFAULT_DATE_COLS + ["hash", "size", "size_pretty"])
    keep_cols = [c for c in df.columns if c in allowed]
    df = df[keep_cols]
    df = _ensure_numeric(df, [c for c in numeric_cols + ["size"] if c in df.columns])
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    _render_metrics(df)
    filt = _filters_ui(df)
    filtered = _apply_filters(df, filt)
    decorated = _decorate_df(filtered)
    # Remove raw size, show pretty size as 'size'
    if "size" in decorated.columns:
        decorated = decorated.drop(columns=["size"])
    if "size_pretty" in decorated.columns:
        decorated = decorated.rename(columns={"size_pretty": "size"})
    # Preferred order: path, size, hash_count, hash, then rest
    preferred = ["path", "size", "hash_count", "hash"]
    existing_pref = [c for c in preferred if c in decorated.columns]
    remaining = [c for c in decorated.columns if c not in existing_pref]
    decorated = decorated[existing_pref + remaining]

    # Ensure numeric columns are numeric for grid
    for col in ["hash_count", "size_count"]:
        if col in decorated.columns:
            decorated[col] = pd.to_numeric(decorated[col], errors="coerce").astype(float)

    # Primary grid
    st.subheader("Files")
    if "file_browser_grid_key" not in st.session_state:
        st.session_state.file_browser_grid_key = "file_browser_grid"
    grid_key = st.session_state.file_browser_grid_key
    grid_result = _aggrid(
        decorated,
        grid_key=grid_key,
        initial_page=st.session_state.get("file_browser_grid_page", 0),
    )
    if "file_browser_grid_page" in st.session_state:
        del st.session_state["file_browser_grid_page"]

    # Maintain a cache for selected rows across renders
    if "selected_rows_cache" not in st.session_state:
        st.session_state.selected_rows_cache = []

    # Extract selected rows from AgGrid result
    sel = []
    if hasattr(grid_result, "selected_rows"):
        sel = grid_result.selected_rows
        if isinstance(sel, pd.DataFrame):
            sel = sel.to_dict("records")
        elif not isinstance(sel, list):
            sel = []
    elif isinstance(grid_result, dict) and "selected_rows" in grid_result:
        sel = grid_result.get("selected_rows") or []
    if isinstance(sel, pd.DataFrame):
        sel = sel.to_dict("records")

    # Always overwrite selection cache (even if empty) to avoid stale selections
    st.session_state.selected_rows_cache = sel if isinstance(sel, list) else []
    sel = st.session_state.selected_rows_cache

    # Extract paths
    selected_paths: list[str] = []
    for r in sel or []:
        if isinstance(r, dict):
            pv = r.get("path") or r.get("Path") or r.get("PATH")
            if isinstance(pv, str) and pv.strip():
                selected_paths.append(pv.strip())

    # Filter out any stale/invalid paths (extra safety)
    if "path" in filtered.columns:
        valid_paths = set(filtered["path"].astype(str))
        selected_paths = [p for p in selected_paths if p in valid_paths]

    # Status
    c1, _ = st.columns([1, 3])
    with c1:
        if selected_paths:
            st.success(f"\u2713 {len(selected_paths)} file(s) selected")
        else:
            st.info("0 files selected")

    # Actions
    _actions_ui(selected_paths, filtered, df_key)