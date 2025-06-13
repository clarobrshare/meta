import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# -------- CACHE DOS DADOS --------
@st.cache_data
def load_data():
    url_4g = "export_calculated_4g.xlsx"
    url_5g = "export_calculated_5g.xlsx"

    df_4g = pd.read_excel(url_4g)
    df_4g['Tecnologia'] = '4G'

    df_5g = pd.read_excel(url_5g)
    df_5g['Tecnologia'] = '5G'

    return pd.concat([df_4g, df_5g], ignore_index=True)

df = load_data()
color_map = {1: 'green', 2: 'orange', 3: 'red', 'No Readiness': 'black'}

# ===================================================================
# 1. MAPA INTERATIVO COM FILTROS PRÓPRIOS
# ===================================================================
st.header("📍 Mapa de Ranks")

col1, col2 = st.columns(2)
with col1:
    mapa_tecnologia = st.selectbox("Tecnologia (Mapa):", sorted(df['Tecnologia'].dropna().unique()), key="map_tec")
with col2:
    mapa_rank = st.selectbox("Ranking:", ['Claro Rank', 'Vivo Rank', 'TIM Rank'], key="map_rank")

mapa_valores = st.multiselect("Valores de Rank:", [1, 2, 3, 'No Readiness'], default=[1, 2, 3, 'No Readiness'], key="map_vals")

df_mapa = df[df['Tecnologia'] == mapa_tecnologia]

def create_map(data, rank_col, valores):
    mapa = folium.Map(location=[data['Latitude'].mean(), data['Longitude'].mean()], zoom_start=4)
    for _, row in data.iterrows():
        rank = row[rank_col]
        if rank in valores:
            color = color_map.get(rank, 'gray')
            radius = {1: 3, 2: 2, 3: 4, 'No Readiness': 1}.get(rank, 2)
            folium.CircleMarker(
                location=(row['Latitude'], row['Longitude']),
                radius=radius,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"{row['Region']} - {rank_col}: {rank}"
            ).add_to(mapa)
    return mapa

st_folium(create_map(df_mapa, mapa_rank, mapa_valores), width=1000, height=500)

# ===================================================================
# 2. TABELA ESTILIZADA COM FILTRO PRÓPRIO
# ===================================================================
st.header("📋 Ranking % Readiness - Capitais")

tabela_tecnologia = st.selectbox("Tecnologia (Tabela):", sorted(df['Tecnologia'].dropna().unique()), key="tab_tec")

df_tab = df[(df['Tecnologia'] == tabela_tecnologia) & (df['Capital'] == 1)].copy()
df_tab = df_tab[['Region', 'Regional', 'Claro Rank', 'Vivo Rank', 'TIM Rank',
                 'Claro Readiness (%)', 'Vivo Readiness (%)', 'TIM Readiness (%)']]
df_tab['Region'] = df_tab['Region'].str.split('- ').str[1]
df_tab = df_tab.sort_values(by='Regional')

def color_ranks(val):
    if val == 3:
        return 'background-color: red'
    elif val == 1:
        return 'background-color: green'
    elif val == 'No Readiness':
        return 'background-color: black'
    return ''

st.dataframe(
    df_tab.style
    .applymap(color_ranks, subset=['Claro Rank', 'Vivo Rank', 'TIM Rank'])
    .format({'Claro Readiness (%)': '{:.1f}', 'Vivo Readiness (%)': '{:.1f}', 'TIM Readiness (%)': '{:.1f}'})
)

# ===================================================================
# 3. GRÁFICO ABSOLUTO COM FILTRO PRÓPRIO
# ===================================================================
st.header("📊 Quantidade de Ranks por Regional")

grafico_tecnologia = st.selectbox("Tecnologia (Gráfico Absoluto):", sorted(df['Tecnologia'].dropna().unique()), key="graf_tec")
df_graf = df[df['Tecnologia'] == grafico_tecnologia]

def plot_absolute_ranks(data):
    count_claro = data.groupby(['Regional', 'Claro Rank']).size().unstack(fill_value=0).reindex(columns=color_map.keys(), fill_value=0)
    count_vivo  = data.groupby(['Regional', 'Vivo Rank']).size().unstack(fill_value=0).reindex(columns=color_map.keys(), fill_value=0)
    count_tim   = data.groupby(['Regional', 'TIM Rank']).size().unstack(fill_value=0).reindex(columns=color_map.keys(), fill_value=0)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, count_data, title in zip(
        axes, [count_claro, count_vivo, count_tim], ['Claro', 'Vivo', 'TIM']
    ):
        valid_cols = [c for c in color_map if c in count_data.columns]
        count_data[valid_cols].plot(kind='bar', stacked=True, ax=ax,
                                    color=[color_map[c] for c in valid_cols])
        ax.set_title(f"{title} Rank por Regional")
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticklabels(count_data.index, rotation=45)
    
    # Adiciona uma única legenda acima dos subplots
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Rank", bbox_to_anchor=(0.5, 1.15), loc='upper center', ncol=3, fontsize='small')
    
    plt.tight_layout(rect=[0, 0, 0.85, 1.2])
    st.pyplot(fig)

plot_absolute_ranks(df_graf)

# ===================================================================
# 4. GRÁFICO PERCENTUAL COM FILTRO PRÓPRIO
# ===================================================================
st.header("📈 Porcentagem de Ranks por Regional")

percent_tecnologia = st.selectbox("Tecnologia (Gráfico Percentual):", sorted(df['Tecnologia'].dropna().unique()), key="pct_tec")
df_pct = df[df['Tecnologia'] == percent_tecnologia]

def plot_percentage_ranks(data):
    def to_pct(df_op):
        return df_op.div(df_op.sum(axis=1), axis=0) * 100

    count_claro = data.groupby(['Regional', 'Claro Rank']).size().unstack(fill_value=0).reindex(columns=color_map, fill_value=0)
    count_vivo  = data.groupby(['Regional', 'Vivo Rank']).size().unstack(fill_value=0).reindex(columns=color_map, fill_value=0)
    count_tim   = data.groupby(['Regional', 'TIM Rank']).size().unstack(fill_value=0).reindex(columns=color_map, fill_value=0)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, pct_data, title in zip(
        axes, [to_pct(count_claro), to_pct(count_vivo), to_pct(count_tim)], ['Claro', 'Vivo', 'TIM']
    ):
        valid_cols = [c for c in color_map if c in pct_data.columns]
        pct_data[valid_cols].plot(kind='bar', stacked=True, ax=ax,
                                  color=[color_map[c] for c in valid_cols])
        ax.set_title(f"{title} Rank (%) por Regional")
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticklabels(pct_data.index, rotation=45)

    # Adiciona uma única legenda acima dos subplots
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Rank", bbox_to_anchor=(0.5, 1.15), loc='upper center', ncol=3, fontsize='small')
    
    plt.tight_layout(rect=[0, 0, 0.85, 1.2])
    st.pyplot(fig)

plot_percentage_ranks(df_pct)
