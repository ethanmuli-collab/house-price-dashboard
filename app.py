"""דשבורד מכירות בתים - Ames Housing (dataset.csv)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="דשבורד מכירות בתים", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------- palette
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#898781", "#e1e0d9"

LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK, size=13),
    margin=dict(l=70, r=25, t=60, b=50),
    xaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED)),
    hoverlabel=dict(bgcolor="white", font_size=13),
    modebar=dict(orientation="v", bgcolor="rgba(0,0,0,0)"),  # לא מסתיר את כותרת הגרף
)


def style(fig, title, height=380):
    fig.update_layout(
        **LAYOUT,
        title=dict(text=title, font=dict(size=16), x=0, xanchor="left", y=0.97),
        height=height,
    )
    return fig


def headroom(fig, values, axis="y"):
    """מרווח בקצה הציר כדי שתוויות הערכים מחוץ לעמודה לא ייחתכו."""
    hi = max(values) * 1.18
    (fig.update_yaxes if axis == "y" else fig.update_xaxes)(range=[0, hi])
    return fig


# ---------------------------------------------------------------- data
@st.cache_data
def load_data(path="dataset.csv"):
    df = pd.read_csv(path, na_values=["NA"], keep_default_na=False)
    df["PricePerSF"] = df["SalePrice"] / df["GrLivArea"]
    df["TotalSF"] = df["GrLivArea"] + df["TotalBsmtSF"].fillna(0)
    df["HouseAge"] = df["YrSold"] - df["YearBuilt"]
    df["SaleDate"] = pd.to_datetime(dict(year=df["YrSold"], month=df["MoSold"], day=1))
    return df


df = load_data()

# ---------------------------------------------------------------- filters
st.sidebar.header("סינון")
neigh = st.sidebar.multiselect("שכונה (Neighborhood)", sorted(df["Neighborhood"].unique()))
btype = st.sidebar.multiselect("סוג מבנה (BldgType)", sorted(df["BldgType"].unique()))
years = sorted(df["YrSold"].unique())
yr = st.sidebar.select_slider("שנת מכירה", options=years, value=(years[0], years[-1]))
qual = st.sidebar.slider("איכות כללית (OverallQual)", 1, 10, (1, 10))
p_min, p_max = int(df["SalePrice"].min()), int(df["SalePrice"].max())
price = st.sidebar.slider("טווח מחיר ($)", p_min, p_max, (p_min, p_max), step=5000)

f = df[
    df["YrSold"].between(*yr)
    & df["OverallQual"].between(*qual)
    & df["SalePrice"].between(*price)
]
if neigh:
    f = f[f["Neighborhood"].isin(neigh)]
if btype:
    f = f[f["BldgType"].isin(btype)]

st.sidebar.caption(f"נבחרו {len(f):,} מתוך {len(df):,} עסקאות")

st.title("🏠 דשבורד מכירות בתים")
st.caption("Ames Housing · 1,460 עסקאות · 2006-2010")

if f.empty:
    st.warning("אין נתונים בסינון שנבחר. שנה את המסננים בצד.")
    st.stop()

# ---------------------------------------------------------------- KPIs
last_yr = f["YrSold"].max()
cur_med = f.loc[f["YrSold"] == last_yr, "SalePrice"].median()
prev_med = f.loc[f["YrSold"] == last_yr - 1, "SalePrice"].median()
yoy = (cur_med / prev_med - 1) * 100 if pd.notna(prev_med) and prev_med else None

r1 = st.columns(3)
r1[0].metric("עסקאות", f"{len(f):,}")
r1[1].metric("מחיר חציוני", f"${f['SalePrice'].median():,.0f}")
r1[2].metric("מחיר ממוצע", f"${f['SalePrice'].mean():,.0f}")

r2 = st.columns(3)
r2[0].metric("מחיר חציוני ל-sqft", f"${f['PricePerSF'].median():,.0f}")
r2[1].metric("שטח מגורים חציוני", f"{f['GrLivArea'].median():,.0f} sqft")
r2[2].metric(
    f"חציון {last_yr} מול {last_yr - 1}",
    f"${cur_med:,.0f}" if pd.notna(cur_med) else "—",
    delta=f"{yoy:+.1f}%" if yoy is not None else None,
)

st.divider()

tabs = st.tabs(["סקירה", "שכונות", "מאפייני הנכס", "מגמות בזמן", "טבלת נתונים"])

# ---------------------------------------------------------------- overview
with tabs[0]:
    c1, c2 = st.columns(2)

    fig = px.histogram(f, x="SalePrice", nbins=50, color_discrete_sequence=[SERIES[0]])
    fig.add_vline(
        x=f["SalePrice"].median(),
        line_dash="dash",
        line_color=SERIES[1],
        annotation_text=f"חציון ${f['SalePrice'].median():,.0f}",
    )
    fig.update_traces(marker_line_color=SURFACE, marker_line_width=1)
    fig.update_xaxes(title="מחיר מכירה ($)")
    fig.update_yaxes(title="מספר עסקאות")
    c1.plotly_chart(style(fig, "התפלגות מחירי המכירה"), width="stretch", theme=None)

    fig = px.scatter(
        f,
        x="GrLivArea",
        y="SalePrice",
        color="OverallQual",
        color_continuous_scale=SEQ_BLUE,
        hover_data=["Neighborhood", "YearBuilt"],
    )
    fig.update_traces(marker=dict(size=8, line=dict(width=1, color=SURFACE)))
    fig.update_xaxes(title="שטח מגורים (sqft)")
    fig.update_yaxes(title="מחיר מכירה ($)")
    c2.plotly_chart(
        style(fig, "מחיר מול שטח מגורים"), width="stretch", theme=None
    )

    # PricePerSF נגזר ממחיר המכירה עצמו - מוצא מהמתאם כדי לא לייצר מתאם מעגלי
    num = f.select_dtypes("number").drop(columns=["Id", "PricePerSF"], errors="ignore")
    corr = num.corr(numeric_only=True)["SalePrice"].drop("SalePrice").dropna()
    top = corr.reindex(corr.abs().sort_values(ascending=False).index).head(15).iloc[::-1]
    fig = go.Figure(
        go.Bar(
            x=top.values,
            y=top.index,
            orientation="h",
            marker_color=[SERIES[0] if v >= 0 else SERIES[7] for v in top.values],
            text=[f"{v:.2f}" for v in top.values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.update_xaxes(title="מתאם עם מחיר המכירה",
                     range=[min(top.min(), 0) * 1.3, max(top.max(), 0) * 1.15])
    st.plotly_chart(
        style(fig, "מתאם למחיר: 15 המשתנים החזקים", height=520),
        width="stretch", theme=None,
    )

# ---------------------------------------------------------------- neighborhoods
with tabs[1]:
    metric = st.radio(
        "מדד",
        ["מחיר חציוני", "מחיר למ״ר חציוני", "מספר עסקאות"],
        horizontal=True,
        key="nb_metric",
    )
    col = {"מחיר חציוני": "SalePrice", "מחיר למ״ר חציוני": "PricePerSF"}.get(metric)
    g = f.groupby("Neighborhood").agg(
        value=(col or "SalePrice", "median" if col else "size"), n=("SalePrice", "size")
    )
    if col is None:
        g["value"] = g["n"]
    g = g.sort_values("value")

    fig = go.Figure(
        go.Bar(
            x=g["value"],
            y=g.index,
            orientation="h",
            marker=dict(
                color=g["value"], colorscale=SEQ_BLUE, line=dict(color=SURFACE, width=1)
            ),
            customdata=g["n"],
            hovertemplate="%{y}<br>%{x:,.0f}<br>%{customdata} עסקאות<extra></extra>",
        )
    )
    fig.update_xaxes(title=metric)
    st.plotly_chart(
        style(fig, f"{metric} לפי שכונה", height=700), width="stretch", theme=None
    )

    c1, c2 = st.columns(2)
    order = f.groupby("Neighborhood")["SalePrice"].median().sort_values().index
    fig = px.box(f, x="Neighborhood", y="SalePrice", category_orders={"Neighborhood": list(order)})
    fig.update_traces(marker_color=SERIES[0], line_color=SERIES[0])
    fig.update_xaxes(title=None, tickangle=-45)
    fig.update_yaxes(title="מחיר מכירה ($)")
    c1.plotly_chart(style(fig, "פיזור מחירים בתוך כל שכונה", height=460), width="stretch", theme=None)

    g2 = f.groupby("Neighborhood").agg(
        med=("SalePrice", "median"), area=("GrLivArea", "median"), n=("Id", "size")
    ).reset_index()
    fig = px.scatter(g2, x="area", y="med", size="n", text="Neighborhood",
                     color_discrete_sequence=[SERIES[0]], size_max=40)
    fig.update_traces(textposition="top center", textfont=dict(size=10, color=MUTED),
                      marker=dict(line=dict(width=2, color=SURFACE)))
    fig.update_xaxes(title="שטח מגורים חציוני (sqft)")
    fig.update_yaxes(title="מחיר חציוני ($)")
    c2.plotly_chart(style(fig, "שכונות: שטח מול מחיר", height=460),
                    width="stretch", theme=None)

# ---------------------------------------------------------------- property
with tabs[2]:
    c1, c2 = st.columns(2)

    fig = px.box(f, x="OverallQual", y="SalePrice")
    fig.update_traces(marker_color=SERIES[0], line_color=SERIES[0])
    fig.update_xaxes(title="איכות כללית (1-10)", dtick=1)
    fig.update_yaxes(title="מחיר מכירה ($)")
    c1.plotly_chart(style(fig, "מחיר לפי איכות כללית"), width="stretch", theme=None)

    g = f.groupby("HouseStyle")["SalePrice"].median().sort_values()
    fig = go.Figure(go.Bar(x=g.values, y=g.index, orientation="h",
                           marker=dict(color=g.values, colorscale=SEQ_BLUE,
                                       line=dict(color=SURFACE, width=1)),
                           text=[f"${v:,.0f}" for v in g.values], textposition="outside"))
    fig.update_xaxes(title="מחיר חציוני ($)")
    headroom(fig, g.values, "x")
    c2.plotly_chart(style(fig, "מחיר חציוני לפי סגנון הבית"), width="stretch", theme=None)

    c3, c4 = st.columns(2)

    g = f.groupby("BldgType").agg(med=("SalePrice", "median"), n=("Id", "size")).reset_index()
    fig = go.Figure(go.Bar(x=g["BldgType"], y=g["med"], marker_color=SERIES[0],
                           customdata=g["n"],
                           hovertemplate="%{x}<br>$%{y:,.0f}<br>%{customdata} עסקאות<extra></extra>",
                           text=[f"${v:,.0f}" for v in g["med"]], textposition="outside"))
    fig.update_yaxes(title="מחיר חציוני ($)")
    headroom(fig, g["med"])
    c3.plotly_chart(style(fig, "מחיר חציוני לפי סוג מבנה"), width="stretch", theme=None)

    bins = [0, 1, 2, 3, 4, 5, 20]
    labels = ["0", "1", "2", "3", "4", "5+"]
    tmp = f.assign(Rooms=pd.cut(f["BedroomAbvGr"], bins=bins, labels=labels, right=False))
    g = tmp.groupby("Rooms", observed=True)["SalePrice"].median().dropna()
    fig = go.Figure(go.Bar(x=g.index.astype(str), y=g.values, marker_color=SERIES[0],
                           text=[f"${v:,.0f}" for v in g.values], textposition="outside"))
    fig.update_xaxes(title="חדרי שינה מעל הקרקע")
    fig.update_yaxes(title="מחיר חציוני ($)")
    headroom(fig, g.values)
    c4.plotly_chart(style(fig, "מחיר חציוני לפי מספר חדרי שינה"), width="stretch", theme=None)

    fig = px.density_heatmap(f, x="OverallQual", y="YearBuilt", z="SalePrice",
                             histfunc="avg", nbinsy=25, color_continuous_scale=SEQ_BLUE)
    fig.update_xaxes(title="איכות כללית", dtick=1)
    fig.update_yaxes(title="שנת בנייה")
    fig.update_coloraxes(colorbar_title="מחיר ממוצע")
    st.plotly_chart(style(fig, "מחיר ממוצע: איכות מול שנת בנייה", height=460),
                    width="stretch", theme=None)

# ---------------------------------------------------------------- time
with tabs[3]:
    ts = f.groupby("SaleDate").agg(med=("SalePrice", "median"), n=("Id", "size")).reset_index()
    fig = go.Figure(go.Scatter(x=ts["SaleDate"], y=ts["med"], mode="lines+markers",
                               line=dict(color=SERIES[0], width=2), marker=dict(size=8),
                               customdata=ts["n"],
                               hovertemplate="%{x|%m/%Y}<br>$%{y:,.0f}<br>%{customdata} עסקאות<extra></extra>"))
    fig.update_yaxes(title="מחיר חציוני ($)")
    fig.update_xaxes(title=None)
    st.plotly_chart(style(fig, "מחיר חציוני לאורך זמן (חודשי)"), width="stretch", theme=None)

    c1, c2 = st.columns(2)
    g = f.groupby("MoSold")["Id"].size()
    fig = go.Figure(go.Bar(x=g.index, y=g.values, marker_color=SERIES[0]))
    fig.update_xaxes(title="חודש מכירה", dtick=1)
    fig.update_yaxes(title="מספר עסקאות")
    c1.plotly_chart(style(fig, "עונתיות: עסקאות לפי חודש"), width="stretch", theme=None)

    g = f.groupby("YrSold").agg(med=("SalePrice", "median"), n=("Id", "size")).reset_index()
    fig = go.Figure(go.Bar(x=g["YrSold"], y=g["med"], marker_color=SERIES[0],
                           text=[f"${v:,.0f}" for v in g["med"]], textposition="outside"))
    fig.update_xaxes(title="שנת מכירה", dtick=1)
    fig.update_yaxes(title="מחיר חציוני ($)")
    headroom(fig, g["med"])
    c2.plotly_chart(style(fig, "מחיר חציוני לפי שנת מכירה"), width="stretch", theme=None)

    g = f.groupby("YearBuilt")["SalePrice"].median()
    fig = go.Figure(go.Scatter(x=g.index, y=g.values, mode="lines",
                               line=dict(color=SERIES[0], width=2)))
    fig.update_xaxes(title="שנת בנייה")
    fig.update_yaxes(title="מחיר חציוני ($)")
    st.plotly_chart(style(fig, "מחיר חציוני לפי שנת בנייה"), width="stretch", theme=None)

# ---------------------------------------------------------------- table + sorting
with tabs[4]:
    st.subheader("טבלת נתונים עם מיון")
    cols_default = ["Id", "Neighborhood", "BldgType", "HouseStyle", "OverallQual",
                    "YearBuilt", "GrLivArea", "TotalSF", "BedroomAbvGr", "FullBath",
                    "GarageCars", "PricePerSF", "YrSold", "SalePrice"]

    c1, c2, c3 = st.columns([2, 1, 1])
    sort_col = c1.selectbox("מיין לפי", cols_default, index=cols_default.index("SalePrice"))
    order = c2.radio("סדר", ["יורד", "עולה"], horizontal=True)
    top_n = c3.number_input("מספר שורות להצגה", 1, len(f), min(100, len(f)), step=10)

    shown = f[cols_default].sort_values(sort_col, ascending=(order == "עולה")).head(int(top_n))
    st.dataframe(
        shown.style.format({"SalePrice": "${:,.0f}", "PricePerSF": "${:,.0f}",
                            "GrLivArea": "{:,.0f}", "TotalSF": "{:,.0f}"}),
        width="stretch",
        hide_index=True,
    )
    st.caption("אפשר גם ללחוץ על כותרת עמודה בטבלה כדי למיין אותה ישירות.")

    st.download_button(
        "הורדת הנתונים המסוננים (CSV)",
        f.to_csv(index=False).encode("utf-8-sig"),
        file_name="filtered_houses.csv",
        mime="text/csv",
    )
