from __future__ import annotations

import plotly.graph_objects as go


POINT_STYLES = {
    "FBC": {"color": "#F59E0B", "symbol": "diamond", "size": 11},
    "APC": {"color": "#2563EB", "symbol": "circle", "size": 12},
    "BBC": {"color": "#8B5CF6", "symbol": "diamond", "size": 11},
    "CPC": {"color": "#DC2626", "symbol": "circle", "size": 12},
}


def inject_css(st):
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 88% 4%, rgba(37,99,235,.08), transparent 24rem),
                #F6F8FC;
        }

        [data-testid="stSidebar"] {
            background: #101828;
        }

        [data-testid="stSidebar"] * {
            color: #F8FAFC;
        }

        .cv-brand {
            padding: 0.4rem 0 1.2rem 0;
        }

        .cv-brand-title {
            font-weight: 780;
            font-size: 1.25rem;
            letter-spacing: -0.02em;
        }

        .cv-brand-subtitle {
            color: #98A2B3;
            font-size: .78rem;
            margin-top: .25rem;
        }

        .hero {
            background: linear-gradient(135deg, #172033 0%, #263550 100%);
            border-radius: 18px;
            padding: 1.55rem 1.7rem;
            color: white;
            margin-bottom: 1.2rem;
            box-shadow: 0 12px 35px rgba(16,24,40,.10);
        }

        .hero h1 {
            font-size: 1.65rem;
            line-height: 1.2;
            margin: 0 0 .45rem 0;
            letter-spacing: -0.025em;
        }

        .hero p {
            color: #D0D5DD;
            margin: 0;
            max-width: 900px;
            line-height: 1.55;
            font-size: .92rem;
        }

        .small-note {
            font-size: .80rem;
            color: #667085;
            line-height: 1.45;
        }

        .section-title {
            color: #172033;
            font-size: 1.05rem;
            font-weight: 730;
            letter-spacing: -0.01em;
            margin: .25rem 0 .25rem 0;
        }

        .section-copy {
            color: #667085;
            font-size: .85rem;
            margin-bottom: .8rem;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #EAECF0;
            border-radius: 14px;
            padding: .85rem 1rem;
            box-shadow: 0 4px 18px rgba(16,24,40,.035);
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 650;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def make_cv_figure(df, points, title: str):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["potential"],
            y=df["current"],
            mode="lines",
            name="CV trace",
            line=dict(color="#344054", width=2.1),
            hovertemplate=(
                "Potential: %{x:.6f} V<br>"
                "Current: %{y:.8e} A<extra></extra>"
            ),
        )
    )

    for label in ["FBC", "APC", "BBC", "CPC"]:
        point = points[label]
        style = POINT_STYLES[label]

        fig.add_trace(
            go.Scatter(
                x=[point.potential],
                y=[point.current],
                mode="markers+text",
                name=label,
                text=[label],
                textposition="top center",
                marker=dict(
                    color=style["color"],
                    symbol=style["symbol"],
                    size=style["size"],
                    line=dict(color="white", width=1.5),
                ),
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "Potential: %{x:.6f} V<br>"
                    "Current: %{y:.8e} A<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left"),
        xaxis_title="Working electrode potential (V)",
        yaxis_title="Current (A)",
        template="plotly_white",
        height=550,
        margin=dict(l=55, r=25, t=70, b=55),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="closest",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#EEF2F6",
        zeroline=True,
        zerolinecolor="#D0D5DD",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#EEF2F6",
        zeroline=True,
        zerolinecolor="#D0D5DD",
    )
    return fig
