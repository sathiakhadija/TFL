import html
import os
from datetime import datetime

import dotenv
import pandas as pd
import plotly.graph_objects as go
import psycopg2
import streamlit as st
import streamlit.components.v1 as components


def inject_css():
    """Inject complete futuristic TfL operations centre CSS design system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
          --tfl-red:        #DC241F;
          --tfl-blue:       #003B8E;
          --eng-white:      #FFFFFF;
          --eng-red:        #CF142B;
          --dark-bg:        #060810;
          --dark-surface:   #0D1117;
          --dark-surface2:  #111827;
          --dark-border:    #1C2333;
          --dark-muted:     #4B5563;
          --dark-muted2:    #6B7280;
          --health-good:    #00C853;
          --health-minor:   #FFD600;
          --health-severe:  #FF3D00;
          --health-susp:    #212121;
          --glow-red:       rgba(220, 36, 31, 0.4);
          --glow-blue:      rgba(0, 59, 142, 0.4);
          --glow-green:     rgba(0, 200, 83, 0.4);
        }

        /* Hide Streamlit chrome */
        header[data-testid="stHeader"],
        footer, #MainMenu,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
          display: none !important;
        }

        /* Page base */
        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stApp {
          background: var(--dark-bg) !important;
          color: var(--eng-white) !important;
          font-family: 'Inter', sans-serif;
        }

        /* Scanline texture overlay */
        [data-testid="stAppViewContainer"]::before {
          content: '';
          position: fixed;
          top: 0; left: 0;
          width: 100%; height: 100%;
          background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 0, 0, 0.03) 2px,
            rgba(0, 0, 0, 0.03) 4px
          );
          pointer-events: none;
          z-index: 9999;
        }

        /* Ambient background glow */
        [data-testid="stMain"]::before {
          content: '';
          position: fixed;
          top: -30%;
          left: -10%;
          width: 60%;
          height: 60%;
          background: radial-gradient(
            ellipse at center,
            rgba(0, 59, 142, 0.08) 0%,
            transparent 70%
          );
          pointer-events: none;
          z-index: 0;
        }

        [data-testid="stMain"]::after {
          content: '';
          position: fixed;
          bottom: -20%;
          right: -10%;
          width: 50%;
          height: 50%;
          background: radial-gradient(
            ellipse at center,
            rgba(220, 36, 31, 0.06) 0%,
            transparent 70%
          );
          pointer-events: none;
          z-index: 0;
        }

        /* Block container */
        .block-container {
          padding-top: 0 !important;
          padding-bottom: 60px;
          max-width: 1600px;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
          background: #080C14 !important;
          border-right: 1px solid var(--dark-border);
        }
        [data-testid="stSidebar"] > div {
          padding-top: 0;
        }

        /* Typography */
        h1, h2, h3, .times {
          font-family: 'Times New Roman', serif !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--dark-bg); }
        ::-webkit-scrollbar-thumb {
          background: var(--dark-border);
          border-radius: 999px;
        }
        ::-webkit-scrollbar-thumb:hover { background: #2D3748; }

        /* ── Header ── */
        .tfl-header {
          background: linear-gradient(
            180deg,
            #0D1117 0%,
            rgba(13, 17, 23, 0) 100%
          );
          border-bottom: 1px solid var(--dark-border);
          padding: 24px 32px 20px;
          position: relative;
          margin-bottom: 8px;
        }

        .tfl-header::after {
          content: '';
          position: absolute;
          bottom: -1px;
          left: 0;
          width: 100%;
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent 0%,
            var(--tfl-red) 30%,
            var(--tfl-blue) 70%,
            transparent 100%
          );
        }

        .header-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 20px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .brand-text h1 {
          font-family: 'Times New Roman', serif !important;
          font-size: 32px;
          font-weight: 700;
          color: var(--eng-white);
          margin: 0 0 4px;
          letter-spacing: -0.5px;
        }

        .brand-text p {
          font-size: 11px;
          font-weight: 600;
          color: var(--dark-muted2);
          text-transform: uppercase;
          letter-spacing: 0.15em;
          margin: 0;
        }

        .live-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(220, 36, 31, 0.08);
          border: 1px solid rgba(220, 36, 31, 0.3);
          border-radius: 6px;
          padding: 10px 16px;
          backdrop-filter: blur(8px);
        }

        .live-dot {
          width: 8px;
          height: 8px;
          background: var(--tfl-red);
          border-radius: 50%;
          animation: pulseDot 1.6s ease-in-out infinite;
        }

        .live-label {
          font-size: 11px;
          font-weight: 800;
          color: var(--tfl-red);
          letter-spacing: 0.15em;
        }

        .live-time {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          color: var(--dark-muted2);
        }

        /* ── KPI Strip ── */
        .kpi-strip {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1px;
          background: var(--dark-border);
          border-radius: 8px;
          overflow: hidden;
          margin-top: 0;
        }

        .kpi-item {
          background: var(--dark-surface);
          padding: 16px 20px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          position: relative;
          transition: background 0.2s ease;
        }

        .kpi-item::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 2px;
          background: var(--kpi-color, var(--tfl-blue));
          opacity: 0.8;
        }

        .kpi-item:hover { background: var(--dark-surface2); }

        .kpi-value {
          font-family: 'Times New Roman', serif;
          font-size: 28px;
          font-weight: 700;
          color: var(--kpi-color, var(--eng-white));
          line-height: 1;
        }

        .kpi-label {
          font-size: 11px;
          font-weight: 600;
          color: var(--dark-muted2);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        /* ── Section heading ── */
        .section-heading {
          display: flex;
          align-items: center;
          gap: 14px;
          margin: 32px 0 16px;
          padding-left: 2px;
        }

        .section-bar {
          width: 3px;
          height: 24px;
          background: var(--tfl-red);
          border-radius: 999px;
          animation: pulseBar 2s ease-in-out infinite;
          flex-shrink: 0;
        }

        .section-title {
          font-family: 'Times New Roman', serif !important;
          font-size: 20px;
          font-weight: 700;
          color: var(--eng-white);
          margin: 0;
          letter-spacing: -0.3px;
        }

        .section-count {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          color: var(--dark-muted);
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 4px;
          padding: 2px 8px;
          margin-left: auto;
        }

        /* ── Line cards ── */
        .cards-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
          margin-bottom: 8px;
        }

        .line-card {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 10px;
          padding: 18px 16px 16px;
          position: relative;
          overflow: hidden;
          cursor: default;
          animation: fadeInUp 0.5s ease both;
          animation-delay: var(--card-delay, 0s);
          transition: transform 0.2s ease, box-shadow 0.2s ease,
                      border-color 0.2s ease;
        }

        /* Accent bar at top of card */
        .line-card::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 3px;
          background: var(--line-accent);
        }

        /* Ambient glow behind card */
        .line-card::after {
          content: '';
          position: absolute;
          top: -40px; left: -40px;
          width: 120px; height: 120px;
          background: radial-gradient(
            ellipse,
            var(--line-glow) 0%,
            transparent 70%
          );
          pointer-events: none;
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .line-card:hover {
          transform: translateY(-3px);
          border-color: var(--line-accent);
          box-shadow: 0 0 0 1px var(--line-accent),
                      0 8px 32px rgba(0,0,0,0.4),
                      0 0 40px var(--line-glow);
        }

        .line-card:hover::after { opacity: 1; }

        .card-line-name {
          font-family: 'Times New Roman', serif;
          font-size: 15px;
          font-weight: 700;
          color: var(--eng-white);
          margin-bottom: 12px;
          line-height: 1.2;
        }

        .card-score {
          font-family: 'Times New Roman', serif;
          font-size: 52px;
          font-weight: 700;
          line-height: 0.9;
          margin-bottom: 12px;
          color: var(--score-colour);
          text-shadow: 0 0 20px var(--score-glow);
        }

        .card-badge {
          display: inline-flex;
          align-items: center;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          padding: 4px 10px;
          border-radius: 4px;
          background: var(--badge-bg);
          color: var(--badge-fg);
          border: 1px solid var(--badge-border);
          margin-bottom: 10px;
        }

        .card-meta {
          font-family: 'JetBrains Mono', monospace;
          font-size: 10px;
          color: var(--dark-muted);
          margin-top: 6px;
        }

        /* Card background line tint */
        .card-bg-tint {
          position: absolute;
          bottom: 0; right: 0;
          width: 80px; height: 80px;
          background: radial-gradient(
            ellipse at bottom right,
            var(--line-tint) 0%,
            transparent 70%
          );
          pointer-events: none;
        }

        /* ── Chart panels ── */
        .chart-panel {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 10px;
          padding: 20px;
          margin-bottom: 16px;
          transition: border-color 0.2s ease;
        }

        .chart-panel:hover {
          border-color: rgba(220, 36, 31, 0.3);
        }

        .chart-panel-title {
          font-family: 'Times New Roman', serif;
          font-size: 17px;
          font-weight: 700;
          color: var(--eng-white);
          margin: 0 0 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--dark-border);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        /* ── Station table ── */
        .stn-wrap {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 10px;
          overflow: hidden;
          height: 100%;
        }

        .stn-header {
          background: var(--tfl-blue);
          padding: 14px 16px;
          font-family: 'Times New Roman', serif;
          font-size: 17px;
          font-weight: 700;
          color: var(--eng-white);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .stn-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }

        .stn-table th {
          background: rgba(0, 59, 142, 0.4);
          color: var(--dark-muted2);
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          padding: 10px 12px;
          text-align: left;
          border-bottom: 1px solid var(--dark-border);
        }

        .stn-table td {
          padding: 10px 12px;
          border-bottom: 1px solid rgba(28, 35, 51, 0.5);
          color: var(--eng-white);
          vertical-align: middle;
        }

        .stn-table tr:hover td {
          background: rgba(255, 255, 255, 0.02);
        }

        .stn-rank {
          font-family: 'Times New Roman', serif;
          font-size: 16px;
          font-weight: 700;
          color: var(--dark-muted2);
        }

        .stn-name {
          font-weight: 500;
          font-size: 12px;
        }

        .stn-count {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          color: var(--dark-muted2);
        }

        .grade-pill {
          display: inline-flex;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          padding: 3px 8px;
          border-radius: 4px;
        }

        /* ── Sidebar control panel ── */
        .ctrl-panel-title {
          font-family: 'Times New Roman', serif;
          font-size: 13px;
          font-weight: 700;
          color: var(--dark-muted2);
          text-transform: uppercase;
          letter-spacing: 0.15em;
          padding: 20px 16px 12px;
          border-bottom: 1px solid var(--dark-border);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ctrl-panel-title::before {
          content: '';
          width: 3px;
          height: 14px;
          background: var(--tfl-red);
          border-radius: 999px;
          flex-shrink: 0;
        }

        .line-row {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px 16px;
          border-bottom: 1px solid rgba(28,35,51,0.5);
          transition: background 0.15s ease;
        }

        .line-row:hover {
          background: rgba(255,255,255,0.02);
        }

        .line-indicator {
          width: 3px;
          height: 28px;
          border-radius: 999px;
          flex-shrink: 0;
        }

        .line-info {
          flex: 1;
          min-width: 0;
        }

        .line-info-name {
          font-size: 12px;
          font-weight: 600;
          color: var(--eng-white);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .line-info-status {
          font-size: 10px;
          color: var(--dark-muted);
          margin-top: 2px;
        }

        .line-score-badge {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          color: var(--score-colour);
          background: rgba(0,0,0,0.3);
          border: 1px solid var(--dark-border);
          border-radius: 4px;
          padding: 2px 7px;
          flex-shrink: 0;
        }

        .refresh-panel {
          margin: 12px 16px;
          background: var(--dark-surface2);
          border: 1px solid var(--dark-border);
          border-radius: 8px;
          padding: 12px 14px;
        }

        .refresh-label {
          font-size: 10px;
          font-weight: 700;
          color: var(--dark-muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 6px;
        }

        .refresh-bar-wrap {
          background: var(--dark-border);
          border-radius: 999px;
          height: 3px;
          overflow: hidden;
          margin-bottom: 6px;
        }

        .refresh-bar {
          height: 3px;
          background: linear-gradient(
            90deg, var(--tfl-red), var(--tfl-blue)
          );
          border-radius: 999px;
          transition: width 1s linear;
        }

        .refresh-countdown {
          font-family: 'JetBrains Mono', monospace;
          font-size: 13px;
          font-weight: 600;
          color: var(--eng-white);
        }

        .empty-state,
        .error-state {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-left: 3px solid var(--tfl-red);
          border-radius: 10px;
          color: var(--eng-white);
          font-size: 13px;
          padding: 16px;
        }

        @media (max-width: 1100px) {
          .cards-grid { grid-template-columns: repeat(2, 1fr); }
          .kpi-strip { grid-template-columns: repeat(2, 1fr); }
          .header-top { align-items: flex-start; flex-direction: column; }
        }

        @media (max-width: 720px) {
          .cards-grid { grid-template-columns: 1fr; }
          .kpi-strip { grid-template-columns: 1fr; }
          .tfl-header { padding: 20px 16px; }
          .brand-text h1 { font-size: 26px; }
        }

        /* ── Animations ── */
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulseDot {
          0%   { box-shadow: 0 0 0 0 rgba(220,36,31,0.7); transform: scale(0.95); }
          70%  { box-shadow: 0 0 0 8px rgba(220,36,31,0); transform: scale(1); }
          100% { box-shadow: 0 0 0 0 rgba(220,36,31,0); transform: scale(0.95); }
        }

        @keyframes pulseBar {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }

        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position:  200% 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

LINE_COLOURS = {
    "bakerloo": "#894E24",
    "central": "#DC241F",
    "circle": "#FFCE00",
    "district": "#007229",
    "elizabeth": "#6A1B9A",
    "hammersmith-city": "#F4A9BE",
    "jubilee": "#6A7278",
    "metropolitan": "#9B0058",
    "northern": "#000000",
    "piccadilly": "#000F9F",
    "victoria": "#00A0E2",
    "waterloo-city": "#00BDA8",
}

NAME_TO_COLOUR = {
    "Bakerloo": "#894E24",
    "Central": "#DC241F",
    "Circle": "#FFCE00",
    "District": "#007229",
    "Elizabeth Line": "#6A1B9A",
    "Hammersmith & City": "#F4A9BE",
    "Jubilee": "#6A7278",
    "Metropolitan": "#9B0058",
    "Northern": "#000000",
    "Piccadilly": "#000F9F",
    "Victoria": "#00A0E2",
    "Waterloo & City": "#00BDA8",
}

TFL_RED = "#DC241F"
TFL_BLUE = "#003B8E"
ENG_WHITE = "#FFFFFF"
DARK_BG = "#060810"
DARK_SURFACE = "#0D1117"
DARK_SURFACE2 = "#111827"
DARK_BORDER = "#1C2333"
DARK_MUTED = "#4B5563"
DARK_MUTED2 = "#6B7280"
HEALTH_GOOD = "#00C853"
HEALTH_MINOR = "#FFD600"
HEALTH_SEVERE = "#FF3D00"
HEALTH_SUSP = "#212121"


def get_db_connection():
    """Establish PostgreSQL database connection with error handling."""
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "tfl_pipeline"),
            user=os.getenv("POSTGRES_USER", "tfl_user"),
            password=os.getenv("POSTGRES_PASSWORD", "tfl_password"),
            connect_timeout=10,
        )
    except Exception as exc:
        raise ConnectionError(
            "Could not connect to PostgreSQL. Check POSTGRES_HOST, "
            "POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD."
        ) from exc


def load_line_performance(conn) -> pd.DataFrame:
    """Load line performance metrics from marts table."""
    query = """
        SELECT DISTINCT ON (line_id)
          line_id, line_name, avg_severity, max_severity,
          health_score, service_status, disruption_rate_pct,
          ingested_hour
        FROM marts.mart_line_performance
        ORDER BY line_id, ingested_hour DESC
    """
    return pd.read_sql_query(query, conn)


def load_disruption_trends(conn) -> pd.DataFrame:
    """Load disruption trend analysis by line."""
    query = """
        SELECT line_name,
               SUM(disruption_rate_pct) as total_disruption_rate,
               AVG(avg_severity) as avg_severity,
               MAX(peak_severity) as peak_severity
        FROM marts.mart_disruption_trends
        GROUP BY line_name
        ORDER BY total_disruption_rate DESC
    """
    return pd.read_sql_query(query, conn)


def load_station_reliability(conn) -> pd.DataFrame:
    """Load station reliability grades and disruption metrics."""
    query = """
        SELECT station_name, total_disruptions,
               avg_daily_disruptions, disruption_rank,
               reliability_grade
        FROM marts.mart_station_reliability
        ORDER BY disruption_rank ASC
    """
    return pd.read_sql_query(query, conn)


def load_raw_volume(conn) -> pd.DataFrame:
    """Load ingestion volume data aggregated by hour."""
    query = """
        SELECT DATE_TRUNC('hour', ingested_at) as hour,
               COUNT(*) as row_count
        FROM raw.line_status
        GROUP BY 1
        ORDER BY 1 ASC
    """
    return pd.read_sql_query(query, conn)


def get_health_color(service_status: str) -> str:
    """Map service status to health indicator colour."""
    normalized = (service_status or "").strip().lower()
    if normalized == "good":
        return HEALTH_GOOD
    if normalized == "minor issues":
        return HEALTH_MINOR
    if normalized == "severe disruption":
        return HEALTH_SEVERE
    if normalized == "suspended":
        return HEALTH_SUSP
    return DARK_MUTED2


def hex_to_rgba(hex_colour: str, alpha: float) -> str:
    """Convert hex colour to rgba with specified alpha."""
    clean = hex_colour.strip().lstrip("#")
    if len(clean) != 6:
        return f"rgba(75,85,99,{alpha})"
    try:
        red = int(clean[0:2], 16)
        green = int(clean[2:4], 16)
        blue = int(clean[4:6], 16)
        return f"rgba({red},{green},{blue},{alpha})"
    except ValueError:
        return f"rgba(75,85,99,{alpha})"


def get_line_colour(line_id: str) -> str:
    """Get TfL line colour by line ID."""
    line_id_clean = str(line_id or "").lower().strip()
    return LINE_COLOURS.get(line_id_clean, DARK_MUTED)


def get_badge_style(service_status: str) -> tuple:
    """Get badge background, border, and text colour by status."""
    normalized = (service_status or "").strip().lower()
    if normalized == "good":
        return "rgba(0,200,83,0.15)", HEALTH_GOOD, HEALTH_GOOD
    if normalized == "minor issues":
        return "rgba(255,214,0,0.15)", HEALTH_MINOR, HEALTH_MINOR
    if normalized == "severe disruption":
        return "rgba(255,61,0,0.15)", HEALTH_SEVERE, HEALTH_SEVERE
    if normalized == "suspended":
        return HEALTH_SUSP, "#333333", "#666666"
    return DARK_BORDER, "#2D3748", DARK_MUTED2


def get_score_glow(score_colour: str) -> str:
    """Get glow colour effect for score based on health colour."""
    if score_colour == HEALTH_GOOD:
        return "rgba(0,200,83,0.5)"
    if score_colour == HEALTH_MINOR:
        return "rgba(255,214,0,0.5)"
    if score_colour == HEALTH_SEVERE:
        return "rgba(255,61,0,0.5)"
    return "rgba(0,0,0,0)"


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
          --tfl-red:        #DC241F;
          --tfl-blue:       #003B8E;
          --eng-white:      #FFFFFF;
          --eng-red:        #CF142B;
          --dark-bg:        #060810;
          --dark-surface:   #0D1117;
          --dark-surface2:  #111827;
          --dark-border:    #1C2333;
          --dark-muted:     #4B5563;
          --dark-muted2:    #6B7280;
          --health-good:    #00C853;
          --health-minor:   #FFD600;
          --health-severe:  #FF3D00;
          --health-susp:    #212121;
          --glow-red:       rgba(220, 36, 31, 0.4);
          --glow-blue:      rgba(0, 59, 142, 0.4);
          --glow-green:     rgba(0, 200, 83, 0.4);
        }

        /* Hide Streamlit chrome */
        header[data-testid="stHeader"],
        footer, #MainMenu,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {
          display: none !important;
        }

        /* Page base */
        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stApp {
          background: var(--dark-bg) !important;
          color: var(--eng-white) !important;
          font-family: 'Inter', sans-serif;
        }

        /* Scanline texture overlay */
        [data-testid="stAppViewContainer"]::before {
          content: '';
          position: fixed;
          top: 0; left: 0;
          width: 100%; height: 100%;
          background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 0, 0, 0.03) 2px,
            rgba(0, 0, 0, 0.03) 4px
          );
          pointer-events: none;
          z-index: 9999;
        }

        /* Ambient background glow */
        [data-testid="stMain"]::before {
          content: '';
          position: fixed;
          top: -30%;
          left: -10%;
          width: 60%;
          height: 60%;
          background: radial-gradient(
            ellipse at center,
            rgba(0, 59, 142, 0.08) 0%,
            transparent 70%
          );
          pointer-events: none;
          z-index: 0;
        }

        [data-testid="stMain"]::after {
          content: '';
          position: fixed;
          bottom: -20%;
          right: -10%;
          width: 50%;
          height: 50%;
          background: radial-gradient(
            ellipse at center,
            rgba(220, 36, 31, 0.06) 0%,
            transparent 70%
          );
          pointer-events: none;
          z-index: 0;
        }

        /* Block container */
        .block-container {
          padding-top: 0 !important;
          padding-bottom: 60px;
          max-width: 1600px;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
          background: #080C14 !important;
          border-right: 1px solid var(--dark-border);
        }
        [data-testid="stSidebar"] > div {
          padding-top: 0;
        }

        /* Typography */
        h1, h2, h3, .times {
          font-family: 'Times New Roman', serif !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--dark-bg); }
        ::-webkit-scrollbar-thumb {
          background: var(--dark-border);
          border-radius: 999px;
        }
        ::-webkit-scrollbar-thumb:hover { background: #2D3748; }

        /* ── Header ── */
        .tfl-header {
          background: linear-gradient(
            180deg,
            #0D1117 0%,
            rgba(13, 17, 23, 0) 100%
          );
          border-bottom: 1px solid var(--dark-border);
          padding: 24px 32px 20px;
          position: relative;
          margin-bottom: 8px;
        }

        .tfl-header::after {
          content: '';
          position: absolute;
          bottom: -1px;
          left: 0;
          width: 100%;
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent 0%,
            var(--tfl-red) 30%,
            var(--tfl-blue) 70%,
            transparent 100%
          );
        }

        .header-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 20px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .brand-text h1 {
          font-family: 'Times New Roman', serif !important;
          font-size: 32px;
          font-weight: 700;
          color: var(--eng-white);
          margin: 0 0 4px;
          letter-spacing: -0.5px;
        }

        .brand-text p {
          font-size: 11px;
          font-weight: 600;
          color: var(--dark-muted2);
          text-transform: uppercase;
          letter-spacing: 0.15em;
          margin: 0;
        }

        .live-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(220, 36, 31, 0.08);
          border: 1px solid rgba(220, 36, 31, 0.3);
          border-radius: 6px;
          padding: 10px 16px;
          backdrop-filter: blur(8px);
        }

        .live-dot {
          width: 8px;
          height: 8px;
          background: var(--tfl-red);
          border-radius: 50%;
          animation: pulseDot 1.6s ease-in-out infinite;
        }

        .live-label {
          font-size: 11px;
          font-weight: 800;
          color: var(--tfl-red);
          letter-spacing: 0.15em;
        }

        .live-time {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          color: var(--dark-muted2);
        }

        /* ── KPI Strip ── */
        .kpi-strip {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1px;
          background: var(--dark-border);
          border-radius: 8px;
          overflow: hidden;
          margin-top: 0;
        }

        .kpi-item {
          background: var(--dark-surface);
          padding: 16px 20px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          position: relative;
          transition: background 0.2s ease;
        }

        .kpi-item::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 2px;
          background: var(--kpi-color, var(--tfl-blue));
          opacity: 0.8;
        }

        .kpi-item:hover { background: var(--dark-surface2); }

        .kpi-value {
          font-family: 'Times New Roman', serif;
          font-size: 28px;
          font-weight: 700;
          color: var(--kpi-color, var(--eng-white));
          line-height: 1;
        }

        .kpi-label {
          font-size: 11px;
          font-weight: 600;
          color: var(--dark-muted2);
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }

        /* ── Section heading ── */
        .section-heading {
          display: flex;
          align-items: center;
          gap: 14px;
          margin: 32px 0 16px;
          padding-left: 2px;
        }

        .section-bar {
          width: 3px;
          height: 24px;
          background: var(--tfl-red);
          border-radius: 999px;
          animation: pulseBar 2s ease-in-out infinite;
          flex-shrink: 0;
        }

        .section-title {
          font-family: 'Times New Roman', serif !important;
          font-size: 20px;
          font-weight: 700;
          color: var(--eng-white);
          margin: 0;
          letter-spacing: -0.3px;
        }

        .section-count {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          color: var(--dark-muted);
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 4px;
          padding: 2px 8px;
          margin-left: auto;
        }

        /* ── Line cards ── */
        .cards-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 12px;
          margin-bottom: 8px;
        }

        .line-card {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 10px;
          padding: 18px 16px 16px;
          position: relative;
          overflow: hidden;
          cursor: default;
          animation: fadeInUp 0.5s ease both;
          animation-delay: var(--card-delay, 0s);
          transition: transform 0.2s ease, box-shadow 0.2s ease,
                      border-color 0.2s ease;
        }

        /* Accent bar at top of card */
        .line-card::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 3px;
          background: var(--line-accent);
        }

        /* Ambient glow behind card */
        .line-card::after {
          content: '';
          position: absolute;
          top: -40px; left: -40px;
          width: 120px; height: 120px;
          background: radial-gradient(
            ellipse,
            var(--line-glow) 0%,
            transparent 70%
          );
          pointer-events: none;
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .line-card:hover {
          transform: translateY(-3px);
          border-color: var(--line-accent);
          box-shadow: 0 0 0 1px var(--line-accent),
                      0 8px 32px rgba(0,0,0,0.4),
                      0 0 40px var(--line-glow);
        }

        .line-card:hover::after { opacity: 1; }

        .card-line-name {
          font-family: 'Times New Roman', serif;
          font-size: 15px;
          font-weight: 700;
          color: var(--eng-white);
          margin-bottom: 12px;
          line-height: 1.2;
        }

        .card-score {
          font-family: 'Times New Roman', serif;
          font-size: 52px;
          font-weight: 700;
          line-height: 0.9;
          margin-bottom: 12px;
          color: var(--score-colour);
          text-shadow: 0 0 20px var(--score-glow);
        }

        .card-badge {
          display: inline-flex;
          align-items: center;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          padding: 4px 10px;
          border-radius: 4px;
          background: var(--badge-bg);
          color: var(--badge-fg);
          border: 1px solid var(--badge-border);
          margin-bottom: 10px;
        }

        .card-meta {
          font-family: 'JetBrains Mono', monospace;
          font-size: 10px;
          color: var(--dark-muted);
          margin-top: 6px;
        }

        /* Card background line tint */
        .card-bg-tint {
          position: absolute;
          bottom: 0; right: 0;
          width: 80px; height: 80px;
          background: radial-gradient(
            ellipse at bottom right,
            var(--line-tint) 0%,
            transparent 70%
          );
          pointer-events: none;
        }

        /* ── Chart panels ── */
        .chart-panel {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 10px;
          padding: 20px;
          margin-bottom: 16px;
          transition: border-color 0.2s ease;
        }

        .chart-panel:hover {
          border-color: rgba(220, 36, 31, 0.3);
        }

        .chart-panel-title {
          font-family: 'Times New Roman', serif;
          font-size: 17px;
          font-weight: 700;
          color: var(--eng-white);
          margin: 0 0 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--dark-border);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        /* ── Station table ── */
        .stn-wrap {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-radius: 10px;
          overflow: hidden;
          height: 100%;
        }

        .stn-header {
          background: var(--tfl-blue);
          padding: 14px 16px;
          font-family: 'Times New Roman', serif;
          font-size: 17px;
          font-weight: 700;
          color: var(--eng-white);
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .stn-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }

        .stn-table th {
          background: rgba(0, 59, 142, 0.4);
          color: var(--dark-muted2);
          font-size: 10px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          padding: 10px 12px;
          text-align: left;
          border-bottom: 1px solid var(--dark-border);
        }

        .stn-table td {
          padding: 10px 12px;
          border-bottom: 1px solid rgba(28, 35, 51, 0.5);
          color: var(--eng-white);
          vertical-align: middle;
        }

        .stn-table tr:hover td {
          background: rgba(255, 255, 255, 0.02);
        }

        .stn-rank {
          font-family: 'Times New Roman', serif;
          font-size: 16px;
          font-weight: 700;
          color: var(--dark-muted2);
        }

        .stn-name {
          font-weight: 500;
          font-size: 12px;
        }

        .stn-count {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          color: var(--dark-muted2);
        }

        .grade-pill {
          display: inline-flex;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          padding: 3px 8px;
          border-radius: 4px;
        }

        /* ── Sidebar control panel ── */
        .ctrl-panel-title {
          font-family: 'Times New Roman', serif;
          font-size: 13px;
          font-weight: 700;
          color: var(--dark-muted2);
          text-transform: uppercase;
          letter-spacing: 0.15em;
          padding: 20px 16px 12px;
          border-bottom: 1px solid var(--dark-border);
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .ctrl-panel-title::before {
          content: '';
          width: 3px;
          height: 14px;
          background: var(--tfl-red);
          border-radius: 999px;
          flex-shrink: 0;
        }

        .line-row {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px 16px;
          border-bottom: 1px solid rgba(28,35,51,0.5);
          transition: background 0.15s ease;
        }

        .line-row:hover {
          background: rgba(255,255,255,0.02);
        }

        .line-indicator {
          width: 3px;
          height: 28px;
          border-radius: 999px;
          flex-shrink: 0;
        }

        .line-info {
          flex: 1;
          min-width: 0;
        }

        .line-info-name {
          font-size: 12px;
          font-weight: 600;
          color: var(--eng-white);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .line-info-status {
          font-size: 10px;
          color: var(--dark-muted);
          margin-top: 2px;
        }

        .line-score-badge {
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          color: var(--score-colour);
          background: rgba(0,0,0,0.3);
          border: 1px solid var(--dark-border);
          border-radius: 4px;
          padding: 2px 7px;
          flex-shrink: 0;
        }

        .refresh-panel {
          margin: 12px 16px;
          background: var(--dark-surface2);
          border: 1px solid var(--dark-border);
          border-radius: 8px;
          padding: 12px 14px;
        }

        .refresh-label {
          font-size: 10px;
          font-weight: 700;
          color: var(--dark-muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 6px;
        }

        .refresh-bar-wrap {
          background: var(--dark-border);
          border-radius: 999px;
          height: 3px;
          overflow: hidden;
          margin-bottom: 6px;
        }

        .refresh-bar {
          height: 3px;
          background: linear-gradient(
            90deg, var(--tfl-red), var(--tfl-blue)
          );
          border-radius: 999px;
          transition: width 1s linear;
        }

        .refresh-countdown {
          font-family: 'JetBrains Mono', monospace;
          font-size: 13px;
          font-weight: 600;
          color: var(--eng-white);
        }

        .empty-state,
        .error-state {
          background: var(--dark-surface);
          border: 1px solid var(--dark-border);
          border-left: 3px solid var(--tfl-red);
          border-radius: 10px;
          color: var(--eng-white);
          font-size: 13px;
          padding: 16px;
        }

        @media (max-width: 1100px) {
          .cards-grid { grid-template-columns: repeat(2, 1fr); }
          .kpi-strip { grid-template-columns: repeat(2, 1fr); }
          .header-top { align-items: flex-start; flex-direction: column; }
        }

        @media (max-width: 720px) {
          .cards-grid { grid-template-columns: 1fr; }
          .kpi-strip { grid-template-columns: 1fr; }
          .tfl-header { padding: 20px 16px; }
          .brand-text h1 { font-size: 26px; }
        }

        /* ── Animations ── */
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulseDot {
          0%   { box-shadow: 0 0 0 0 rgba(220,36,31,0.7); transform: scale(0.95); }
          70%  { box-shadow: 0 0 0 8px rgba(220,36,31,0); transform: scale(1); }
          100% { box-shadow: 0 0 0 0 rgba(220,36,31,0); transform: scale(0.95); }
        }

        @keyframes pulseBar {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }

        @keyframes shimmer {
          0%   { background-position: -200% 0; }
          100% { background-position:  200% 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )




def render_header(df_performance: pd.DataFrame, df_volume: pd.DataFrame):
    """Render immersive TfL header with KPI strip and live badge."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    total_lines = len(df_performance)
    lines_with_issues = len(df_performance[df_performance['service_status'] != 'Good']) if not df_performance.empty else 0
    total_arrivals = int(df_volume['row_count'].sum()) if not df_volume.empty else 0
    arrivals_str = f"{total_arrivals:,}"
    last_updated = datetime.now().strftime("%H:%M:%S")

    kpi_html = f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#1C2333;border-radius:8px;overflow:hidden;margin-top:20px;">
      <div style="background:#0D1117;padding:14px 18px;position:relative;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:#003B8E;"></div>
        <div style="font-family:'Times New Roman',serif;font-size:26px;font-weight:700;color:#003B8E;line-height:1;">{total_lines}</div>
        <div style="font-size:10px;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px;">Lines Monitored</div>
      </div>
      <div style="background:#0D1117;padding:14px 18px;position:relative;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:#FFD600;"></div>
        <div style="font-family:'Times New Roman',serif;font-size:26px;font-weight:700;color:#FFD600;line-height:1;">{lines_with_issues}</div>
        <div style="font-size:10px;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px;">Lines with Issues</div>
      </div>
      <div style="background:#0D1117;padding:14px 18px;position:relative;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:#DC241F;"></div>
        <div style="font-family:'Times New Roman',serif;font-size:26px;font-weight:700;color:#DC241F;line-height:1;">{arrivals_str}</div>
        <div style="font-size:10px;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px;">Arrivals Tracked</div>
      </div>
      <div style="background:#0D1117;padding:14px 18px;position:relative;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:#00C853;"></div>
        <div style="font-family:'Times New Roman',serif;font-size:26px;font-weight:700;color:#00C853;line-height:1;">{last_updated}</div>
        <div style="font-size:10px;font-weight:600;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px;">Last Updated</div>
      </div>
    </div>
    """

    header_html = f"""
    <div class="tfl-header">
      <div class="header-top">
        <div class="brand">
          <svg width="56" height="56" viewBox="0 0 56 56" role="img" aria-label="TfL">
            <circle cx="28" cy="28" r="26" fill="#003B8E" />
            <rect x="2" y="20" width="52" height="16" fill="#DC241F" />
            <text x="28" y="33" text-anchor="middle" fill="white"
                  font-family="Times New Roman" font-size="13"
                  font-weight="700">TfL</text>
          </svg>
          <div class="brand-text">
            <h1>TfL Intelligence Dashboard</h1>
            <p>Live London Underground Operations Centre</p>
          </div>
        </div>
        <div class="live-badge">
          <div class="live-dot"></div>
          <span class="live-label">LIVE</span>
          <span class="live-time">{timestamp}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.markdown(header_html, unsafe_allow_html=True)


def render_sidebar(df_performance: pd.DataFrame):
    """Render sidebar with line monitor and auto-refresh panel."""
    st.markdown(
        '<div class="ctrl-panel-title">Line Monitor</div>',
        unsafe_allow_html=True,
    )

    if df_performance.empty:
        st.markdown(
            '<div class="error-state">No line monitor data available.</div>',
            unsafe_allow_html=True,
        )
    else:
        for _, row in df_performance.sort_values("line_name").iterrows():
            line_colour = get_line_colour(row.get("line_id"))
            score_colour = get_health_color(str(row.get("service_status", "")))
            health_score = int(float(row.get("health_score") or 0))
            line_name = html.escape(str(row.get("line_name", "Unknown")))
            service_status = html.escape(str(row.get("service_status", "Unknown")))

            line_row_html = f"""
            <div class="line-row">
              <div class="line-indicator" style="background:{line_colour}"></div>
              <div class="line-info">
                <div class="line-info-name">{line_name}</div>
                <div class="line-info-status">{service_status}</div>
              </div>
              <div class="line-score-badge" style="--score-colour:{score_colour}">
                {health_score}
              </div>
            </div>
            """
            st.markdown(line_row_html, unsafe_allow_html=True)

    elapsed = (datetime.now() - st.session_state.last_refresh).total_seconds()
    refresh_interval = st.session_state.refresh_interval
    remaining = max(0, int(refresh_interval - elapsed))
    pct = min(100, max(0, (elapsed / refresh_interval) * 100))

    refresh_html = f"""
    <div class="refresh-panel">
      <div class="refresh-label">Auto Refresh</div>
      <div class="refresh-bar-wrap">
        <div class="refresh-bar" style="width:{pct:.1f}%"></div>
      </div>
      <div class="refresh-countdown">{remaining}s remaining</div>
    </div>
    <a href="https://github.com/sathiakhadija/TFL"
       target="_blank"
       style="display:block; padding:12px 16px;
              font-size:11px; font-weight:700;
              color:#4B5563; text-decoration:none;
              border-top:1px solid #1C2333;
              transition:color 0.2s ease;"
       onmouseover="this.style.color='#DC241F'"
       onmouseout="this.style.color='#4B5563'">
      ↗ GitHub Repository
    </a>
    """
    st.markdown(refresh_html, unsafe_allow_html=True)


def section_heading(title: str, count_str: str = ""):
    """Render section heading with animated bar and optional count badge."""
    count_html = ""
    if count_str:
        count_html = f'<span class="section-count">{html.escape(count_str)}</span>'

    heading_html = f"""
    <div class="section-heading">
      <div class="section-bar"></div>
      <h2 class="section-title">{html.escape(title)}</h2>
      {count_html}
    </div>
    """
    st.markdown(heading_html, unsafe_allow_html=True)


def render_line_health_cards(df: pd.DataFrame):
    if df.empty:
        st.info("No line performance data available.")
        return

    LINE_COLOURS = {
        "bakerloo": "#894E24",
        "central": "#DC241F",
        "circle": "#FFCE00",
        "district": "#007229",
        "elizabeth": "#6A1B9A",
        "hammersmith-city": "#F4A9BE",
        "jubilee": "#6A7278",
        "metropolitan": "#9B0058",
        "northern": "#1A1A1A",
        "piccadilly": "#000F9F",
        "victoria": "#00A0E2",
        "waterloo-city": "#00BDA8",
    }

    def score_colour(score):
        if score >= 80:
            return "#00C853"
        if score >= 50:
            return "#FFD600"
        if score >= 20:
            return "#FF3D00"
        return "#666666"

    def badge_style(status):
        s = status.lower()
        if "good" in s:
            return ("rgba(0,200,83,0.15)", "#00C853", "#00C853")
        if "minor" in s:
            return ("rgba(255,214,0,0.15)", "#FFD600", "#FFD600")
        if "severe" in s:
            return ("rgba(255,61,0,0.15)", "#FF3D00", "#FF3D00")
        return ("#1C2333", "#2D3748", "#6B7280")

    rows = df.sort_values("line_name").reset_index(drop=True)
    cols = st.columns(4)

    for i, row in rows.iterrows():
        line_id = str(row.get("line_id", "")).lower().strip()
        line_colour = LINE_COLOURS.get(line_id, "#4B5563")
        health = float(row.get("health_score") or 0)
        status = str(row.get("service_status", "Unknown"))
        sc = score_colour(health)
        bb, bc, bt = badge_style(status)
        rate = float(row.get("disruption_rate_pct") or 0)
        name = str(row.get("line_name", "Unknown"))
        delay_ms = min(i * 50, 550)

        card_html = f"""
<!DOCTYPE html><html><head><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;
  font-family:Inter,-apple-system,sans-serif;}}
.card{{
  background:linear-gradient(135deg,
    {line_colour}18 0%, #0D1117 65%);
  border:1px solid #1C2333;
  border-radius:10px;
  padding:18px 16px 14px;
  position:relative;
  overflow:hidden;
  animation:fadeUp 0.5s ease {delay_ms}ms both;
  transition:transform 0.2s,box-shadow 0.2s,
             border-color 0.2s;
  cursor:default;
  min-height:160px;
}}
.card:hover{{
  transform:translateY(-3px);
  border-color:{line_colour};
  box-shadow:0 0 0 1px {line_colour},
             0 8px 32px rgba(0,0,0,0.5),
             0 0 40px {line_colour}33;
}}
.top-bar{{
  position:absolute;top:0;left:0;right:0;
  height:3px;
  background:{line_colour};
  border-radius:10px 10px 0 0;
}}
.tint{{
  position:absolute;bottom:0;right:0;
  width:80px;height:80px;
  background:radial-gradient(
    ellipse at bottom right,
    {line_colour}22 0%,transparent 70%);
  pointer-events:none;
}}
.name{{
  font-family:'Georgia',serif;
  font-size:14px;font-weight:700;
  color:#FFFFFF;margin-bottom:10px;
  line-height:1.2;
}}
.score{{
  font-family:'Georgia',serif;
  font-size:50px;font-weight:700;
  line-height:0.9;margin-bottom:10px;
  color:{sc};
  text-shadow:0 0 24px {sc}66;
}}
.badge{{
  display:inline-flex;
  font-size:9px;font-weight:800;
  letter-spacing:0.12em;
  text-transform:uppercase;
  padding:4px 10px;border-radius:4px;
  background:{bb};
  border:1px solid {bc};
  color:{bt};
  margin-bottom:8px;
}}
.meta{{
  font-size:10px;color:#4B5563;
  font-family:'Courier New',monospace;
  margin-top:4px;
}}
@keyframes fadeUp{{
  from{{opacity:0;transform:translateY(14px);}}
  to{{opacity:1;transform:translateY(0);}}
}}
</style></head><body>
<div class="card">
  <div class="top-bar"></div>
  <div class="name">{html.escape(name)}</div>
  <div class="score">{health:.0f}</div>
  <div class="badge">{html.escape(status)}</div>
  <div class="meta">{rate:.1f}% disruption</div>
  <div class="tint"></div>
</div>
</body></html>"""

        with cols[i % 4]:
            components.html(card_html, height=175,
                           scrolling=False)


def render_disruption_chart(df: pd.DataFrame):
    """Render horizontal bar chart of disruption rates by line."""
    st.markdown(
        '<div class="chart-panel"><div class="chart-panel-title">📊 Disruption Rate by Line</div>',
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            '<div class="empty-state">No disruption data available.</div></div>',
            unsafe_allow_html=True,
        )
        return

    chart_df = df.sort_values("total_disruption_rate", ascending=True)
    marker_colours = [
        NAME_TO_COLOUR.get(str(name), DARK_MUTED)
        for name in chart_df["line_name"].tolist()
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=chart_df["total_disruption_rate"],
                y=chart_df["line_name"],
                orientation="h",
                marker_color=marker_colours,
                hovertemplate="%{y}<br>Disruption rate: %{x:.2f}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        paper_bgcolor=DARK_SURFACE,
        plot_bgcolor=DARK_BG,
        height=380,
        margin={"l": 10, "r": 10, "t": 10, "b": 40},
        showlegend=False,
        font={"family": "Inter", "color": ENG_WHITE},
        hoverlabel={
            "bgcolor": DARK_SURFACE2,
            "bordercolor": DARK_BORDER,
            "font_family": "Inter",
            "font_color": ENG_WHITE,
        },
    )

    fig.update_xaxes(
        gridcolor=DARK_BORDER,
        zerolinecolor=DARK_BORDER,
        tickfont={"color": DARK_MUTED, "size": 11},
        title_text="",
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0)",
        zerolinecolor="rgba(0,0,0,0)",
        tickfont={"color": "#9CA3AF", "size": 12},
        title_text="",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_station_table(df: pd.DataFrame):
    if df.empty:
        st.markdown(
            '<div style="background:#0D1117;border:1px solid '
            '#1C2333;border-radius:10px;padding:18px;color:#6B7280;"'
            '>No station data available.</div>',
            unsafe_allow_html=True,
        )
        return

    grade_styles = {
        "Excellent": "background:rgba(0,200,83,0.15);border:1px solid "
                     "#00C853;color:#00C853;",
        "Good":      "background:rgba(0,59,142,0.3);border:1px solid "
                     "#003B8E;color:#60A5FA;",
        "Fair":      "background:rgba(255,214,0,0.15);border:1px solid "
                     "#FFD600;color:#FFD600;",
        "Poor":      "background:rgba(255,61,0,0.15);border:1px solid "
                     "#FF3D00;color:#FF3D00;",
    }

    rows_html = ""
    for _, row in df.head(20).iterrows():
        grade = str(row.get("reliability_grade", "Unknown"))
        grade_style = grade_styles.get(
            grade, "background:#1C2333;border:1px solid "
                   "#2D3748;color:#6B7280;"
        )
        rank = int(row.get("disruption_rank") or 0)
        station = html.escape(
            str(row.get("station_name", "Unknown"))
        )
        total = float(row.get("total_disruptions") or 0)
        rows_html += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid
            rgba(28,35,51,0.5);font-family:'Georgia',serif;
            font-size:15px;font-weight:700;color:#4B5563;">
            {rank}
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid
            rgba(28,35,51,0.5);font-size:12px;font-weight:500;
            color:#FFFFFF;">
            {station}
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid
            rgba(28,35,51,0.5);font-family:'Courier New',monospace;
            font-size:12px;color:#6B7280;">
            {total:.0f}
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid
            rgba(28,35,51,0.5);">
            <span style="display:inline-flex;font-size:9px;
              font-weight:800;letter-spacing:0.1em;
              text-transform:uppercase;padding:3px 8px;
              border-radius:4px;{grade_style}">
              {html.escape(grade)}
            </span>
          </td>
        </tr>"""

    table_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      body {{
        background: #0D1117;
        font-family: Inter, -apple-system, sans-serif;
        overflow-x: hidden;
      }}
      .wrap {{
        background: #0D1117;
        border: 1px solid #1C2333;
        border-radius: 10px;
        overflow: hidden;
      }}
      .tbl-header {{
        background: #003B8E;
        padding: 14px 16px;
        font-family: 'Georgia', serif;
        font-size: 16px;
        font-weight: 700;
        color: #FFFFFF;
        border-bottom: 1px solid rgba(255,255,255,0.1);
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
      }}
      th {{
        background: rgba(0,59,142,0.3);
        color: #6B7280;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 10px 12px;
        text-align: left;
        border-bottom: 1px solid #1C2333;
      }}
      tr:hover td {{
        background: rgba(255,255,255,0.02) !important;
      }}
    </style>
    </head>
    <body>
      <div class="wrap">
        <div class="tbl-header">🚉 Station Reliability</div>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Station</th>
              <th>Disruptions</th>
              <th>Grade</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </body>
    </html>"""

    height = min(44 + 42 * min(len(df), 20) + 80, 560)
    components.html(table_html, height=height, scrolling=False)


def render_severity_heatmap(df_performance: pd.DataFrame):
    """Render heatmap of severity across lines and hours."""
    st.markdown(
        '<div class="chart-panel"><div class="chart-panel-title">🗺 Severity Heatmap — Lines × Hour</div>',
        unsafe_allow_html=True,
    )

    if df_performance.empty:
        st.markdown(
            '<div class="empty-state">No severity data available.</div></div>',
            unsafe_allow_html=True,
        )
        return

    heatmap_df = df_performance.copy()
    heatmap_df["ingested_hour"] = pd.to_datetime(heatmap_df["ingested_hour"], errors="coerce")
    heatmap_df["hour_of_day"] = heatmap_df["ingested_hour"].dt.hour

    pivot = heatmap_df.pivot_table(
        index="line_name",
        columns="hour_of_day",
        values="avg_severity",
        aggfunc="mean",
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[str(int(column)) for column in pivot.columns],
            y=pivot.index,
            colorscale=[[0, TFL_BLUE], [0.5, DARK_BORDER], [1, TFL_RED]],
            colorbar={
                "thickness": 8,
                "tickfont": {"color": DARK_MUTED},
            },
            hovertemplate="Line: %{y}<br>Hour: %{x}:00<br>Severity: %{z:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        paper_bgcolor=DARK_SURFACE,
        plot_bgcolor=DARK_BG,
        height=380,
        margin={"l": 10, "r": 60, "t": 10, "b": 40},
        font={"family": "Inter", "color": ENG_WHITE},
    )

    fig.update_xaxes(
        gridcolor=DARK_BORDER,
        tickfont={"color": DARK_MUTED},
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0)",
        tickfont={"color": "#9CA3AF"},
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_volume_chart(df: pd.DataFrame):
    """Render line chart of data ingestion volume by hour."""
    st.markdown(
        '<div class="chart-panel"><div class="chart-panel-title">📈 Data Ingestion — Rows per Hour</div>',
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            '<div class="empty-state">No ingestion volume data available.</div></div>',
            unsafe_allow_html=True,
        )
        return

    volume_df = df.copy()
    volume_df["hour"] = pd.to_datetime(volume_df["hour"], errors="coerce")

    fig = go.Figure(
        data=[
            go.Scatter(
                x=volume_df["hour"],
                y=volume_df["row_count"],
                mode="lines+markers",
                line={"color": TFL_RED, "width": 2},
                marker={"color": TFL_RED, "size": 6},
                fill="tozeroy",
                fillcolor="rgba(220,36,31,0.08)",
                hovertemplate="%{x}<br>Rows: %{y:,}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        paper_bgcolor=DARK_SURFACE,
        plot_bgcolor=DARK_BG,
        height=380,
        margin={"l": 10, "r": 10, "t": 10, "b": 40},
        showlegend=False,
        font={"family": "Inter", "color": ENG_WHITE},
    )

    fig.update_xaxes(
        gridcolor=DARK_BORDER,
        tickfont={"color": DARK_MUTED},
    )

    fig.update_yaxes(
        gridcolor=DARK_BORDER,
        tickfont={"color": DARK_MUTED},
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Main dashboard orchestrator with auto-refresh and data loading."""
    st.set_page_config(
        page_title="TfL Intelligence Dashboard",
        page_icon="🚇",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()
    dotenv.load_dotenv()

    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if "refresh_interval" not in st.session_state:
        st.session_state.refresh_interval = 60

    try:
        conn = get_db_connection()
    except ConnectionError as exc:
        error_html = f"""
        <div class="error-state">
          <strong>Database connection failed.</strong><br>
          {html.escape(str(exc))}
        </div>
        """
        st.markdown(error_html, unsafe_allow_html=True)
        st.stop()

    try:
        df_performance = load_line_performance(conn)
        df_trends = load_disruption_trends(conn)
        df_stations = load_station_reliability(conn)
        df_volume = load_raw_volume(conn)
    finally:
        conn.close()

    render_header(df_performance, df_volume)

    with st.sidebar:
        render_sidebar(df_performance)

    section_heading("Line Health", f"{len(df_performance)} lines")
    render_line_health_cards(df_performance)

    col1, col2 = st.columns([3, 2])
    with col1:
        section_heading("Disruption Analysis")
        render_disruption_chart(df_trends)
    with col2:
        section_heading("Station Reliability", f"{len(df_stations)} stations")
        render_station_table(df_stations)

    col1, col2 = st.columns(2)
    with col1:
        section_heading("Severity by Hour")
        render_severity_heatmap(df_performance)
    with col2:
        section_heading("Ingestion Volume")
        render_volume_chart(df_volume)

    elapsed = (datetime.now() - st.session_state.last_refresh).total_seconds()
    if elapsed > st.session_state.refresh_interval:
        st.session_state.last_refresh = datetime.now()
        st.rerun()


if __name__ == "__main__":
    main()
