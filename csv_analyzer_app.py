import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import warnings
warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataLens – Analyseur CSV",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'DM Serif Display', serif; }
section[data-testid="stSidebar"] { background: #0f0f0f; border-right: 1px solid #222; }
section[data-testid="stSidebar"] * { color: #e0ddd5 !important; }
[data-testid="metric-container"] {
    background: #f7f5f0; border: 1px solid #e0ddd5;
    border-radius: 12px; padding: 16px !important;
}
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed #c8c4bb !important;
    border-radius: 16px !important; background: #faf9f6 !important;
}
button[data-baseweb="tab"] { font-family: 'DM Sans', sans-serif; font-weight: 500; }
.stDownloadButton > button {
    background: #0f0f0f !important; color: #fff !important;
    border-radius: 8px !important; border: none !important;
    font-weight: 500; padding: 10px 24px; transition: opacity .2s;
}
.stDownloadButton > button:hover { opacity: .85; }
.stAlert { border-radius: 10px !important; }
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DataLens")
    st.markdown("**Analyseur CSV automatique**")
    st.markdown("<small style='opacity:.6'>v2.0 — Edition Pro</small>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Comment utiliser")
    st.markdown("""
1. **Importez** votre fichier CSV
2. **Nettoyez** vos données si besoin
3. **Filtrez** les colonnes à analyser
4. **Explorez** les onglets d'analyse
5. **Exportez** PDF ou Excel
    """)
    st.markdown("---")
    st.markdown("### Options d'import")
    sep_choice      = st.selectbox("Séparateur CSV", [",", ";", "\\t", "|"], index=0)
    encoding_choice = st.selectbox("Encodage", ["utf-8", "latin-1", "utf-8-sig"], index=0)
    st.markdown("---")
    st.markdown(
        "<small style='opacity:.5'>DataLens v2.0 · Python & Streamlit</small>",
        unsafe_allow_html=True
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# DataLens")
st.markdown("#### Transformez vos données brutes en insights en quelques secondes.")
st.markdown("---")

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📂 Glissez-déposez votre fichier CSV ici",
    type=["csv"],
    help="Fichiers CSV jusqu'à 200 Mo"
)

if uploaded_file is None:
    st.info("⬆️  Importez un fichier CSV pour commencer l'analyse.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Analyse automatique :**
        - 🔢 Statistiques descriptives complètes
        - 🚨 Détection valeurs manquantes & outliers
        - 📈 Graphiques Plotly interactifs
        - 🔗 Matrice de corrélation
        """)
    with col2:
        st.markdown("""
        **Nouveau dans v2.0 :**
        - 🧹 Nettoyage automatique des données
        - 🎯 Filtre de colonnes personnalisable
        - 📊 Graphiques Plotly interactifs & zoomables
        - 📥 Export Excel multi-onglets
        """)
    st.stop()

# ── Chargement ────────────────────────────────────────────────────────────────
sep = "\t" if sep_choice == "\\t" else sep_choice
try:
    df_raw = pd.read_csv(uploaded_file, sep=sep, encoding=encoding_choice)
except Exception as e:
    st.error(f"Erreur lors du chargement : {e}")
    st.stop()

if df_raw.empty:
    st.error("Le fichier CSV est vide ou mal formaté.")
    st.stop()

# ═══════════════════════════════════════════════
# ① NETTOYAGE AUTOMATIQUE
# ═══════════════════════════════════════════════
with st.expander("🧹 Nettoyage automatique des données", expanded=False):
    st.markdown("Corrigez vos données en 1 clic avant l'analyse.")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        remove_dup = st.checkbox("Supprimer les doublons",
                                  value=df_raw.duplicated().sum() > 0,
                                  help=f"{df_raw.duplicated().sum()} doublons détectés")
    with col_b:
        fill_method = st.selectbox("Remplir les NaN",
                                    ["Ne pas remplir", "Moyenne", "Médiane", "0", "Supprimer les lignes"])
    with col_c:
        strip_spaces = st.checkbox("Supprimer espaces inutiles", value=True)
    with col_d:
        fix_types = st.checkbox("Corriger les types auto.", value=True,
                                 help="Convertit colonnes numériques stockées en texte")

    apply_clean = st.button("✨ Appliquer le nettoyage", use_container_width=True, type="primary")
    if apply_clean:
        st.session_state["cleaned"] = True

df = df_raw.copy()
if st.session_state.get("cleaned", False):
    before_rows = df.shape[0]
    if remove_dup:
        df = df.drop_duplicates()
    if strip_spaces:
        obj_cols = df.select_dtypes(include="object").columns
        df[obj_cols] = df[obj_cols].apply(lambda c: c.str.strip())
    if fix_types:
        for col in df.select_dtypes(include="object").columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                pass
    if fill_method == "Moyenne":
        num = df.select_dtypes(include=np.number).columns
        df[num] = df[num].fillna(df[num].mean())
    elif fill_method == "Médiane":
        num = df.select_dtypes(include=np.number).columns
        df[num] = df[num].fillna(df[num].median())
    elif fill_method == "0":
        df = df.fillna(0)
    elif fill_method == "Supprimer les lignes":
        df = df.dropna()
    st.success(
        f"✅ Nettoyage appliqué — "
        f"{before_rows - df.shape[0]} lignes supprimées · "
        f"{df.isnull().sum().sum()} valeurs manquantes restantes"
    )

# ═══════════════════════════════════════════════
# ② FILTRE DE COLONNES
# ═══════════════════════════════════════════════
with st.expander("🎯 Sélectionner les colonnes à analyser", expanded=False):
    all_cols = df.columns.tolist()
    selected_cols = st.multiselect(
        "Colonnes sélectionnées",
        options=all_cols,
        default=all_cols,
        help="Laissez vide pour tout inclure"
    )
    if not selected_cols:
        selected_cols = all_cols
        st.info("Aucune sélection → toutes les colonnes incluses.")

df = df[selected_cols]

# ── Métriques globales ────────────────────────────────────────────────────────
num_cols   = df.select_dtypes(include=np.number).columns.tolist()
cat_cols   = df.select_dtypes(include="object").columns.tolist()
missing    = df.isnull().sum().sum()
miss_pct   = round(missing / df.size * 100, 1) if df.size > 0 else 0
duplicates = df.duplicated().sum()

st.markdown("### Vue d'ensemble")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Lignes",        f"{df.shape[0]:,}")
c2.metric("Colonnes",      f"{df.shape[1]}")
c3.metric("Numériques",    f"{len(num_cols)}")
c4.metric("Valeurs manq.", f"{missing} ({miss_pct}%)")
c5.metric("Doublons",      f"{duplicates}")
st.markdown("---")

# ── Onglets ───────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📋 Données", "📊 Statistiques", "📈 Visualisations",
    "🔗 Corrélations", "🚨 Qualité", "📄 Rapport PDF", "📥 Export Excel"
])

# ── Onglet 1 : Données ───────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("#### Aperçu des données")
    n_rows = st.slider("Nombre de lignes à afficher", 5, min(100, len(df)), 10)
    st.dataframe(df.head(n_rows), use_container_width=True)
    st.markdown("#### Types de colonnes")
    dtype_df = pd.DataFrame({
        "Colonne":  df.columns,
        "Type":     df.dtypes.astype(str).values,
        "Non-nuls": df.count().values,
        "Nuls":     df.isnull().sum().values,
        "% Nuls":   (df.isnull().mean() * 100).round(1).astype(str).add("%").values,
    })
    st.dataframe(dtype_df, use_container_width=True, hide_index=True)

# ── Onglet 2 : Statistiques ──────────────────────────────────────────────────
with tabs[1]:
    if not num_cols:
        st.warning("Aucune colonne numérique détectée.")
    else:
        st.markdown("#### Statistiques descriptives")
        desc = df[num_cols].describe().T
        desc["skewness"] = df[num_cols].skew().round(3)
        desc["kurtosis"] = df[num_cols].kurtosis().round(3)
        st.dataframe(desc.style.format("{:.3f}", na_rep="—"), use_container_width=True)

    if cat_cols:
        st.markdown("#### Colonnes catégorielles")
        sel = st.selectbox("Colonne à explorer", cat_cols)
        vc  = df[sel].value_counts().head(20)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(vc.reset_index().rename(columns={sel:"Valeur","count":"Fréquence"}),
                         hide_index=True, use_container_width=True)
        with col2:
            fig_cat = px.bar(x=vc.values, y=vc.index, orientation="h",
                              color=vc.values, color_continuous_scale="Blues",
                              title=f"Top valeurs — {sel}")
            fig_cat.update_layout(showlegend=False, coloraxis_showscale=False,
                                   plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig_cat.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_cat, use_container_width=True)

# ═══════════════════════════════════════════════
# ③ VISUALISATIONS PLOTLY INTERACTIVES
# ═══════════════════════════════════════════════
with tabs[2]:
    if not num_cols:
        st.warning("Aucune colonne numérique pour les visualisations.")
    else:
        st.markdown("#### Visualisation interactive")
        st.caption("Zoomez, survolez les barres, cliquez la légende pour interagir.")

        viz_col  = st.selectbox("Colonne à visualiser", num_cols)
        viz_type = st.radio("Type de graphique",
                             ["Histogramme", "Box plot", "Violin", "Scatter"],
                             horizontal=True)

        data_col = df[viz_col].dropna()
        fig_viz  = None

        if viz_type == "Histogramme":
            fig_viz = px.histogram(df, x=viz_col, nbins=40, marginal="box",
                                    color_discrete_sequence=["#2d2d2d"],
                                    title=f"Distribution — {viz_col}")
            fig_viz.add_vline(x=data_col.mean(), line_dash="dash", line_color="#e74c3c",
                               annotation_text=f"Moy: {data_col.mean():.2f}")
            fig_viz.add_vline(x=data_col.median(), line_dash="dot", line_color="#3498db",
                               annotation_text=f"Méd: {data_col.median():.2f}")

        elif viz_type == "Box plot":
            fig_viz = px.box(df, y=viz_col, points="outliers",
                              color_discrete_sequence=["#2d2d2d"],
                              title=f"Box plot — {viz_col}")

        elif viz_type == "Violin":
            fig_viz = px.violin(df, y=viz_col, box=True, points="outliers",
                                 color_discrete_sequence=["#534AB7"],
                                 title=f"Violin — {viz_col}")

        else:
            if len(num_cols) >= 2:
                col_y     = st.selectbox("Axe Y", [c for c in num_cols if c != viz_col])
                color_col = st.selectbox("Couleur (optionnel)", ["Aucune"] + cat_cols)
                fig_viz   = px.scatter(
                    df, x=viz_col, y=col_y, opacity=0.7,
                    color=None if color_col == "Aucune" else color_col,
                    trendline="ols", title=f"Scatter — {viz_col} vs {col_y}"
                )
            else:
                st.warning("Il faut au moins 2 colonnes numériques pour le scatter.")

        if fig_viz:
            fig_viz.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                   font=dict(family="DM Sans"))
            st.plotly_chart(fig_viz, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Toutes les distributions")
        n_c  = len(num_cols); cpr = min(3, n_c); rws = (n_c+cpr-1)//cpr
        fig_all = make_subplots(rows=rws, cols=cpr, subplot_titles=num_cols)
        clrs = px.colors.sequential.Greys_r
        for idx, col in enumerate(num_cols):
            r = idx//cpr+1; c = idx%cpr+1
            fig_all.add_trace(
                go.Histogram(x=df[col].dropna(), nbinsx=30, name=col,
                              marker_color=clrs[min(idx,len(clrs)-1)], showlegend=False),
                row=r, col=c
            )
        fig_all.update_layout(height=280*rws, title_text="Distributions — toutes variables numériques",
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                               font=dict(family="DM Sans"))
        st.plotly_chart(fig_all, use_container_width=True)

# ── Onglet 4 : Corrélations ──────────────────────────────────────────────────
with tabs[3]:
    if len(num_cols) < 2:
        st.warning("Il faut au moins 2 colonnes numériques pour les corrélations.")
    else:
        corr = df[num_cols].corr()
        fig_corr = px.imshow(corr, color_continuous_scale="RdBu_r",
                              zmin=-1, zmax=1, text_auto=".2f", aspect="auto",
                              title="Corrélations de Pearson")
        fig_corr.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                font=dict(family="DM Sans"))
        st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("#### Paires les plus corrélées")
        pairs = (corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                     .stack().reset_index()
                     .rename(columns={"level_0":"Var A","level_1":"Var B",0:"Corrélation"}))
        pairs["|r|"] = pairs["Corrélation"].abs()
        pairs = pairs.sort_values("|r|", ascending=False).drop(columns="|r|")
        st.dataframe(pairs.head(15).style.format({"Corrélation":"{:.4f}"}),
                     use_container_width=True, hide_index=True)

# ── Onglet 5 : Qualité ───────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("#### 🚨 Rapport de qualité des données")
    miss_series = df.isnull().sum()
    miss_series = miss_series[miss_series > 0]

    if miss_series.empty:
        st.success("✅ Aucune valeur manquante !")
    else:
        st.error(f"⚠️ {len(miss_series)} colonne(s) avec des valeurs manquantes")
        miss_df = pd.DataFrame({
            "Colonne": miss_series.index,
            "Valeurs manquantes": miss_series.values,
            "% du total": (miss_series/len(df)*100).round(1).values
        }).sort_values("Valeurs manquantes", ascending=False)
        col1, col2 = st.columns([1,2])
        with col1:
            st.dataframe(miss_df, hide_index=True, use_container_width=True)
        with col2:
            fig_miss = px.bar(miss_df, x="% du total", y="Colonne", orientation="h",
                               color="% du total", color_continuous_scale=["#f1c40f","#f39c12","#e74c3c"],
                               title="Valeurs manquantes par colonne")
            fig_miss.update_layout(coloraxis_showscale=False,
                                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig_miss.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_miss, use_container_width=True)

    st.markdown("---")
    if duplicates == 0:
        st.success("✅ Aucun doublon !")
    else:
        st.warning(f"⚠️ {duplicates} doublon(s) — {round(duplicates/len(df)*100,1)}%")

    if num_cols:
        st.markdown("---")
        st.markdown("#### Outliers (méthode IQR)")
        out_info = []
        for col in num_cols:
            Q1=df[col].quantile(.25); Q3=df[col].quantile(.75); IQR=Q3-Q1
            n_out=((df[col]<Q1-1.5*IQR)|(df[col]>Q3+1.5*IQR)).sum()
            out_info.append({"Colonne":col,"Outliers":n_out,
                              "% total":round(n_out/len(df)*100,1),
                              "Borne inf.":round(Q1-1.5*IQR,3),
                              "Borne sup.":round(Q3+1.5*IQR,3)})
        out_df = pd.DataFrame(out_info).sort_values("Outliers", ascending=False)
        st.dataframe(out_df, use_container_width=True, hide_index=True)

# ── Onglet 6 : Rapport PDF ───────────────────────────────────────────────────
with tabs[5]:
    st.markdown("#### 📄 Générer le rapport PDF")
    if st.button("🚀 Générer le rapport PDF", use_container_width=True):
        with st.spinner("Génération en cours…"):
            buf = io.BytesIO()
            with PdfPages(buf) as pdf:

                # Titre
                fig = plt.figure(figsize=(11.69,8.27)); fig.patch.set_facecolor("#0f0f0f")
                ax  = fig.add_subplot(111); ax.axis("off"); ax.set_facecolor("#0f0f0f")
                ax.text(0.5,0.68,"DataLens",ha="center",fontsize=72,fontweight="bold",
                        color="white",transform=ax.transAxes)
                ax.text(0.5,0.53,"Rapport d'Analyse CSV — v2.0",ha="center",
                        fontsize=22,color="#a8a8a8",transform=ax.transAxes)
                ax.text(0.5,0.40,f"Fichier : {uploaded_file.name}",ha="center",
                        fontsize=14,color="#6b6b6b",transform=ax.transAxes)
                ax.text(0.5,0.30,
                        f"{df.shape[0]:,} lignes · {df.shape[1]} colonnes · "
                        f"{len(num_cols)} num. · {len(cat_cols)} catég.",
                        ha="center",fontsize=12,color="#6b6b6b",transform=ax.transAxes)
                pdf.savefig(fig,bbox_inches="tight"); plt.close()

                # Métriques
                fig,axes=plt.subplots(1,5,figsize=(11.69,1.5))
                fig.suptitle("Vue d'ensemble",fontsize=14,fontweight="bold",y=1.02)
                for ax_i,(label,val) in zip(axes,[
                    ("Lignes",f"{df.shape[0]:,}"),("Colonnes",f"{df.shape[1]}"),
                    ("Numériques",f"{len(num_cols)}"),
                    ("Manquantes",f"{missing} ({miss_pct}%)"),("Doublons",f"{duplicates}")
                ]):
                    ax_i.set_facecolor("#f7f5f0"); ax_i.axis("off")
                    ax_i.text(0.5,0.65,val,ha="center",fontsize=18,fontweight="bold",
                              color="#0f0f0f",transform=ax_i.transAxes)
                    ax_i.text(0.5,0.25,label,ha="center",fontsize=9,
                              color="#6b6b6b",transform=ax_i.transAxes)
                plt.tight_layout(); pdf.savefig(fig,bbox_inches="tight"); plt.close()

                # Stats
                if num_cols:
                    d2=df[num_cols].describe().T.reset_index().rename(columns={"index":"Colonne"})
                    cs=["Colonne","count","mean","std","min","25%","50%","75%","max"]
                    cs=[c for c in cs if c in d2.columns]
                    fig,ax=plt.subplots(figsize=(11.69,max(3,len(num_cols)*.55+1.5)))
                    ax.axis("off"); ax.set_title("Statistiques descriptives",fontsize=14,fontweight="bold",pad=12)
                    tbl=ax.table(cellText=[[f"{v:.3f}" if isinstance(v,float) else str(v) for v in r]
                                            for r in d2[cs].values],
                                  colLabels=cs,loc="center",cellLoc="center")
                    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1,1.4)
                    for (r,c),cell in tbl.get_celld().items():
                        if r==0: cell.set_facecolor("#0f0f0f"); cell.set_text_props(color="white",fontweight="bold")
                        else: cell.set_facecolor("#f7f5f0" if r%2==0 else "white")
                        cell.set_edgecolor("#e0ddd5")
                    plt.tight_layout(); pdf.savefig(fig,bbox_inches="tight"); plt.close()

                # Distributions
                if num_cols:
                    n=len(num_cols); cpr=3; rws=(n+cpr-1)//cpr
                    fig,axes=plt.subplots(rws,cpr,figsize=(11.69,3.2*rws))
                    fig.suptitle("Distributions",fontsize=14,fontweight="bold")
                    af=np.array(axes).flatten() if n>1 else [axes]
                    for i,col in enumerate(num_cols):
                        ax=af[i]; d=df[col].dropna()
                        ax.hist(d,bins=30,color="#2d2d2d",edgecolor="white",lw=0.3)
                        ax.axvline(d.mean(),color="#e74c3c",ls="--",lw=1)
                        ax.axvline(d.median(),color="#3498db",ls=":",lw=1)
                        ax.set_title(col,fontsize=8,fontweight="bold"); ax.tick_params(labelsize=6)
                    for j in range(i+1,len(af)): af[j].set_visible(False)
                    plt.tight_layout(); pdf.savefig(fig,bbox_inches="tight"); plt.close()

                # Corrélations
                if len(num_cols)>=2:
                    corr2=df[num_cols].corr()
                    fig,ax=plt.subplots(figsize=(11.69,8.27))
                    im=ax.imshow(corr2.values,cmap="RdBu_r",vmin=-1,vmax=1)
                    plt.colorbar(im,ax=ax,shrink=.8)
                    ax.set_xticks(range(len(num_cols))); ax.set_yticks(range(len(num_cols)))
                    ax.set_xticklabels(num_cols,rotation=40,ha="right",fontsize=7)
                    ax.set_yticklabels(num_cols,fontsize=7)
                    for i in range(len(num_cols)):
                        for j in range(len(num_cols)):
                            v=corr2.values[i,j]
                            ax.text(j,i,f"{v:.2f}",ha="center",va="center",
                                    fontsize=6,color="white" if abs(v)>.5 else "#2d2d2d")
                    ax.set_title("Matrice de corrélation",fontsize=14,fontweight="bold")
                    plt.tight_layout(); pdf.savefig(fig,bbox_inches="tight"); plt.close()

            buf.seek(0)
        st.success("✅ Rapport PDF généré !")
        st.download_button(
            label="⬇️  Télécharger le rapport PDF",
            data=buf,
            file_name=f"rapport_{uploaded_file.name.replace('.csv','')}_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ═══════════════════════════════════════════════
# ④ EXPORT EXCEL
# ═══════════════════════════════════════════════
with tabs[6]:
    st.markdown("#### 📥 Export Excel multi-onglets")
    st.markdown("Téléchargez toutes vos analyses dans un seul fichier Excel.")

    export_options = st.multiselect(
        "Contenu à exporter",
        ["Données nettoyées", "Statistiques descriptives",
         "Corrélations", "Valeurs manquantes", "Rapport outliers"],
        default=["Données nettoyées", "Statistiques descriptives", "Corrélations"]
    )

    if st.button("📥 Générer le fichier Excel", use_container_width=True, type="primary"):
        with st.spinner("Génération du fichier Excel…"):
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:

                if "Données nettoyées" in export_options:
                    df.to_excel(writer, sheet_name="Données", index=False)

                if "Statistiques descriptives" in export_options and num_cols:
                    desc_e = df[num_cols].describe().T
                    desc_e["skewness"] = df[num_cols].skew().round(3)
                    desc_e["kurtosis"] = df[num_cols].kurtosis().round(3)
                    desc_e.to_excel(writer, sheet_name="Statistiques")

                if "Corrélations" in export_options and len(num_cols) >= 2:
                    df[num_cols].corr().round(4).to_excel(writer, sheet_name="Corrélations")

                if "Valeurs manquantes" in export_options:
                    pd.DataFrame({
                        "Colonne": df.columns,
                        "Valeurs manquantes": df.isnull().sum().values,
                        "% manquant": (df.isnull().mean()*100).round(2).values
                    }).to_excel(writer, sheet_name="Manquants", index=False)

                if "Rapport outliers" in export_options and num_cols:
                    out_e = []
                    for col in num_cols:
                        Q1=df[col].quantile(.25); Q3=df[col].quantile(.75); IQR=Q3-Q1
                        n_o=((df[col]<Q1-1.5*IQR)|(df[col]>Q3+1.5*IQR)).sum()
                        out_e.append({"Colonne":col,"Outliers":n_o,
                                      "% total":round(n_o/len(df)*100,1),
                                      "Borne inf.":round(Q1-1.5*IQR,3),
                                      "Borne sup.":round(Q3+1.5*IQR,3)})
                    pd.DataFrame(out_e).to_excel(writer, sheet_name="Outliers", index=False)

            excel_buf.seek(0)

        st.success(f"✅ Excel généré — {len(export_options)} onglet(s) !")
        st.download_button(
            label="⬇️  Télécharger le fichier Excel",
            data=excel_buf,
            file_name=f"analyse_{uploaded_file.name.replace('.csv','')}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
