import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import io
import warnings
warnings.filterwarnings("ignore")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataLens – Analyseur CSV",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personnalisé ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 { font-family: 'DM Serif Display', serif; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f0f0f;
    border-right: 1px solid #222;
}
section[data-testid="stSidebar"] * { color: #e0ddd5 !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #f7f5f0;
    border: 1px solid #e0ddd5;
    border-radius: 12px;
    padding: 16px !important;
}

/* Upload zone */
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed #c8c4bb !important;
    border-radius: 16px !important;
    background: #faf9f6 !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
}

/* Download button */
.stDownloadButton > button {
    background: #0f0f0f !important;
    color: #fff !important;
    border-radius: 8px !important;
    border: none !important;
    font-weight: 500;
    padding: 10px 24px;
    transition: opacity .2s;
}
.stDownloadButton > button:hover { opacity: .85; }

/* Success / info boxes */
.stAlert { border-radius: 10px !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 DataLens")
    st.markdown("**Analyseur CSV automatique**")
    st.markdown("---")
    st.markdown("### Comment utiliser")
    st.markdown("""
1. **Importez** votre fichier CSV
2. **Explorez** les onglets d'analyse
3. **Téléchargez** le rapport PDF
    """)
    st.markdown("---")
    st.markdown("### Options")
    sep_choice = st.selectbox("Séparateur CSV", [",", ";", "\\t", "|"], index=0)
    encoding_choice = st.selectbox("Encodage", ["utf-8", "latin-1", "utf-8-sig"], index=0)
    st.markdown("---")
    st.markdown(
        "<small style='opacity:.5'>DataLens v1.0 · Fait avec Python & Streamlit</small>",
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
    st.markdown("""
    **Ce que DataLens analyse pour vous :**
    - 🔢 Statistiques descriptives complètes (moyenne, écart-type, percentiles…)
    - 🚨 Détection automatique des valeurs manquantes et doublons
    - 📈 Visualisations : distributions, corrélations, tendances
    - 📄 Rapport PDF professionnel téléchargeable en 1 clic
    """)
    st.stop()

# ── Chargement ────────────────────────────────────────────────────────────────
sep = "\t" if sep_choice == "\\t" else sep_choice
try:
    df = pd.read_csv(uploaded_file, sep=sep, encoding=encoding_choice)
except Exception as e:
    st.error(f"Erreur lors du chargement : {e}")
    st.stop()

if df.empty:
    st.error("Le fichier CSV est vide ou mal formaté.")
    st.stop()

# ── Métriques globales ────────────────────────────────────────────────────────
num_cols   = df.select_dtypes(include=np.number).columns.tolist()
cat_cols   = df.select_dtypes(include="object").columns.tolist()
missing    = df.isnull().sum().sum()
miss_pct   = round(missing / df.size * 100, 1)
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
tabs = st.tabs(["📋 Données", "📊 Statistiques", "📈 Visualisations", "🔗 Corrélations", "🚨 Qualité", "📄 Rapport PDF"])

# ────────────────────────── Onglet 1 : Données ───────────────────────────────
with tabs[0]:
    st.markdown("#### Aperçu des données")
    n_rows = st.slider("Nombre de lignes à afficher", 5, min(100, len(df)), 10)
    st.dataframe(df.head(n_rows), use_container_width=True)

    st.markdown("#### Types de colonnes")
    dtype_df = pd.DataFrame({
        "Colonne": df.columns,
        "Type":    df.dtypes.astype(str).values,
        "Non-nuls": df.count().values,
        "Nuls":    df.isnull().sum().values,
        "% Nuls":  (df.isnull().mean() * 100).round(1).astype(str).add("%").values,
    })
    st.dataframe(dtype_df, use_container_width=True, hide_index=True)

# ──────────────────────── Onglet 2 : Statistiques ────────────────────────────
with tabs[1]:
    if not num_cols:
        st.warning("Aucune colonne numérique détectée.")
    else:
        st.markdown("#### Statistiques descriptives — colonnes numériques")
        desc = df[num_cols].describe().T
        desc["skewness"] = df[num_cols].skew().round(3)
        desc["kurtosis"] = df[num_cols].kurtosis().round(3)
        st.dataframe(desc.style.format("{:.3f}", na_rep="—"), use_container_width=True)

    if cat_cols:
        st.markdown("#### Colonnes catégorielles")
        sel = st.selectbox("Colonne à explorer", cat_cols)
        vc = df[sel].value_counts().head(20)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(vc.reset_index().rename(columns={sel: "Valeur", "count": "Fréquence"}),
                         hide_index=True, use_container_width=True)
        with col2:
            fig, ax = plt.subplots(figsize=(6, 3))
            vc.plot(kind="barh", ax=ax, color="#2d2d2d", edgecolor="none")
            ax.set_xlabel("Fréquence", fontsize=9)
            ax.set_title(f"Top valeurs — {sel}", fontsize=10, fontweight="bold")
            ax.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close()

# ──────────────────────── Onglet 3 : Visualisations ──────────────────────────
with tabs[2]:
    if not num_cols:
        st.warning("Aucune colonne numérique pour les visualisations.")
    else:
        st.markdown("#### Distributions des variables numériques")
        n = len(num_cols)
        cols_per_row = 3
        rows = (n + cols_per_row - 1) // cols_per_row
        fig, axes = plt.subplots(rows, cols_per_row,
                                  figsize=(5 * cols_per_row, 3.5 * rows))
        axes = np.array(axes).flatten() if n > 1 else [axes]

        colors = ["#2d2d2d", "#6b6b6b", "#a8a8a8", "#d4d0c8", "#f0ece0"]
        for i, col in enumerate(num_cols):
            ax = axes[i]
            data = df[col].dropna()
            color = colors[i % len(colors)]
            ax.hist(data, bins=30, color=color, edgecolor="white", linewidth=0.4)
            ax.axvline(data.mean(),   color="#e74c3c", linestyle="--", linewidth=1, label=f"Moy: {data.mean():.2f}")
            ax.axvline(data.median(), color="#3498db", linestyle=":",  linewidth=1, label=f"Méd: {data.median():.2f}")
            ax.set_title(col, fontsize=9, fontweight="bold")
            ax.legend(fontsize=7)
            ax.tick_params(labelsize=7)

        for j in range(i + 1, len(axes)):
            axes[j].set_visible(False)

        plt.suptitle("Distributions", fontsize=12, fontweight="bold", y=1.01)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

        # Boxplots
        st.markdown("#### Boxplots (détection des outliers)")
        fig2, ax2 = plt.subplots(figsize=(max(8, n * 1.2), 4))
        df[num_cols].plot(kind="box", ax=ax2, patch_artist=True,
                          boxprops=dict(facecolor="#f0ece0", color="#2d2d2d"),
                          medianprops=dict(color="#e74c3c", linewidth=2),
                          whiskerprops=dict(color="#2d2d2d"),
                          capprops=dict(color="#2d2d2d"),
                          flierprops=dict(marker="o", color="#e74c3c", markersize=3, alpha=.5))
        ax2.set_xticklabels(num_cols, rotation=30, ha="right", fontsize=8)
        ax2.set_title("Boxplots — colonnes numériques", fontsize=10, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close()

# ──────────────────────── Onglet 4 : Corrélations ────────────────────────────
with tabs[3]:
    if len(num_cols) < 2:
        st.warning("Il faut au moins 2 colonnes numériques pour calculer les corrélations.")
    else:
        corr = df[num_cols].corr()
        st.markdown("#### Matrice de corrélation")
        fig, ax = plt.subplots(figsize=(max(6, len(num_cols) * 0.9),
                                        max(5, len(num_cols) * 0.8)))
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        plt.colorbar(im, ax=ax, shrink=0.8)
        ax.set_xticks(range(len(num_cols)))
        ax.set_yticks(range(len(num_cols)))
        ax.set_xticklabels(num_cols, rotation=40, ha="right", fontsize=8)
        ax.set_yticklabels(num_cols, fontsize=8)
        for i in range(len(num_cols)):
            for j in range(len(num_cols)):
                v = corr.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=7, color="white" if abs(v) > .5 else "#2d2d2d")
        ax.set_title("Corrélations de Pearson", fontsize=10, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

        # Top corrélations
        st.markdown("#### Paires les plus corrélées")
        pairs = (corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
                     .stack()
                     .reset_index()
                     .rename(columns={"level_0": "Var A", "level_1": "Var B", 0: "Corrélation"}))
        pairs["|r|"] = pairs["Corrélation"].abs()
        pairs = pairs.sort_values("|r|", ascending=False).drop(columns="|r|")
        st.dataframe(pairs.head(15).style.format({"Corrélation": "{:.4f}"}),
                     use_container_width=True, hide_index=True)

# ──────────────────────── Onglet 5 : Qualité ─────────────────────────────────
with tabs[4]:
    st.markdown("#### 🚨 Rapport de qualité des données")

    # Valeurs manquantes
    miss_series = df.isnull().sum()
    miss_series = miss_series[miss_series > 0]
    if miss_series.empty:
        st.success("✅ Aucune valeur manquante détectée !")
    else:
        st.error(f"⚠️ {len(miss_series)} colonne(s) avec des valeurs manquantes")
        miss_df = pd.DataFrame({
            "Colonne": miss_series.index,
            "Valeurs manquantes": miss_series.values,
            "% du total": (miss_series / len(df) * 100).round(1).values
        }).sort_values("Valeurs manquantes", ascending=False)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(miss_df, hide_index=True, use_container_width=True)
        with col2:
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.barh(miss_df["Colonne"], miss_df["% du total"],
                    color=["#e74c3c" if p > 30 else "#f39c12" if p > 10 else "#f1c40f"
                           for p in miss_df["% du total"]])
            ax.set_xlabel("% manquant", fontsize=9)
            ax.set_title("Valeurs manquantes par colonne", fontsize=10, fontweight="bold")
            ax.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close()

    # Doublons
    st.markdown("---")
    if duplicates == 0:
        st.success("✅ Aucun doublon détecté !")
    else:
        st.warning(f"⚠️ {duplicates} ligne(s) en doublon ({round(duplicates/len(df)*100,1)}%)")
        st.dataframe(df[df.duplicated(keep=False)].head(20),
                     use_container_width=True)

    # Outliers IQR
    if num_cols:
        st.markdown("---")
        st.markdown("#### Détection des outliers (méthode IQR)")
        outlier_info = []
        for col in num_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            mask = (df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)
            n_out = mask.sum()
            outlier_info.append({
                "Colonne": col,
                "Outliers": n_out,
                "% du total": round(n_out / len(df) * 100, 1),
                "Borne inf.": round(Q1 - 1.5 * IQR, 3),
                "Borne sup.": round(Q3 + 1.5 * IQR, 3),
            })
        out_df = pd.DataFrame(outlier_info).sort_values("Outliers", ascending=False)
        st.dataframe(out_df, use_container_width=True, hide_index=True)

# ──────────────────────── Onglet 6 : Rapport PDF ─────────────────────────────
with tabs[5]:
    st.markdown("#### 📄 Générer le rapport PDF")
    st.markdown("Un rapport complet et professionnel avec toutes vos analyses, prêt à partager ou à vendre.")

    if st.button("🚀 Générer le rapport PDF", use_container_width=True):
        with st.spinner("Génération du rapport en cours…"):

            buf = io.BytesIO()
            with PdfPages(buf) as pdf:

                # ─ Page 1 : Titre ─────────────────────────────────────────────
                fig = plt.figure(figsize=(11.69, 8.27))
                fig.patch.set_facecolor("#0f0f0f")
                ax = fig.add_subplot(111)
                ax.set_facecolor("#0f0f0f")
                ax.axis("off")
                ax.text(0.5, 0.70, "DataLens", ha="center", va="center",
                        fontsize=72, fontweight="bold", color="white",
                        transform=ax.transAxes)
                ax.text(0.5, 0.55, "Rapport d'Analyse CSV", ha="center", va="center",
                        fontsize=24, color="#a8a8a8", transform=ax.transAxes)
                ax.text(0.5, 0.42, f"Fichier : {uploaded_file.name}", ha="center",
                        va="center", fontsize=14, color="#6b6b6b", transform=ax.transAxes)
                ax.text(0.5, 0.32,
                        f"{df.shape[0]:,} lignes · {df.shape[1]} colonnes · "
                        f"{len(num_cols)} num. · {len(cat_cols)} catég.",
                        ha="center", va="center", fontsize=12,
                        color="#6b6b6b", transform=ax.transAxes)
                pdf.savefig(fig, bbox_inches="tight")
                plt.close()

                # ─ Page 2 : Vue d'ensemble ─────────────────────────────────────
                fig, axes = plt.subplots(1, 5, figsize=(11.69, 1.5))
                fig.suptitle("Vue d'ensemble", fontsize=14, fontweight="bold", y=1.02)
                for ax_i, (label, val) in zip(axes, [
                    ("Lignes",        f"{df.shape[0]:,}"),
                    ("Colonnes",      f"{df.shape[1]}"),
                    ("Numériques",    f"{len(num_cols)}"),
                    ("Manquantes",    f"{missing} ({miss_pct}%)"),
                    ("Doublons",      f"{duplicates}"),
                ]):
                    ax_i.set_facecolor("#f7f5f0")
                    ax_i.axis("off")
                    ax_i.text(0.5, 0.65, val, ha="center", va="center",
                              fontsize=18, fontweight="bold", color="#0f0f0f",
                              transform=ax_i.transAxes)
                    ax_i.text(0.5, 0.25, label, ha="center", va="center",
                              fontsize=9, color="#6b6b6b", transform=ax_i.transAxes)
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches="tight")
                plt.close()

                # ─ Page 3 : Statistiques ──────────────────────────────────────
                if num_cols:
                    desc2 = df[num_cols].describe().T.reset_index().rename(columns={"index": "Colonne"})
                    fig, ax = plt.subplots(figsize=(11.69, max(3, len(num_cols) * 0.55 + 1.5)))
                    ax.axis("off")
                    ax.set_title("Statistiques descriptives", fontsize=14, fontweight="bold", pad=12)
                    cols_show = ["Colonne", "count", "mean", "std", "min", "25%", "50%", "75%", "max"]
                    cols_show = [c for c in cols_show if c in desc2.columns]
                    table_data = [desc2.columns[desc2.columns.get_indexer(cols_show)].tolist()] + \
                                 desc2[cols_show].values.tolist()
                    tbl = ax.table(
                        cellText=[[f"{v:.3f}" if isinstance(v, float) else str(v) for v in row]
                                  for row in desc2[cols_show].values],
                        colLabels=cols_show,
                        loc="center", cellLoc="center"
                    )
                    tbl.auto_set_font_size(False)
                    tbl.set_fontsize(8)
                    tbl.scale(1, 1.4)
                    for (r, c), cell in tbl.get_celld().items():
                        if r == 0:
                            cell.set_facecolor("#0f0f0f")
                            cell.set_text_props(color="white", fontweight="bold")
                        else:
                            cell.set_facecolor("#f7f5f0" if r % 2 == 0 else "white")
                        cell.set_edgecolor("#e0ddd5")
                    plt.tight_layout()
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close()

                # ─ Page 4 : Distributions ─────────────────────────────────────
                if num_cols:
                    n = len(num_cols)
                    cols_per_row = 3
                    rows = (n + cols_per_row - 1) // cols_per_row
                    fig, axes = plt.subplots(rows, cols_per_row,
                                             figsize=(11.69, 3.2 * rows))
                    fig.suptitle("Distributions des variables numériques",
                                 fontsize=14, fontweight="bold")
                    axes_flat = np.array(axes).flatten() if n > 1 else [axes]
                    for i, col in enumerate(num_cols):
                        ax = axes_flat[i]
                        data = df[col].dropna()
                        ax.hist(data, bins=30, color="#2d2d2d", edgecolor="white", lw=0.3)
                        ax.axvline(data.mean(),   color="#e74c3c", ls="--", lw=1)
                        ax.axvline(data.median(), color="#3498db", ls=":",  lw=1)
                        ax.set_title(col, fontsize=8, fontweight="bold")
                        ax.tick_params(labelsize=6)
                    for j in range(i + 1, len(axes_flat)):
                        axes_flat[j].set_visible(False)
                    plt.tight_layout()
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close()

                # ─ Page 5 : Corrélations ──────────────────────────────────────
                if len(num_cols) >= 2:
                    corr2 = df[num_cols].corr()
                    fig, ax = plt.subplots(figsize=(11.69, 8.27))
                    fig.suptitle("Matrice de corrélation",
                                 fontsize=14, fontweight="bold")
                    im = ax.imshow(corr2.values, cmap="RdBu_r", vmin=-1, vmax=1)
                    plt.colorbar(im, ax=ax, shrink=.8)
                    ax.set_xticks(range(len(num_cols)))
                    ax.set_yticks(range(len(num_cols)))
                    ax.set_xticklabels(num_cols, rotation=40, ha="right", fontsize=7)
                    ax.set_yticklabels(num_cols, fontsize=7)
                    for i in range(len(num_cols)):
                        for j in range(len(num_cols)):
                            v = corr2.values[i, j]
                            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                                    fontsize=6, color="white" if abs(v) > .5 else "#2d2d2d")
                    plt.tight_layout()
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close()

                # ─ Page 6 : Qualité ───────────────────────────────────────────
                fig, axes = plt.subplots(1, 2, figsize=(11.69, 5))
                fig.suptitle("Qualité des données", fontsize=14, fontweight="bold")

                # Manquants
                ax1 = axes[0]
                if not miss_series.empty:
                    m_pct = (miss_series / len(df) * 100).sort_values(ascending=False)
                    colors_m = ["#e74c3c" if p > 30 else "#f39c12" if p > 10 else "#f1c40f"
                                for p in m_pct.values]
                    ax1.barh(m_pct.index, m_pct.values, color=colors_m)
                    ax1.set_xlabel("% manquant")
                    ax1.invert_yaxis()
                else:
                    ax1.text(0.5, 0.5, "✓ Aucune valeur manquante",
                             ha="center", va="center", fontsize=12, color="green",
                             transform=ax1.transAxes)
                ax1.set_title("Valeurs manquantes", fontsize=10, fontweight="bold")

                # Outliers
                ax2 = axes[1]
                if num_cols:
                    out_counts = []
                    for col in num_cols:
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        n_out = ((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum()
                        out_counts.append(n_out)
                    ax2.barh(num_cols, out_counts, color="#2d2d2d")
                    ax2.set_xlabel("Nombre d'outliers")
                    ax2.invert_yaxis()
                ax2.set_title("Outliers (IQR)", fontsize=10, fontweight="bold")
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches="tight")
                plt.close()

            buf.seek(0)

        st.success("✅ Rapport généré avec succès !")
        st.download_button(
            label="⬇️  Télécharger le rapport PDF",
            data=buf,
            file_name=f"rapport_{uploaded_file.name.replace('.csv', '')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
